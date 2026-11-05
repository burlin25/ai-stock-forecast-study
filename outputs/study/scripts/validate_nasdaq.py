"""Read-only live cross-check. Nasdaq Close/Last is NOT automatically official NOCP."""
import json
import study as s

def main():
    snap=json.loads((s.ROOT/'data/latest_snapshot.json').read_text()); out=[]
    for inp in snap['symbols']:
        symbol=inp['symbol']; day=inp['bars'][-1]['date']
        end=(s.dt.date.fromisoformat(day)+s.dt.timedelta(days=1)).isoformat()
        start=(s.dt.date.fromisoformat(day)-s.dt.timedelta(days=1)).isoformat()
        url=f'https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=stocks&limit=10&fromdate={start}&todate={end}'
        try:
            b,m=s.fetch(url,'Nasdaq historical cross-check '+symbol)
            j=json.loads(b)
            if not j.get('data'): raise ValueError(s.dumps(j.get('status')))
            rows=j['data']['tradesTable']['rows']
            row=next(r for r in rows if s.dt.datetime.strptime(r['date'],'%m/%d/%Y').date().isoformat()==day)
            value=float(row['close'].replace('$','').replace(',',''))
            diff=abs(value-inp['previous_close'])
            out.append(dict(symbol=symbol,session=day,nasdaq_close_last=value,yahoo_close=inp['previous_close'],absolute_difference=diff,match_within_half_cent=diff<=.005,raw_path=m['raw_path'],url=url,certification='Close/Last; not proven official auction close'))
        except Exception as e: out.append(dict(symbol=symbol,error=str(e)))
    key=s.digest(out)
    s.immutable(s.ROOT/'data/validation'/('nasdaq-crosscheck-'+key+'.json'),s.dumps(out).encode())
    s.append('nasdaq-crosscheck:'+key,'source_validation',dict(results=out,official_close_verified=False))
    print(s.dumps(dict(tested=len(out),matched=sum(r.get('match_within_half_cent',False) for r in out))))
if __name__=='__main__': main()
