import unittest
from powerline2mqtt.discovery import adapter_configs, bridge_configs
from powerline2mqtt.parser import parse_topology
from test_parser import SAMPLE
class DiscoveryTests(unittest.TestCase):
    def test_stable_identifiers(self):
        row=parse_topology(SAMPLE)['34:E8:94:00:00:01']
        configs=dict(adapter_configs(row,'pi5','homeassistant',60))
        ident='powerline2mqtt_pi5_34e894000001'
        self.assertEqual(configs[f'homeassistant/sensor/{ident}/role/config']['unique_id'],ident+'_role')
        self.assertEqual(len(configs),7)
    def test_remote_rates(self):
        row=parse_topology(SAMPLE)['80:CA:4B:00:00:03']
        cfgs=[c for _,c in adapter_configs(row,'pi5','homeassistant',60)]
        tx=next(c for c in cfgs if c['name']=='TX link rate')
        self.assertEqual(tx['state_class'],'measurement')
        self.assertEqual(row['tx'],0)
        self.assertEqual(len(cfgs),7)
    def test_bridge(self):
        self.assertEqual(len(dict(bridge_configs('pi5','homeassistant',60))),10)
    def test_connectivity(self):
        row=next(iter(parse_topology(SAMPLE).values()))
        cfg=next(c for _,c in adapter_configs(row,'pi5','homeassistant',60) if c['name']=='Connectivity')
        self.assertEqual(cfg['payload_off'],'offline')
        self.assertEqual(cfg['availability_topic'],'powerline2mqtt/pi5/availability')
