"""Free exchange-hosted closing records. Fail closed; never substitute quotes."""
import datetime as dt
import json
import math
import study as s

def parse_nasdaq(payload,symbol,day):
    if payload.get('status',{}).get('rCode')!=200: raise ValueError('Nasdaq official-close API error')
    data=payload.get('data') or {}
    rows=(data.get('nocp') or {}).get('nocpTable') or []
    matches=[r for r in rows if dt.datetime.strptime(r['date'],'%m/%d/%Y').date().isoformat()==day]
    if len(matches)!=1: raise ValueError('Official close absent or duplicated for requested date')
    p=float(matches[0]['price'].replace('$','').replace(',',''))
    if not math.isfinite(p) or p<=0: raise ValueError('Invalid official close')
    return p

def parse_nyse(rows,symbol,day):
    if not isinstance(rows,list) or not rows: raise ValueError('NYSE auction response empty')
    if any(r.get('symbol')!=symbol or r.get('mic')!='XNYS' for r in rows): raise ValueError('NYSE identity mismatch')
    times=[dt.datetime.strptime(r['tradeDate'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=s.ETZ) for r in rows]
    if any(str(t.date())!=day for t in times): raise ValueError('NYSE wrong date')
    i=max(range(len(rows)),key=lambda i:times[i])
    if times[i]!=s.close_time(day): raise ValueError('Missing actual session-final auction record')
    p=float(rows[i]['price'])
    if not math.isfinite(p) or p<=0: raise ValueError('Invalid NYSE auction price')
    if any(abs(float(r['price'])-p)>.00001 for r in rows): raise ValueError('Inconsistent NYSE auction price')
    return p

def official_close(symbol,day,exchange):
    if not s.session(day) or s.close_time(day)>=s.now(): raise ValueError('Session not completed')
    if exchange in ['NMS','NGM','NCM']:
        url=f'https://api.nasdaq.com/api/company/{symbol}/historical-nocp?timeframe=M6&limit=150'
        raw,meta=s.fetch(url,'Nasdaq Official Closing Price '+symbol)
        p=parse_nasdaq(json.loads(raw),symbol,day);source='Nasdaq Historical NOCP'
    elif exchange=='NYQ':
        date=dt.date.fromisoformat(day).strftime('%m-%d-%Y')
        url=f'https://www.nyse.com/api/auction-charts?symbol={symbol}&tradeDate={date}&auctionType=closing'
        raw,meta=s.fetch(url,'NYSE final closing auction '+symbol)
        p=parse_nyse(json.loads(raw),symbol,day);source='NYSE closing-auction final record, price field'
    else: raise ValueError('No approved exchange closing-price source')
    return dict(session=day,symbol=symbol,close=p,source=source,adjustment='Native session price; cash dividends not added; split conflicts flagged separately',certification='Exchange-hosted official-close/closing-auction record',retrieved_at=meta['retrieved_at'],raw_path=meta['raw_path'],url=meta['url'])

def validate():
    snapshot=json.loads((s.ROOT/'data/latest_snapshot.json').read_text());results=[]
    for row in snapshot['symbols']:
        symbol=row['symbol']
        try:
            day=row['bars'][-1]['date'];official=official_close(symbol,day,row['exchange'])
            diff=abs(official['close']-row['previous_close'])
            results.append(dict(**official,yahoo_close=row['previous_close'],difference=diff,matched=diff<=.005,status='verified' if diff<=.005 else 'discrepancy'))
        except Exception as e:results.append(dict(symbol=symbol,status='failure',reason=str(e)))
    payload=dict(verified_at=s.iso(),snapshot_id=snapshot['snapshot_id'],results=results,verified=sum(r['status']=='verified' for r in results),total=len(results))
    key=s.digest(payload);s.immutable(s.ROOT/'data/validation'/('official-'+key+'.json'),s.dumps(payload).encode())
    s.atomic(s.ROOT/'data/validation/latest_official.json',s.dumps(payload));s.append('official-source-validation:'+key,'source_validation',payload)
    print(s.dumps(payload))
if __name__=='__main__':validate()
