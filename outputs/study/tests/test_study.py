"""Isolated synthetic fixtures only; no synthetic evaluation records."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('study',Path(__file__).resolve().parents[1]/'scripts/study.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

class StudyTests(unittest.TestCase):
 def test_return_score_and_zero_direction(self):
  p=dict(session='2026-11-05',symbol='TEST',phase='fixture',previous_close=100,predicted_close=102)
  r=s.score(p,dict(close=101))
  self.assertAlmostEqual(r['residual_usd'],-1)
  self.assertAlmostEqual(r['paired_improvement'],0)
  self.assertAlmostEqual(r['absolute_return_error'],.01)
  self.assertEqual(r['direction_correct'],1)
  p['predicted_close']=100
  self.assertEqual(s.score(p,dict(close=101))['direction_correct'],0)
  self.assertEqual(s.score(p,dict(close=100))['direction_correct'],1)
 def test_scale_invariance(self):
  p=dict(session='2026-11-05',symbol='TEST',phase='fixture',previous_close=10,predicted_close=10.4)
  r=s.score(p,dict(close=10.2))
  p.update(previous_close=1000,predicted_close=1040)
  self.assertAlmostEqual(r['paired_improvement'],s.score(p,dict(close=1020))['paired_improvement'])
 def test_calendar_holiday_early_close(self):
  self.assertFalse(s.session('2026-11-26')); self.assertTrue(s.session('2026-11-11'))
  self.assertEqual(s.close_time('2026-11-27').hour,13)
  self.assertEqual(s.previous('2026-11-27'),'2026-11-25')
  self.assertEqual(s.sessions('2026-11-05',60)[-1],'2027-02-02')
 def test_append_only_and_idempotency(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   self.assertTrue(s.append('test','fixture',dict(x=1),root))
   self.assertFalse(s.append('test','fixture',dict(x=1),root))
   with self.assertRaises(ValueError): s.append('test','fixture',dict(x=2),root)
   with s.db(root) as c:
    with self.assertRaises(sqlite3.IntegrityError): c.execute('DELETE FROM events')
    with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE events SET payload='{}'")
 def test_missing_pending_and_duplicate_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); cfg=dict(sessions=['2026-11-05'])
   before=dt.datetime(2026,11,5,9,14,59,tzinfo=s.ETZ)
   self.assertEqual(s.mark_missed(before,root,cfg),0)
   self.assertEqual(s.mark_missed(before+dt.timedelta(seconds=1),root,cfg),30)
   self.assertEqual(s.mark_missed(before+dt.timedelta(days=1),root,cfg),0)
   self.assertEqual(len(s.records('missing',root)),30)
 def test_daily_equal_weight_not_stock_pool(self):
  daily=[[.01]*30,[-.02]]
  equal=s.statistics.mean(s.statistics.mean(day) for day in daily)
  self.assertAlmostEqual(equal,-.005)
  self.assertNotAlmostEqual(equal,s.statistics.mean(sum(daily,[])))
 def test_bootstrap_gate_and_reproducibility(self):
  self.assertIn('unavailable',s.bootstrap([])['status'])
  x=[.01,-.01]*15
  self.assertEqual(s.bootstrap(x,reps=100),s.bootstrap(x,reps=100))
 def test_invalid_score(self):
  with self.assertRaises(ValueError): s.score(dict(previous_close=0,predicted_close=1),dict(close=1))
 def test_payload_metadata_collision(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);s.append('event-key','fixture',dict(id='automation-id',kind='payload-kind'),root)
   row=s.records(root=root)[0]
   self.assertEqual(row['id'],'event-key');self.assertEqual(row['kind'],'fixture')
 def test_submit_atomic_batch_late_and_replay(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder); (root/'config').mkdir();(root/'config/prompt.txt').write_text('fixture prompt')
   snap=dict(mode='evaluation',target_session='2026-11-05',completed_at='2026-11-05T13:35:00+00:00',information_cutoff='2026-11-05T13:30:00+00:00',prompt_sha256=s.digest(b'fixture prompt'),snapshot_id='fixture',symbols=[dict(symbol=z,status='ready',previous_close=100) for z in s.SYMBOLS])
   response=dict(snapshot_id='fixture',phase='fixture',generated_at='2026-11-05T13:40:00+00:00',forecasts=[dict(symbol=z,predicted_close=101) for z in s.SYMBOLS])
   sp=root/'snap.json';rp=root/'response.json';sp.write_text(s.dumps(snap));rp.write_text(s.dumps(response))
   cfg=dict(status='ACTIVE',sessions=['2026-11-05'],phase='fixture')
   with patch.object(s,'ROOT',root),patch.object(s,'config',return_value=cfg),patch.object(s,'db',side_effect=lambda *args:s.sqlite3.connect(root/'events.sqlite')):
    # Explicit test store preserves schema/triggers despite patched default root.
    with s.sqlite3.connect(root/'events.sqlite') as c:c.execute('CREATE TABLE events (id TEXT PRIMARY KEY,kind TEXT,created TEXT,payload TEXT)')
    with patch.object(s,'now',return_value=s.parse('2026-11-05T14:15:00+00:00')):
     with self.assertRaises(ValueError):s.submit(sp,rp,'evaluation')
    self.assertEqual(len(s.records()),0)
    with patch.object(s,'now',return_value=s.parse('2026-11-05T13:41:00+00:00')):
     self.assertTrue(s.submit(sp,rp,'evaluation'))
    self.assertEqual(len(s.records('forecast_batch')[0]['forecasts']),30)
    with patch.object(s,'now',return_value=s.parse('2026-11-06T13:41:00+00:00')):
     self.assertFalse(s.submit(sp,rp,'evaluation'))
    response['forecasts'][0]['predicted_close']=102;rp.write_text(s.dumps(response))
    with self.assertRaises(ValueError):s.submit(sp,rp,'evaluation')

if __name__=='__main__': unittest.main()
