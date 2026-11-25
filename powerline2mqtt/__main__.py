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
from .discovery import adapter_configs, bridge_configs
from datetime import datetime, timezone
from . import __version__

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('powerline2mqtt')
stop = threading.Event()
connected = threading.Event()
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda *_: stop.set())
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
        connected.set()
def on_disconnect(c, u, flags, reason, props):
    connected.clear()
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
        pub(topic, json.dumps(cfg))
    pub(f'{root}/state', json.dumps(row), retain=False)
    pub(f'{root}/availability', 'online')

def main():
    known = set()
    failures = 0
    last_success = None
    store = Path('/data/known.json')
    try:
        known = set(json.loads(store.read_text()))
        known = {k for k in known if re.fullmatch(r'[0-9a-f]{12}', k)}
    except FileNotFoundError: pass
    client.connect_async(os.getenv('MQTT_HOST','127.0.0.1'), int(os.getenv('MQTT_PORT','1883')), 30)
    client.loop_start()
    try:
        while not stop.is_set():
            if not connected.wait(5):
                log.warning('Waiting for MQTT connection')
                continue
            try:
                result = subprocess.run(['plcstat','-i',iface,'-t'], capture_output=True, text=True, timeout=20, check=True)
                rows = parse_topology(result.stdout)
                current = {mac.replace(':','').lower() for mac in rows}
                for key in known-current:
                    pub(f'{base}/{key}/availability','offline')
                known |= current
                store.parent.mkdir(parents=True, exist_ok=True)
                tmp = store.with_suffix('.tmp')
                tmp.write_text(json.dumps(sorted(known)))
                tmp.replace(store)
                for row in rows.values(): discover(row)
                last_success = datetime.now(timezone.utc).isoformat()
                for topic, cfg in bridge_configs(node, prefix, interval):
                    pub(topic, json.dumps(cfg))
                pub(f'{base}/bridge/state', json.dumps(dict(count=len(rows), failures=failures, last_success=last_success, interface=iface, version=__version__)), retain=False)
                pub(avail,'online')
                log.info('Detected %d adapters', len(rows))
            except Exception as exc:
                failures += 1
                log.warning('Poll failed: %s', exc)
                if connected.is_set():
                    try: pub(avail,'offline')
                    except Exception: log.warning('Could not publish availability')
            stop.wait(min(5, interval) if last_success is None else interval)
    finally:
        if connected.is_set():
            try: pub(avail,'offline')
            except Exception: pass
        client.disconnect()
        client.loop_stop()

if __name__ == '__main__': main()
