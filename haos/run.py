"""Translate Supervisor options without exposing credentials in logs."""
import json
import os
from pathlib import Path

def environment(options):
    keys = ('node_id', 'plc_interface', 'poll_interval', 'mqtt_host', 'mqtt_port', 'mqtt_username', 'mqtt_password', 'mqtt_tls', 'discovery_prefix')
    if not options.get('mqtt_host'):
        raise ValueError('Configure mqtt_host with the reachable broker address')
    return {key.upper(): str(options[key]).lower() if isinstance(options[key], bool) else str(options[key]) for key in keys if key in options and options[key] is not None}

if __name__ == '__main__':
    os.environ.update(environment(json.loads(Path('/data/options.json').read_text())))
    os.execvp('python3', ['python3', '-m', 'powerline2mqtt'])
