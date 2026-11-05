"""Synthetic parser fixtures; never written to the research event store."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import official_closes as o

class OfficialCloseTests(unittest.TestCase):
 def test_nasdaq_exact_session_and_missing(self):
  fixture={'status':{'rCode':200},'data':{'nocp':{'nocpTable':[{'date':'11/04/2026','price':'$123.45'}]}}}
  self.assertEqual(o.parse_nasdaq(fixture,'TEST','2026-11-04'),123.45)
  with self.assertRaises(ValueError):o.parse_nasdaq(fixture,'TEST','2026-11-03')
 def test_nyse_final_not_indicative(self):
  rows=[dict(tradeDate='2026-11-04 15:59:00',symbol='TEST',mic='XNYS',price=123.45,avgBookClearingPrice=120),dict(tradeDate='2026-11-04 16:00:00',symbol='TEST',mic='XNYS',price=123.45,avgBookClearingPrice=123.40)]
  self.assertEqual(o.parse_nyse(rows,'TEST','2026-11-04'),123.45)
  with self.assertRaises(ValueError):o.parse_nyse(rows[:1],'TEST','2026-11-04')
  with self.assertRaises(ValueError):o.parse_nyse(rows,'OTHER','2026-11-04')
 def test_early_close(self):
  row=dict(tradeDate='2026-11-27 13:00:00',symbol='TEST',mic='XNYS',price=123)
  self.assertEqual(o.parse_nyse([row],'TEST','2026-11-27'),123)
  row['tradeDate']='2026-11-27 16:00:00'
  with self.assertRaises(ValueError):o.parse_nyse([row],'TEST','2026-11-27')

if __name__=='__main__':unittest.main()
