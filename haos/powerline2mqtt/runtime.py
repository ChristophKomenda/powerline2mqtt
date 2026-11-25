"""Small, independently testable runtime helpers."""
import json
import re

class DiscoveryCache:
    def __init__(self):
        self.sent = {}

    def clear(self):
        self.sent.clear()

    def publish(self, topic, config, publish):
        payload = json.dumps(config, sort_keys=True)
        if self.sent.get(topic) != payload:
            publish(topic, payload)
            self.sent[topic] = payload

class Presence:
    def __init__(self, known=(), threshold=2):
        self.known = set(known)
        self.misses = {}
        self.threshold = threshold

    def observe(self, current):
        self.known.update(current)
        for key in self.known:
            self.misses[key] = 0 if key in current else self.misses.get(key, 0) + 1
        return {key for key in self.known if self.misses[key] >= self.threshold}

def load_known(path):
    values = json.loads(path.read_text())
    if not isinstance(values, list):
        raise ValueError('Expected a list of adapter IDs')
    return {v for v in values if isinstance(v, str) and re.fullmatch(r'[0-9a-f]{12}', v)}
