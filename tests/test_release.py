import unittest
from powerline2mqtt.discovery import adapter_configs, bridge_configs
from powerline2mqtt.parser import parse_topology
from test_parser import SAMPLE
from haos.run import environment

class ReleaseTests(unittest.TestCase):
    def test_origin(self):
        row = next(iter(parse_topology(SAMPLE).values()))
        for _, config in list(adapter_configs(row, 'test', 'homeassistant', 60)) + list(bridge_configs('test', 'homeassistant', 60)):
            self.assertEqual(config['origin']['name'], 'Powerline2MQTT')
    def test_options(self):
        self.assertEqual(environment({'mqtt_host':'broker','mqtt_tls':True,'mqtt_port':1883}), {'MQTT_HOST':'broker','MQTT_TLS':'true','MQTT_PORT':'1883'})
    def test_missing_host(self):
        with self.assertRaises(ValueError):
            environment({'mqtt_host':''})
