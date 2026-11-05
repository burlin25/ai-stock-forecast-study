"""Activate only after an actually saved, on-time morning non-evaluation batch."""
import datetime as dt
import json
import study as s

def activate():
    cfg=s.config()
    if cfg['status']=='ACTIVE': return cfg
    if not cfg.get('official_close_verified'): raise ValueError('Official source check incomplete')
    snap=json.loads((s.ROOT/'data/latest_snapshot.json').read_text())
    if snap['mode']!='dry_run': raise ValueError('Expected a non-evaluation rehearsal')
    cutoff=s.parse(snap['information_cutoff']).astimezone(s.ETZ)
    if not s.session(cutoff.date()) or not dt.time(8,30)<=cutoff.time()<dt.time(9,15): raise ValueError('Rehearsal cutoff must be 08:30–09:15 Eastern')
    if len(snap['symbols'])!=30 or any(r['status']!='ready' or not r.get('official_baseline') for r in snap['symbols']): raise ValueError('All 30 official-baseline inputs required')
    batch=next((b for b in s.records('forecast_batch') if b['snapshot_id']==snap['snapshot_id']),None)
    if not batch or len(batch['forecasts'])!=30 or any(p['status']!='published' for p in batch['forecasts']): raise ValueError('All 30 numeric rehearsal forecasts must be saved')
    saved=max(s.parse(p['saved_at']) for p in batch['forecasts']).astimezone(s.ETZ)
    if saved.date()!=cutoff.date() or saved.time()>=dt.time(9,15) or (saved-cutoff).total_seconds()>=2700: raise ValueError('Morning rehearsal missed deadline')
    start=cutoff.date()+dt.timedelta(days=1)
    while not s.session(start):start+=dt.timedelta(days=1)
    cfg.update(status='ACTIVE',start_session=str(start),sessions=s.sessions(str(start)),blockers=[],rehearsal_snapshot_id=snap['snapshot_id'],rehearsal_seconds=(saved-cutoff).total_seconds())
    s.append('study-activation:'+snap['snapshot_id'],'study_activation',dict(start_session=str(start),sessions=cfg['sessions'],phase=cfg['phase'],successful_rehearsal=snap['snapshot_id'],elapsed_seconds=cfg['rehearsal_seconds']))
    s.atomic(s.ROOT/'config/study.json',s.dumps(cfg));return cfg
if __name__=='__main__':print(s.dumps(activate()))
