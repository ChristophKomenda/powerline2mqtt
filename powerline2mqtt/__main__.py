import json
import logging
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path
import paho.mqtt.client as mqtt
from .parser import parse_topology
from .runtime import DiscoveryCache, Presence, load_known, PollSchedule, PollHealth
from .discovery import adapter_configs, bridge_configs
from datetime import datetime, timezone
from . import __version__

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('powerline2mqtt')
stop = threading.Event()
connected = threading.Event()
refresh = threading.Event()
wake = threading.Event()
cache = DiscoveryCache()
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda *_: (stop.set(), wake.set()))
node = os.getenv('NODE_ID', 'pi5')
if not re.fullmatch(r'[A-Za-z0-9_-]+', node):
    raise ValueError('Invalid NODE_ID')
iface = os.getenv('PLC_INTERFACE', 'eth0')
interval = max(10, int(os.getenv('POLL_INTERVAL', '60')))
base = f'powerline2mqtt/{node}'
avail = f'{base}/availability'
prefix = os.getenv('DISCOVERY_PREFIX', 'homeassistant')
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'powerline2mqtt-{node}')
user = os.getenv('MQTT_USERNAME')
if user:
    client.username_pw_set(user, os.getenv('MQTT_PASSWORD', ''))
if os.getenv('MQTT_TLS', 'false').lower() == 'true':
    client.tls_set(ca_certs=os.getenv('MQTT_CA_FILE') or None)
client.will_set(avail, 'offline', qos=1, retain=True)
def on_connect(c, u, flags, reason, props):
    if reason.is_failure:
        log.error('MQTT rejected connection: %s', reason)
    else:
        c.subscribe(f'{prefix}/status', qos=1)
        refresh.set()
        connected.set()
        wake.set()
def on_disconnect(c, u, flags, reason, props):
    connected.clear()
def on_message(c, u, message):
    if message.topic == f'{prefix}/status' and message.payload == b'online':
        refresh.set()
        wake.set()
client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect

def pub(topic, value, retain=True):
    if not connected.is_set():
        raise RuntimeError('MQTT disconnected')
    info = client.publish(topic, value, qos=1, retain=retain)
    info.wait_for_publish(timeout=5)
    if not info.is_published():
        raise RuntimeError('MQTT publish not acknowledged')

def discover(row):
    mac = row['mac']
    key = mac.replace(':','').lower()
    ident = f'powerline2mqtt_{node}_{key}'
    root = f'{base}/{key}'
    for topic, cfg in adapter_configs(row, node, prefix, interval):
        cache.publish(topic, cfg, pub)
    pub(f'{root}/state', json.dumps(row), retain=False)
    pub(f'{root}/availability', 'online')

def main():
    known = set()
    health = PollHealth()
    schedule = PollSchedule(interval)
    last_count = 0
    online = False
    last_success = None
    store = Path('/data/known.json')
    try:
        known = load_known(store)
    except FileNotFoundError: pass
    except (ValueError, OSError) as exc:
        log.warning("Ignoring unreadable adapter cache: %s", exc)
    saved_known = set(known)
    presence = Presence(known)
    client.connect_async(os.getenv('MQTT_HOST','127.0.0.1'), int(os.getenv('MQTT_PORT','1883')), 30)
    client.loop_start()
    def publish_bridge():
        for topic, cfg in bridge_configs(node, prefix, interval):
            cache.publish(topic, cfg, pub)
        state = dict(count=last_count, last_success=last_success,
                     interface=iface, version=__version__, poll_interval=interval,
                     retry_interval=schedule.retry, **health.metrics())
        pub(f'{base}/bridge/state', json.dumps(state), retain=False)

    try:
        while not stop.is_set():
            wake.clear()
            if not connected.wait(5):
                continue
            remaining = schedule.remaining(time.monotonic())
            if remaining:
                # Birth/reconnect can request a refresh but never an early scan.
                wake.wait(remaining)
                continue
            if stop.is_set():
                break
            try:
                result = subprocess.run(['plcstat','-i',iface,'-t'], capture_output=True, text=True, timeout=20, check=True)
                rows = parse_topology(result.stdout)
            except Exception as exc:
                health.record(False)
                schedule.completed(time.monotonic(), False)
                log.warning('Poll failed: %s', exc)
                try:
                    if online and health.tolerate_failure() and not refresh.is_set():
                        # Only diagnostics are refreshed; do not refresh old adapter readings.
                        publish_bridge()
                    else:
                        online = False
                        pub(avail, 'offline')
                except Exception as mqtt_exc:
                    online = False
                    refresh.set()
                    log.warning('MQTT update failed: %s', mqtt_exc)
                continue
            health.record(True)
            last_count = len(rows)
            last_success = datetime.now(timezone.utc).isoformat()
            current = {mac.replace(':','').lower() for mac in rows}
            offline = presence.observe(current)
            try:
                if refresh.is_set():
                    refresh.clear()
                    cache.clear()
                for key in offline:
                    pub(f'{base}/{key}/availability','offline')
                known = presence.known
                if known != saved_known:
                    store.parent.mkdir(parents=True, exist_ok=True)
                    tmp = store.with_suffix('.tmp')
                    tmp.write_text(json.dumps(sorted(known)))
                    tmp.replace(store)
                    saved_known = set(known)
                for row in rows.values():
                    discover(row)
                publish_bridge()
                pub(avail,'online')
                online = True
                log.info('Detected %d adapters', len(rows))
                schedule.completed(time.monotonic(), True)
            except Exception as exc:
                online = False
                refresh.set()
                log.warning('MQTT or persistence update failed: %s', exc)
                try:
                    pub(avail,'offline')
                except Exception:
                    log.warning('Could not publish availability')
                schedule.completed(time.monotonic(), False)
    finally:
        if connected.is_set():
            try: pub(avail,'offline')
            except Exception: pass
        client.disconnect()
        client.loop_stop()

if __name__ == '__main__': main()
