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


class PollSchedule:
    """Monotonic, completion-based cadence; events cannot advance the deadline."""
    def __init__(self, interval, retry=5):
        self.interval = max(10, interval)
        self.retry = max(5, retry)
        self.deadline = 0

    def remaining(self, now):
        return max(0, self.deadline - now)

    def completed(self, now, success):
        self.deadline = now + (self.interval if success else self.retry)


class PollHealth:
    def __init__(self):
        self.successes = 0
        self.failures = 0
        self.consecutive = 0

    def record(self, success):
        if success:
            self.successes += 1
            self.consecutive = 0
        else:
            self.failures += 1
            self.consecutive += 1

    def tolerate_failure(self):
        return self.successes > 0 and self.consecutive == 1

    def metrics(self):
        total = self.successes + self.failures
        return dict(successes=self.successes, failures=self.failures,
                    consecutive_failures=self.consecutive,
                    success_rate=round(100 * self.successes / total, 2) if total else None)
