#!/usr/bin/env python3
"""Prospective pilot. Standard library only. See PROTOCOL.md before operating."""
import argparse, csv, datetime as dt, email.utils, hashlib, html, json, math, os
from pathlib import Path
import random, sqlite3, statistics, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ETZ = ZoneInfo('America/Detroit')
UTC = dt.timezone.utc
SECTORS = {
 'Information Technology':'MSFT AAPL NVDA', 'Communication Services':'GOOGL META',
 'Consumer Discretionary':'AMZN HD MCD NKE', 'Financials':'JPM BAC V',
 'Health Care':'UNH JNJ LLY', 'Energy':'XOM CVX COP', 'Industrials':'CAT HON UPS',
 'Consumer Staples':'PG KO WMT', 'Utilities':'NEE DUK SO', 'Real Estate':'PLD AMT',
 'Materials':'LIN'}
SYMBOLS='MSFT AAPL NVDA GOOGL AMZN META JPM BAC V UNH JNJ LLY XOM CVX COP CAT HON UPS PG KO WMT HD MCD NKE NEE DUK SO PLD AMT LIN'.split()
HOLIDAYS=set('2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25 2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25 2027-12-24'.split())
EARLY=set('2026-11-27 2026-12-24 2027-11-26'.split())
def now(): return dt.datetime.now(UTC)
def iso(t=None): return (t or now()).isoformat()
def parse(t):
    x=dt.datetime.fromisoformat(t)
    if x.tzinfo is None: raise ValueError('Timezone required')
    return x
def dumps(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(x if isinstance(x,bytes) else dumps(x).encode()).hexdigest()
def atomic(path, data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    with open(tmp,'wb') as f:
        f.write(data if isinstance(data,bytes) else data.encode()); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def immutable(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise ValueError('Immutable path conflict '+str(path))
        return
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp'); atomic(tmp,data)
    try: os.link(tmp,path)
    finally: tmp.unlink(missing_ok=True)
def session(day):
    d=dt.date.fromisoformat(str(day))
    if not 2026<=d.year<=2027: raise ValueError('Calendar outside validated 2026–2027 range')
    return d.weekday()<5 and str(d) not in HOLIDAYS
def close_time(day): return dt.datetime.fromisoformat(str(day)+('T13:00:00' if str(day) in EARLY else 'T16:00:00')).replace(tzinfo=ETZ)
def previous(day):
    d=dt.date.fromisoformat(str(day))-dt.timedelta(days=1)
    while not session(d): d-=dt.timedelta(days=1)
    return str(d)
def sessions(start,n=60):
    out=[]; d=dt.date.fromisoformat(start)
    while len(out)<n:
        if session(d): out.append(str(d))
        d+=dt.timedelta(days=1)
    return out
def db(root=ROOT):
    p=root/'data/events.sqlite'; p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(p,timeout=30); c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, created TEXT NOT NULL, payload TEXT NOT NULL)')
    for op in ['UPDATE','DELETE']:
        c.execute(f"CREATE TRIGGER IF NOT EXISTS no_{op.lower()} BEFORE {op} ON events BEGIN SELECT RAISE(ABORT,'append-only'); END")
    return c
def append(key,kind,payload,root=ROOT):
    with db(root) as c:
        old=c.execute('SELECT kind,payload FROM events WHERE id=?',(key,)).fetchone()
        if old:
            if old!=(kind,dumps(payload)): raise ValueError('Idempotency conflict '+key)
            return False
        c.execute('INSERT INTO events VALUES(?,?,?,?)',(key,kind,iso(),dumps(payload)))
    return True
def records(kind=None,root=ROOT):
    with db(root) as c:
        q='SELECT id,kind,created,payload FROM events'+(' WHERE kind=?' if kind else '')+' ORDER BY rowid'
        rows=c.execute(q,(kind,) if kind else ()).fetchall()
    # Event metadata wins over payload keys; original payload remains intact in SQLite.
    return [{**json.loads(p),'id':i,'kind':k,'created':t} for i,k,t,p in rows]
def config(): return json.loads((ROOT/'config/study.json').read_text())

def fetch(url,label,cache_seconds=900):
    """Raw bytes, retrieval metadata, bounded retries and same-run cache."""
    folder=ROOT/'data/raw'/now().strftime('%Y-%m-%d'); folder.mkdir(parents=True,exist_ok=True)
    key=digest(url.encode()); index=folder/(key+'.index.json')
    if index.exists():
        m=json.loads(index.read_text())
        if (now()-parse(m['retrieved_at'])).total_seconds()<cache_seconds:
            return (ROOT/m['raw_path']).read_bytes(),m
    errors=[]
    for attempt in range(3):
        time.sleep(0.6 if attempt==0 else 2**attempt)
        t=now()
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (prospective personal research pilot)'})
            with urllib.request.urlopen(req,timeout=12) as r:
                b=r.read(8_000_000); status=r.status; headers=dict(r.headers)
            raw=folder/(key+'-'+t.strftime('%H%M%S%f')+'.raw'); immutable(raw,b)
            m=dict(url=url,label=label,retrieved_at=iso(t),received_at=iso(),http_status=status,headers=headers,sha256=digest(b),raw_path=str(raw.relative_to(ROOT)))
            immutable(raw.with_suffix('.meta.json'),dumps(m).encode()); atomic(index,dumps(m))
            return b,m
        except Exception as e: errors.append(dict(at=iso(),error=str(e)))
    append('fetch-failure:'+key+':'+iso(),'fetch_failure',dict(url=url,label=label,errors=errors))
    raise RuntimeError(str(errors))

def prices(symbol,cutoff):
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
    b,m=fetch(url,'Yahoo chart '+symbol)
    j=json.loads(b)['chart']['result'][0]; meta=j['meta']
    if meta.get('symbol')!=symbol or meta.get('currency')!='USD' or meta.get('instrumentType')!='EQUITY': raise ValueError('Unexpected symbol/currency/instrument')
    if meta.get('exchangeName') not in ['NMS','NYQ','NGM','NCM']: raise ValueError('Unexpected exchange')
    q=j['indicators']['quote'][0]; rows=[]
    for i,t in enumerate(j['timestamp']):
        day=dt.datetime.fromtimestamp(t,ETZ).date().isoformat()
        if not 2026<=int(day[:4])<=2027: continue
        if not session(day) or close_time(day)>=cutoff: continue
        vals=[q[x][i] for x in ['open','high','low','close','volume']]
        if any(v is None or not math.isfinite(v) for v in vals): continue
        o,h,l,c,v=vals
        if min(o,h,l,c)<=0 or v<=0 or l>min(o,c) or h<max(o,c): raise ValueError('Invalid OHLCV')
        rows.append(dict(date=day,open=o,high=h,low=l,close=c,volume=v))
    rows.sort(key=lambda x:x['date'])
    return rows,j.get('events',{}),m,meta

def news(symbol,cutoff):
    # Bounded feed query; no unconstrained web search or article expansion.
    query=f's={symbol}&region=US&lang=en-US'
    b,m=fetch('https://feeds.finance.yahoo.com/rss/2.0/headline?'+query,'Yahoo RSS '+symbol)
    root=ET.fromstring(b); eligible=[]; rejected=[]
    for item in root.findall('.//item'):
        raw={x:item.findtext(x,'') for x in ['title','link','pubDate','description','guid']}
        try: pub=email.utils.parsedate_to_datetime(raw['pubDate']).astimezone(UTC)
        except Exception:
            rejected.append(dict(reason='unparseable publication time',**raw)); continue
        if not cutoff-dt.timedelta(hours=72)<=pub<=cutoff:
            rejected.append(dict(reason='outside 72h cutoff window',**raw)); continue
        text=html.unescape(raw['title'])[:300]
        # Only feed title supplied: summary/article text omitted consistently.
        eligible.append(dict(title=text,url=raw['link'],publication_time=iso(pub),retrieved_at=m['retrieved_at'],source='Yahoo Finance RSS',content_supplied=text))
    eligible.sort(key=lambda x:(x['publication_time'],x['url']),reverse=True)
    unique=[]; seen=set()
    for x in eligible:
        if x['url'] not in seen: unique.append(x); seen.add(x['url'])
    return dict(query=query,query_url=m['url'],retrieval=m,items=unique[:3],excluded_count=len(rejected)+max(0,len(unique)-3),rejected=rejected)

def collect(target,mode='dry_run'):
    begin=now(); cutoff=begin # Publication cutoff is the start, not completion, of collection.
    if mode=='evaluation':
        cfg=config()
        if cfg['status']!='ACTIVE' or target not in cfg['sessions']: raise ValueError('Study not active/session not planned')
        if begin.astimezone(ETZ).date().isoformat()!=target or begin.astimezone(ETZ).time()>=dt.time(9,15): raise ValueError('Outside forecast window')
    expected=previous(target) if mode=='evaluation' else previous(begin.astimezone(ETZ).date())
    out=dict(mode=mode,target_session=target,started_at=iso(begin),information_cutoff=iso(cutoff),expected_last_session=expected,symbols=[],prompt_sha256=digest((ROOT/'config/prompt.txt').read_bytes()))
    for s in SYMBOLS:
        rec=dict(symbol=s,status='input_failure')
        try:
            rows,actions,pm,meta=prices(s,cutoff)
            last=rows[-60:]
            expected_dates=list(reversed([expected]))
            d=expected
            for _ in range(59): d=previous(d); expected_dates.append(d)
            if [r['date'] for r in last]!=sorted(expected_dates): raise ValueError('Missing/stale prior 60 sessions')
            n=news(s,cutoff)
            baseline=last[-1]['close']; official=None
            if config().get('official_close_verified'):
                from official_closes import official_close
                official=official_close(s,expected,meta['exchangeName'])
                if abs(official['close']-baseline)>.005: raise ValueError('Official baseline and Yahoo daily Close disagree')
                baseline=official['close']
                if any(dt.datetime.fromtimestamp(e['date'],ETZ).date().isoformat()==target for e in actions.get('splits',{}).values()): raise ValueError('Target-date split: baseline price units unresolved')
            rec.update(status='ready',bars=last,previous_close=baseline,official_baseline=official,price_source=pm,corporate_actions=actions,news=n,name=meta.get('longName'),exchange=meta['exchangeName'],sector=next(k for k,v in SECTORS.items() if s in v.split()))
        except Exception as e: rec['reason']=str(e)
        out['symbols'].append(rec)
    out['completed_at']=iso(); out['elapsed_seconds']=(now()-begin).total_seconds()
    out['snapshot_id']=digest(out)
    path=ROOT/'data/snapshots'/(out['snapshot_id']+'.json'); immutable(path,dumps(out).encode())
    append('snapshot:'+out['snapshot_id'],'snapshot',dict(path=str(path.relative_to(ROOT)),snapshot_id=out['snapshot_id'],mode=mode,target_session=target,ready=sum(x['status']=='ready' for x in out['symbols']),elapsed_seconds=out['elapsed_seconds']))
    atomic(ROOT/'data/latest_snapshot.json',dumps(out))
    model_input=dict(mode=mode,target_session=target,information_cutoff=out['information_cutoff'],snapshot_id=out['snapshot_id'],symbols=[dict(symbol=r['symbol'],status=r['status'],reason=r.get('reason'),previous_close=r.get('previous_close'),bars=r.get('bars',[]),news=r.get('news',{}).get('items',[])) for r in out['symbols']])
    immutable(ROOT/'data/inputs'/(out['snapshot_id']+'.json'),dumps(model_input).encode())
    return out

def score(p,a):
    b=p['previous_close']; pred=p['predicted_close']; actual=a['close']
    if min(b,pred,actual)<=0: raise ValueError('Nonpositive price')
    pr=pred/b-1; ar=actual/b-1; err=ar-pr; ae=abs(err); be=abs(ar)
    sign=lambda x: 0 if abs(x)<=1e-12 else (1 if x>0 else -1)
    return dict(session=p['session'],symbol=p['symbol'],phase=p['phase'],previous_close=b,predicted_close=pred,actual_close=actual,residual_usd=actual-pred,absolute_error_usd=abs(actual-pred),squared_error_usd=(actual-pred)**2,predicted_return=pr,actual_return=ar,absolute_return_error=ae,baseline_absolute_return_error=be,paired_improvement=be-ae,direction_correct=int(sign(pr)==sign(ar)),baseline_direction_correct=int(sign(ar)==0))

def submit(snapshot_path,response_path,mode):
    snap=json.loads(Path(snapshot_path).read_text()); response=json.loads(Path(response_path).read_text()); t=now()
    if snap['mode']!=mode: raise ValueError('Mode mismatch')
    if digest((ROOT/'config/prompt.txt').read_bytes())!=snap['prompt_sha256']: raise ValueError('Prompt changed')
    if response.get('snapshot_id')!=snap['snapshot_id']: raise ValueError('Wrong snapshot')
    items=response['forecasts']
    if sorted(x['symbol'] for x in items)!=sorted(SYMBOLS): raise ValueError('Need exactly one attempt per symbol')
    phase=response['phase']; cfg=config()
    key=f"batch:{mode}:{phase}:{snap['target_session']}"
    # Rehearsals may repeat, but each immutable input snapshot has its own batch.
    # Evaluation retains exactly one batch per phase/session.
    if mode=='dry_run': key+=':'+snap['snapshot_id']
    old=next((b for b in records('forecast_batch') if b['id']==key),None)
    if old:
        if old['response_sha256']==digest(response): return False
        raise ValueError('Original batch immutable; correction event required')
    generated=parse(response['generated_at'])
    if generated<parse(snap['completed_at']) or generated>t: raise ValueError('Generation timestamp outside actual collection/save interval')
    if t-generated>dt.timedelta(minutes=45): raise ValueError('Stale generated response')
    if phase!=cfg['phase']: raise ValueError('Phase mismatch; model changes need amendment')
    if mode=='evaluation':
        if cfg['status']!='ACTIVE' or snap['target_session'] not in cfg['sessions']: raise ValueError('Not active')
        if t.astimezone(ETZ).date().isoformat()!=snap['target_session'] or t.astimezone(ETZ).time()>=dt.time(9,15): raise ValueError('Late forecast rejected; run mark-missed')
        if t-parse(snap['information_cutoff'])>dt.timedelta(minutes=45): raise ValueError('Stale snapshot')
    rows={x['symbol']:x for x in snap['symbols']}; batch=[]
    for item in items:
        s=item['symbol']; inp=rows[s]; pred=item.get('predicted_close')
        if pred is not None and (isinstance(pred,bool) or not isinstance(pred,(float,int)) or not math.isfinite(pred) or pred<=0): raise ValueError('Invalid prediction')
        if inp['status']!='ready' and pred is not None: raise ValueError('Prediction on failed inputs')
        if pred is None and not item.get('reason'): raise ValueError('Abstention reason required')
        batch.append(dict(session=snap['target_session'],symbol=s,mode=mode,phase=phase,snapshot_id=snap['snapshot_id'],information_cutoff=snap['information_cutoff'],generated_at=response['generated_at'],saved_at=iso(t),model_identity=response.get('model_identity','unavailable'),generation_settings=response.get('generation_settings','unavailable'),context_isolation='unavailable; recurring chat context',previous_close=inp.get('previous_close'),predicted_close=pred,status='published' if pred is not None else 'abstained',reason=item.get('reason',''),rationale=item.get('rationale',''),prompt_sha256=snap['prompt_sha256']))
    # All 30 inserts in one transaction; duplicate unchanged response is a no-op.
    payload=dict(snapshot_id=snap['snapshot_id'],response_sha256=digest(response),forecasts=batch)
    with db() as c:
        old=c.execute('SELECT payload FROM events WHERE id=?',(key,)).fetchone()
        if old:
            if json.loads(old[0])['response_sha256']==digest(response): return False
            raise ValueError('Original batch immutable; correction event required')
        if mode=='evaluation' and any(x['session']==snap['target_session'] for x in records('missing')): raise ValueError('Session already marked missing')
        if mode=='evaluation' and now().astimezone(ETZ).time()>=dt.time(9,14,59): raise ValueError('Publication too close to deadline; conservative 1s safety margin')
        c.execute('INSERT INTO events VALUES(?,?,?,?)',(key,'forecast_batch',iso(),dumps(payload)))
    immutable(ROOT/'data/responses'/(digest(response)+'.json'),dumps(response).encode())
    return True

def mark_missed(at=None,root=ROOT,cfg=None):
    t=at or now(); cfg=cfg or config(); count=0
    if not cfg.get('sessions'): return 0
    published={(p['session'],p['symbol']) for b in records('forecast_batch',root) for p in b['forecasts'] if p['mode']=='evaluation'}
    old={(x['session'],x['symbol']) for x in records('missing',root)}
    for day in cfg['sessions']:
        deadline=dt.datetime.fromisoformat(day+'T09:15:00').replace(tzinfo=ETZ)
        if t<deadline: continue
        for s in SYMBOLS:
            if (day,s) not in published|old:
                count+=append(f'missing:{day}:{s}','missing',dict(session=day,symbol=s,reason='No forecast saved before 09:15 Eastern',status='missing_forecast'),root)
    return count

def reconcile():
    ps=[p for b in records('forecast_batch') for p in b['forecasts'] if p['mode']=='evaluation' and p['status']=='published']
    existing={(x['session'],x['symbol']) for x in records('actual')}; count=0
    for s in SYMBOLS:
        pending=[p for p in ps if p['symbol']==s and (p['session'],s) not in existing and close_time(p['session'])+dt.timedelta(hours=2)<now()]
        if not pending: continue
        try:
            rows,actions,m,meta=prices(s,now()); bydate={r['date']:r for r in rows}
            for p in pending:
                day=p['session']
                # Refuse split-affected units rather than silently changing the frozen baseline.
                splits=actions.get('splits',{}).values()
                conflict=any(dt.datetime.fromtimestamp(e['date'],ETZ).date().isoformat()>=day for e in splits)
                if conflict:
                    append(f'action-flag:{day}:{s}','action_flag',dict(session=day,symbol=s,reason='Split at/after target; price unit alignment requires amendment',actions=actions)); continue
                if day not in bydate: continue
                if not config().get('official_close_verified'): raise ValueError('Official close validation gate not passed')
                from official_closes import official_close
                a=official_close(s,day,meta['exchangeName'])
                if abs(a['close']-bydate[day]['close'])>.005:
                    append(f'close-discrepancy:{day}:{s}','action_flag',dict(session=day,symbol=s,reason='Official close and Yahoo daily close disagree; scoring withheld',official=a,yahoo_close=bydate[day]['close'])); continue
                a['corporate_actions']=actions
                count+=append(f'actual:{day}:{s}','actual',a)
        except Exception as e: append('reconcile-failure:'+s+':'+iso(),'reconcile_failure',dict(symbol=s,error=str(e)))
    return count

def report():
    cfg=config(); ps=[p for b in records('forecast_batch') for p in b['forecasts'] if p['mode']=='evaluation' and p['phase']==cfg['phase']]; actuals=records('actual'); am={(x['session'],x['symbol']):x for x in actuals}
    scored=[score(p,am[(p['session'],p['symbol'])]) for p in ps if p['status']=='published' and (p['session'],p['symbol']) in am]
    missing=records('missing'); daily=[]
    for day in cfg.get('sessions',[]):
        rows=[r for r in scored if r['session']==day]; pp=[p for p in ps if p['session']==day]; mm=[m for m in missing if m['session']==day]
        daily.append(dict(session=day,planned=30,published=sum(p['status']=='published' for p in pp),abstained=sum(p['status']=='abstained' for p in pp),missing=len(mm),scored=len(rows),pending_actual=sum(p['status']=='published' and (day,p['symbol']) not in am for p in pp),coverage=len(rows)/30,mean_improvement=statistics.mean(r['paired_improvement'] for r in rows) if rows else None,model_return_mae=statistics.mean(r['absolute_return_error'] for r in rows) if rows else None,baseline_return_mae=statistics.mean(r['baseline_absolute_return_error'] for r in rows) if rows else None,status='scored' if rows else ('missing' if mm else ('pending_actual' if pp else 'pending_session'))))
    means=[r['mean_improvement'] for r in daily if r['mean_improvement'] is not None]
    perstock=[]
    for s in SYMBOLS:
        rr=[x for x in scored if x['symbol']==s]
        perstock.append(dict(symbol=s,n=len(rr),mae_usd=statistics.mean(x['absolute_error_usd'] for x in rr) if rr else None,rmse_usd=math.sqrt(statistics.mean(x['squared_error_usd'] for x in rr)) if rr else None,return_mae=statistics.mean(x['absolute_return_error'] for x in rr) if rr else None,return_rmse=math.sqrt(statistics.mean(x['absolute_return_error']**2 for x in rr)) if rr else None,baseline_mae_usd=statistics.mean(abs(x['actual_close']-x['previous_close']) for x in rr) if rr else None,baseline_return_mae=statistics.mean(x['baseline_absolute_return_error'] for x in rr) if rr else None,directional_accuracy=statistics.mean(x['direction_correct'] for x in rr) if rr else None,baseline_directional_accuracy=statistics.mean(x['baseline_direction_correct'] for x in rr) if rr else None))
    allmeans=[r['mean_improvement'] for r in daily]
    full=[r['mean_improvement'] for r in daily if r['scored']==30]
    result=dict(as_of=iso(),config=cfg,predictions=ps,actuals=actuals,scored=scored,daily=daily,per_stock=perstock,primary_mean_improvement=statistics.mean(means) if means else None,full_coverage_sensitivity=statistics.mean(full) if full else None,uncertainty={str(length):bootstrap(allmeans,length=length) for length in [1,5,10]},missing=missing,run_log=records(),universe=json.loads((ROOT/'config/universe.json').read_text()) if (ROOT/'config/universe.json').exists() else [])
    atomic(ROOT/'reports/report.json',dumps(result))
    atomic(ROOT/'data/events.jsonl',''.join(dumps(x)+'\n' for x in records()))
    return result
def bootstrap(means,reps=10000,length=5):
    # Retain unscored elapsed days as nulls inside blocks; omit future planned days.
    while means and means[-1] is None: means=means[:-1]
    if sum(x is not None for x in means)<20: return dict(status='unavailable; need at least 20 scored trading days')
    rng=random.Random(20261104); n=len(means); samples=[]
    for _ in range(reps):
        vals=[]
        while len(vals)<n:
            start=rng.randrange(n)
            vals.extend(means[(start+j)%n] for j in range(length))
        finite=[x for x in vals[:n] if x is not None]
        if finite: samples.append(statistics.mean(finite))
    samples.sort()
    return dict(method=f'circular moving blocks of {length} consecutive planned trading-day means; null days retained in blocks',reps=len(samples),seed=20261104,lower=samples[int(.025*len(samples))],upper=samples[int(.975*len(samples))],interpretation='exploratory 95% percentile interval; serial-dependence assumptions; pilot, no significance claim')

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('collect'); a.add_argument('--target',required=True); a.add_argument('--mode',choices=['dry_run','evaluation'],default='dry_run')
    a=sub.add_parser('submit'); a.add_argument('--snapshot',required=True); a.add_argument('--response',required=True); a.add_argument('--mode',choices=['dry_run','evaluation'],required=True)
    for x in ['report','reconcile','mark-missed','status']: sub.add_parser(x)
    a=p.parse_args()
    if a.cmd=='collect':
        out=collect(a.target,a.mode); print(dumps({k:v for k,v in out.items() if k!='symbols'})); print('ready',sum(r['status']=='ready' for r in out['symbols']))
    elif a.cmd=='submit': print('inserted',submit(a.snapshot,a.response,a.mode))
    elif a.cmd=='report':
        r=report(); print(dumps(dict(scored=len(r['scored']),primary=r['primary_mean_improvement'])))
    elif a.cmd=='reconcile': print('actuals added',reconcile())
    elif a.cmd=='mark-missed': print('missing added',mark_missed())
    else: print(dumps(config()))
if __name__=='__main__': main()
