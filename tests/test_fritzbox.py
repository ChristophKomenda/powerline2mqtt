import unittest

from powerline2mqtt.fritzbox import parse_mesh, mbps
from powerline2mqtt.discovery import adapter_configs

A = "80:CA:4B:00:00:01"
B = "80:CA:4B:00:00:02"
C = "34:E8:94:00:00:03"


def fixture():
    devices = [
        {"NewMACAddress": mac, "NewActive": "1"}
        for mac in (A, B, C)
    ]

    link = {
        "uid": "link-1",
        "type": "PLC",
        "state": "CONNECTED",
        "node_1_uid": "a",
        "node_2_uid": "b",
        "cur_data_rate_tx": 275000,
        "cur_data_rate_rx": 313000,
    }

    nodes = [
        {
            "uid": uid,
            "device_mac_address": mac,
            "device_firmware_version": "test-fw",
            "node_interfaces": [{
                "type": "PLC",
                "node_links": links,
            }],
        }
        for uid, mac, links in (
            ("a", A, [link]),
            ("b", B, [link]),
            ("c", C, []),
        )
    ]

    return devices, {"nodes": nodes}


class FritzBoxTests(unittest.TestCase):

    def test_adapter_detection(self):
        devices, mesh = fixture()
        self.assertEqual(len(parse_mesh(devices, mesh, A)), 3)

    def test_reference(self):
        devices, mesh = fixture()
        rows = parse_mesh(devices, mesh, A)
        self.assertEqual(rows[A]["locality"], "LOC")
        self.assertEqual(rows[B]["locality"], "REM")

    def test_forward_rates(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, A)[B]
        self.assertEqual(row["tx"], 275)
        self.assertEqual(row["rx"], 313)

    def test_reverse_rates(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, B)[A]
        self.assertEqual(row["tx"], 313)
        self.assertEqual(row["rx"], 275)

    def test_missing_reference(self):
        devices, mesh = fixture()
        with self.assertRaises(ValueError):
            parse_mesh(devices, mesh, "00:00:00:00:00:00")

    def test_invalid_mac(self):
        devices, mesh = fixture()
        with self.assertRaises(ValueError):
            parse_mesh(devices, mesh, "invalid")

    def test_unknown_fields(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, A)[B]
        self.assertIsNone(row["tei"])
        self.assertIsNone(row["role"])
        self.assertIsNone(row["chipset"])

    def test_missing_link(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, A)[C]
        self.assertIsNone(row["tx"])
        self.assertIsNone(row["rx"])

    def test_firmware(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, A)[B]
        self.assertEqual(row["firmware"], "test-fw")

    def test_incomplete_mesh(self):
        devices, mesh = fixture()
        mesh["nodes"].pop()
        with self.assertRaises(ValueError):
            parse_mesh(devices, mesh, A)

    def test_rate_conversion(self):
        self.assertEqual(mbps(328000), 328)
        self.assertEqual(mbps(0), 0)
        self.assertIsNone(mbps(None))
        self.assertIsNone(mbps(-1))
        self.assertIsNone(mbps(True))

    def test_inactive_adapter(self):
        devices, mesh = fixture()
        devices[2]["NewActive"] = "0"
        self.assertNotIn(C, parse_mesh(devices, mesh, A))

    def test_stable_mqtt_identifiers(self):
        devices, mesh = fixture()
        row = parse_mesh(devices, mesh, A)[B]

        configs = dict(
            adapter_configs(row, "pi5", "homeassistant", 60)
        )

        ident = "powerline2mqtt_pi5_80ca4b000002"
        topic = f"homeassistant/sensor/{ident}/tx/config"

        self.assertEqual(
            configs[topic]["unique_id"], ident + "_tx"
        )

    def test_disconnected_link(self):
        devices, mesh = fixture()
        mesh["nodes"][0]["node_interfaces"][0][
            "node_links"
        ][0]["state"] = "DISCONNECTED"

        row = parse_mesh(devices, mesh, A)[B]
        self.assertIsNone(row["tx"])
        self.assertIsNone(row["rx"])


if __name__ == "__main__":
    unittest.main()
