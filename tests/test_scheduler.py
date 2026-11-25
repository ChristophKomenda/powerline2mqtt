import unittest
from powerline2mqtt.runtime import PollSchedule, PollHealth

class SchedulerTests(unittest.TestCase):
    def test_events_do_not_advance_deadline(self):
        s = PollSchedule(60)
        s.completed(100, True)
        for t in (100, 100.061, 100.186, 159):
            self.assertGreater(s.remaining(t), 0)
        self.assertEqual(s.remaining(160), 0)

    def test_retry_after_failure(self):
        s = PollSchedule(60)
        s.completed(100, False)
        self.assertEqual(s.remaining(100), 5)
        self.assertEqual(s.remaining(105), 0)
        s.completed(106, True)
        self.assertEqual(s.remaining(106), 60)

    def test_minimum_interval(self):
        s = PollSchedule(1, 1)
        self.assertEqual((s.interval, s.retry), (10, 5))

    def test_failure_grace(self):
        h = PollHealth()
        h.record(False)
        self.assertFalse(h.tolerate_failure())
        h.record(True)
        h.record(False)
        self.assertTrue(h.tolerate_failure())
        h.record(False)
        self.assertFalse(h.tolerate_failure())
        h.record(True)
        self.assertEqual(h.metrics(), dict(successes=2, failures=3, consecutive_failures=0, success_rate=40.0))

    def test_empty_metrics(self):
        self.assertIsNone(PollHealth().metrics()['success_rate'])
