import unittest
from powerline2mqtt.parser import parse_topology
SAMPLE = ''' P/L NET TEI ------ MAC ------ ------ BDA ------ TX RX CHIPSET FIRMWARE
 LOC STA 083 34:E8:94:00:00:01 02:00:00:00:00:01 n/a n/a QCA7420 MAC-QCA7420-example
 REM STA 072 80:CA:4B:00:00:02 82:CA:4B:00:00:02 050 091
 REM CCO 082 80:CA:4B:00:00:03 82:CA:4B:00:00:03 000 165
'''
class ParserTests(unittest.TestCase):
    def test_topology(self):
        rows = parse_topology(SAMPLE)
        self.assertEqual(len(rows),3)
        self.assertIsNone(rows['34:E8:94:00:00:01']['tx'])
        self.assertEqual(rows['80:CA:4B:00:00:02']['rx'],91)
        self.assertEqual(rows['80:CA:4B:00:00:03']['tx'],0)
        self.assertEqual(rows['80:CA:4B:00:00:03']['role'],'CCO')
    def test_empty(self):
        with self.assertRaises(ValueError): parse_topology('')
    def test_bad_row(self):
        with self.assertRaises(ValueError): parse_topology(SAMPLE+'REM bad')
