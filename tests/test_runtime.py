import unittest
import tempfile
from pathlib import Path
from powerline2mqtt.runtime import DiscoveryCache, Presence, load_known

class RuntimeTests(unittest.TestCase):
    def test_discovery_cache(self):
        cache = DiscoveryCache()
        calls = []
        send = lambda *args: calls.append(args)
        cache.publish('topic', {'a': 1}, send)
        cache.publish('topic', {'a': 1}, send)
        self.assertEqual(len(calls), 1)
        cache.publish('topic', {'a': 2}, send)
        cache.clear()
        cache.publish('topic', {'a': 2}, send)
        self.assertEqual(len(calls), 3)

    def test_failed_publish_not_cached(self):
        cache = DiscoveryCache()
        def fail(*args):
            raise RuntimeError('offline')
        with self.assertRaises(RuntimeError):
            cache.publish('topic', {}, fail)
        self.assertEqual(cache.sent, {})

    def test_presence(self):
        p = Presence({'a', 'b'})
        self.assertEqual(p.observe({'a'}), set())
        self.assertEqual(p.observe({'a'}), {'b'})
        self.assertEqual(p.observe({'a', 'b'}), set())

    def test_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'known.json'
            path.write_text('{bad')
            with self.assertRaises(ValueError):
                load_known(path)
            path.write_text('["abcdef123456", 2, "bad"]')
            self.assertEqual(load_known(path), {'abcdef123456'})
