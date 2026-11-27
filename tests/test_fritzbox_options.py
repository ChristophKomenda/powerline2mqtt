import unittest

from haos.run import environment


class FritzBoxOptionsTests(unittest.TestCase):

    def test_fritzbox_options(self):
        options = {
            "mqtt_host": "broker",
            "powerline_backend": "fritzbox",
            "fritzbox_url": "http://192.0.2.1:49000",
            "fritzbox_username": "test-user",
            "fritzbox_password": "test-password",
            "fritzbox_reference_mac": "02:00:00:00:00:01",
        }

        result = environment(options)

        for key, value in options.items():
            self.assertEqual(result[key.upper()], value)

    def test_homeplug_default_compatibility(self):
        result = environment({"mqtt_host": "broker"})
        self.assertEqual(result, {"MQTT_HOST": "broker"})

    def test_explicit_homeplug_backend(self):
        result = environment({
            "mqtt_host": "broker",
            "powerline_backend": "homeplug",
        })

        self.assertEqual(
            result["POWERLINE_BACKEND"],
            "homeplug",
        )


if __name__ == "__main__":
    unittest.main()
