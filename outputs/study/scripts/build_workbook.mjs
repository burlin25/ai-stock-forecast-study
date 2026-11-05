import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtime=JSON.parse(await fs.readFile(path.join(root,'config/runtime.json'),'utf8'));
const require=createRequire(path.join(runtime.node_modules,'_study_resolver.cjs'));
const {Workbook,SpreadsheetFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const r=JSON.parse(await fs.readFile(path.join(root,'reports/report.json'),'utf8'));
const wb=Workbook.create();
const names=['Dashboard','Daily Summary','Scored Results','Predictions','Actuals','Stock Universe','Run Log','Readme Protocol'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const navy='#243B53',muted='#526575';
function col(n){let out='';for(;n;n=Math.floor((n-1)/26))out=String.fromCharCode(65+(n-1)%26)+out;return out;}
function base(sheet,lastCol=8,lastRow=25){
 sheet.showGridLines=false;
 const range=sheet.getRange(`A1:${col(lastCol)}${lastRow}`);
 range.format.font={name:'Arial',size:10,color:'#172B4D'};
 range.format.rowHeight=22;range.format.verticalAlignment='center';
 range.format.columnWidth=20;
}
function title(sheet,text){sheet.getRange('A2').values=[[text]];sheet.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};}
function table(name,headers,rows,opts={}){
 const sheet=sheets[name],start=opts.start||5,last=start+Math.max(rows.length,1),n=headers.length;
 base(sheet,n,last+3);title(sheet,opts.title||name);
 sheet.getRange(`A${start}:${col(n)}${start}`).values=[headers];
 sheet.getRange(`A${start}:${col(n)}${start}`).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:34,horizontalAlignment:'center'};
 if(rows.length){
  sheet.getRange(`A${start+1}:${col(n)}${start+rows.length}`).values=rows;
  for(let i=0;i<rows.length;i++)if(i%2===1)sheet.getRange(`A${start+1+i}:${col(n)}${start+1+i}`).format.fill='#F2F5F8';
  sheet.tables.add(`A${start}:${col(n)}${start+rows.length}`,true,name.replace(/ /g,'')+'Table');
 }else{
  sheet.getRange(`A${start+2}`).values=[[opts.empty||'No evaluation records have been published.']];
  sheet.getRange(`A${start+2}`).format.font={name:'Arial',size:10,italic:true,color:muted};
 }
 sheet.freezePanes.freezeRows(start);sheet.freezePanes.freezeColumns(Math.min(2,n));
 return sheet;
}
const d=sheets.Dashboard;base(d,11,34);title(d,'Prospective AI closing-price pilot');d.tabColor=navy;
d.getRange('A4:B14').values=[['Study status',r.config.status],['Start session',r.config.start_session||'Not set — readiness gates open'],['Planned trading sessions',60],['Planned stocks',30],['Planned forecast attempts',null],['Published evaluation forecasts',r.predictions.filter(x=>x.status==='published').length],['Scored evaluation pairs',r.scored.length],['Daily mean paired improvement',r.primary_mean_improvement],['Full-coverage sensitivity',r.full_coverage_sensitivity],['Scored days',r.daily.filter(x=>x.scored>0).length],['Report as of (UTC)',r.as_of]];
d.getRange('B8').formulas=[['=B6*B7']];
d.getRange('A4:A14').format.columnWidth=37;d.getRange('B4:B14').format.columnWidth=48;
d.getRange('B11:B12').setNumberFormat('0.0000%');
d.getRange('B14').setNumberFormat('yyyy-mm-dd hh:mm:ss');
d.getRange('A16').values=[['Primary result is unavailable until real paired outcomes exist.']];
d.getRange('A18').values=[[r.config.official_close_verified?'Official close sources validated for all 30 stocks.':'Open gate: official closing-price verification is unresolved.']];
d.getRange('A19').values=[['Morning non-evaluation rehearsal still required before collection starts.']];
d.getRange('A21').values=[['Agent-assisted phase. Model identity and settings unavailable.']];
d.getRange('A22').values=[['60 sessions form a pilot. The 1,800 planned forecasts are dependent.']];
const counts=Object.entries(r.universe.reduce((a,x)=>(a[x.sector]=(a[x.sector]||0)+1,a),{}));
d.getRange(`D5:E${5+counts.length}`).values=[['Sector','Stocks'],...counts];
d.getRange('D5:E5').format={fill:navy,font:{bold:true,color:'#FFFFFF'}};
d.getRange('D5:D16').format.columnWidth=29;d.getRange('E5:E16').format.columnWidth=10;
const ch=d.charts.add('bar',d.getRange(`D5:E${5+counts.length}`));ch.title='Frozen purposive universe by sector (stocks)';ch.hasLegend=false;ch.setPosition('D18','L34');
ch.xAxis={axisType:'textAxis'};ch.yAxis={numberFormatCode:'0',numberFormatSourceLinked:false};
ch.titleTextStyle.fontSize=11;ch.titleTextStyle.typeface='Arial';
table('Stock Universe',['Symbol','Company','Sector','Exchange','Currency','Last completed session','Input sessions','Min daily shares','Access status','Raw price archive'],r.universe.map(x=>[x.symbol,x.company,x.sector,x.exchange,x.currency,x.last_completed_session,x.input_sessions,x.min_daily_volume,x.access_status,x.price_raw]));
sheets['Stock Universe'].getRange('B6:C35').format.columnWidth=31;
sheets['Stock Universe'].getRange('F6:F35').format.columnWidth=24;
sheets['Stock Universe'].getRange('J6:J35').format.columnWidth=90;
sheets['Stock Universe'].getRange('H6:H35').setNumberFormat('#,##0');
sheets['Stock Universe'].getRange('A3').values=[['Source: Yahoo Finance chart. Broad sector labels are research classifications.']];
table('Predictions',['Session','Symbol','Phase','Predicted close USD','Baseline close USD','Status','Generated at UTC','Saved at UTC','Cutoff UTC','Snapshot ID','Reason'],[...r.predictions.map(x=>[x.session,x.symbol,x.phase,x.predicted_close,x.previous_close,x.status,x.generated_at,x.saved_at,x.information_cutoff,x.snapshot_id,x.reason]),...r.missing.map(x=>[x.session,x.symbol,r.config.phase,null,null,'missing_forecast',null,x.created,null,null,x.reason])]);
table('Actuals',['Session','Symbol','Regular close USD','Retrieval UTC','Source','Adjustment convention','Certification','Raw archive'],r.actuals.map(x=>[x.session,x.symbol,x.close,x.retrieved_at,x.source,x.adjustment,x.certification,x.raw_path]),{empty:'No evaluation actuals yet. Dry-run history is excluded.'});
table('Scored Results',['Session','Symbol','Phase','Baseline USD','Prediction USD','Actual USD','Residual USD','Absolute error USD','Squared error USD2','Predicted return','Actual return','Model abs return error','Baseline abs return error','Paired improvement','Direction correct','Baseline direction correct'],r.scored.map(x=>[x.session,x.symbol,x.phase,x.previous_close,x.predicted_close,x.actual_close,x.residual_usd,x.absolute_error_usd,x.squared_error_usd,x.predicted_return,x.actual_return,x.absolute_return_error,x.baseline_absolute_return_error,x.paired_improvement,x.direction_correct,x.baseline_direction_correct]));
const ss=sheets['Scored Results'],row=10+r.scored.length;
ss.getRange(`A${row}`).values=[['Per-stock evaluation metrics (pending metrics remain blank)']];
ss.getRange(`A${row}`).format.font={bold:true};
ss.getRange(`A${row+2}:K${row+2}`).values=[['Symbol','Scored pairs','MAE USD','RMSE USD','Return MAE','Return RMSE','Baseline MAE USD','Baseline return MAE','Direction accuracy','Baseline direction accuracy','Status']];
ss.getRange(`A${row+2}:K${row+2}`).format={fill:navy,font:{bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:40};
ss.getRange(`A${row+3}:K${row+32}`).values=r.per_stock.map(x=>[x.symbol,x.n,x.mae_usd,x.rmse_usd,x.return_mae,x.return_rmse,x.baseline_mae_usd,x.baseline_return_mae,x.directional_accuracy,x.baseline_directional_accuracy,x.n?'scored':'pending']);
ss.getRange(`E${row+3}:F${row+32}`).setNumberFormat('0.0000%');ss.getRange(`H${row+3}:J${row+32}`).setNumberFormat('0.00%');
table('Daily Summary',['Session','Planned stocks','Published','Abstained','Missing forecasts','Scored pairs','Pending actuals','Scored coverage','Daily mean improvement','Model return MAE','Baseline return MAE','Status'],r.daily.map(x=>[x.session,x.planned,x.published,x.abstained,x.missing,x.scored,x.pending_actual,x.coverage,x.mean_improvement,x.model_return_mae,x.baseline_return_mae,x.status]),{empty:'Start date is unset. No evaluation sessions have been scheduled.'});
if(r.daily.length)sheets['Daily Summary'].getRange(`H6:K${r.daily.length+5}`).setNumberFormat('0.0000%');
if(r.daily.some(x=>x.scored>0)){
 const ds=sheets['Daily Summary'];ds.getRange(`N5:P${r.daily.length+5}`).values=[['Session','Model return MAE','Baseline return MAE'],...r.daily.map(x=>[x.session,x.model_return_mae,x.baseline_return_mae])];
 const chart=ds.charts.add('line',ds.getRange(`N5:P${r.daily.length+5}`));chart.title='Daily absolute return error by arm (%)';chart.hasLegend=true;chart.setPosition('N8','X25');chart.yAxis={numberFormatCode:'0.00%',numberFormatSourceLinked:false};
 chart.series.items[0].line={fill:'#265D8F',style:'solid',width:2};chart.series.items[1].line={fill:'#687786',style:'dashed',width:2};
}
table('Run Log',['Recorded UTC','Event type','Event ID','Mode','Session','Ready symbols','Elapsed seconds','Details'],r.run_log.map(x=>[x.created,x.kind,x.id,x.mode||null,x.target_session||x.session||null,x.ready??null,x.elapsed_seconds??null,JSON.stringify(x).slice(0,30000)]));
sheets['Run Log'].getRange('A6:A100').format.columnWidth=34;sheets['Run Log'].getRange('C6:C100').format.columnWidth=47;sheets['Run Log'].getRange('H6:H100').format.columnWidth=100;
sheets['Run Log'].getRange('A6:A100').setNumberFormat('yyyy-mm-dd hh:mm:ss');
sheets['Run Log'].getRange(`C6:C${Math.max(6,r.run_log.length+5)}`).format.wrapText=true;
sheets['Run Log'].getRange(`A6:H${Math.max(6,r.run_log.length+5)}`).format.rowHeight=48;
const notes=[
 ['Purpose','Prospective pilot. No historical model-performance claims.'],
 ['Protocol','PROTOCOL.md is the full frozen protocol; config/study.json gives current gates.'],
 ['Sample','30 purposively selected US stocks across 11 sectors. No mid-study substitutions.'],
 ['Duration','60 consecutive eligible regular sessions. Start follows successful setup/dry run.'],
 ['Source of truth','data/events.sqlite is append-only. Excel is regenerated from source records.'],
 ['Forecast timing','08:30 America/Detroit weekdays. Saved strictly before 09:15; no backfills.'],
 ['Model arm','agent-assisted-v1; exact identity/settings unavailable; recurring context limitation.'],
 ['Price inputs','Exactly 60 prior completed daily OHLCV sessions. No current intraday bar.'],
 ['News inputs','At most 3 RSS titles per stock, prior 72h, timestamped and bounded by cutoff.'],
 ['Price source','Yahoo Finance daily Close, split adjusted, not dividend adjusted.'],
 ['Official close gate',r.config.official_close_verified?'Validated: Nasdaq Historical NOCP and NYSE completed-session closing-auction price.':'Official close source validation unresolved.'],
 ['Calendar source','https://www.nyse.com/trade/hours-calendars (verified 2026-11-04).'],
 ['Early closes','2026-11-27 and 2026-12-24 at 13:00 Eastern; ordinary close 16:00.'],
 ['Primary metric','Baseline abs return error minus model abs return error; equal stock weight within day, equal day weight.'],
 ['Baseline','Previous valid regular-session close, predicting zero price return.'],
 ['Price residual','Actual minus predicted close, USD. Dollar MAE/RMSE shown per stock.'],
 ['Direction','Down/flat/up; |return| <= 1e-12 is flat. All zero-return cases retained.'],
 ['Coverage','Missing forecasts, abstentions and pending actuals remain separate. No zero imputation.'],
 ['Uncertainty','10,000 circular block-bootstrap replications; 5-day primary block, 1/10 sensitivity. Pilot only.'],
 ['Corporate actions','Retain originals; split unit conflicts flagged pending review. Dividends not added to price return.'],
 ['Dry run','Live archived input validation is non-evaluation. Dry responses never enter result sheets.'],
 ['Refresh','python3 scripts/study.py report; then bundled Node scripts/build_workbook.mjs.'],
 ['Availability','Computer on, app running, workspace/network available through the forecast window.'],
 ['Tab name','Readme Protocol replaces the requested slash, which Excel sheet names do not allow.']
];
table('Readme Protocol',['Item','Definition'],notes);const rp=sheets['Readme Protocol'];rp.getRange('A5:A29').format.columnWidth=27;rp.getRange('B5:B29').format.columnWidth=108;rp.getRange('B6:B29').format.wrapText=true;rp.getRange('B6:B29').format.rowHeight=32;rp.tabColor='#8293A5';
// Standard numeric formats and readable identifier columns.
for(const n of ['Predictions','Actuals','Scored Results']){
 const sh=sheets[n];sh.getRange('A5:A8').format.columnWidth=15;sh.getRange('B5:B8').format.columnWidth=13;
}
if(r.predictions.length)sheets.Predictions.getRange(`D6:E${r.predictions.length+5}`).setNumberFormat('0.00');
if(r.actuals.length)sheets.Actuals.getRange(`C6:C${r.actuals.length+5}`).setNumberFormat('0.00');
if(r.scored.length){ss.getRange(`D6:I${r.scored.length+5}`).setNumberFormat('0.00');ss.getRange(`J6:N${r.scored.length+5}`).setNumberFormat('0.0000%');}
// Disposable boundary change verifies actual engine recalculation, then restores.
d.getRange('B6').values=[[61]];wb.recalculate();
if(d.getRange('B8').values[0][0]!==1830)throw Error('Planned count did not recalculate');
d.getRange('B6').values=[[60]];
wb.recalculate();
if(d.getRange('B8').values[0][0]!==1800)throw Error('Planned count not restored');
const qa=path.join(root,'reports/qa');await fs.mkdir(qa,{recursive:true});
const inspect=await wb.inspect({kind:'table',range:'Dashboard!A4:B14',include:'values,formulas',tableMaxRows:11,tableMaxCols:2,maxChars:4000});
await fs.writeFile(path.join(qa,'dashboard-inspect.ndjson'),inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:4000});
await fs.writeFile(path.join(qa,'formula-errors.ndjson'),errors.ndjson);
for(const name of names){
 const ranges={'Dashboard':'A1:L34','Daily Summary':'A1:F10','Scored Results':`A${row}:K${row+12}`,'Predictions':'A1:F10','Actuals':'A1:F10','Stock Universe':'A1:I14','Run Log':'A1:G13','Readme Protocol':'A1:B29'};
 const image=await wb.render({sheetName:name,range:ranges[name],scale:1.5,format:'png'});
 await fs.writeFile(path.join(qa,name.replaceAll(' ','_')+'.png'),new Uint8Array(await image.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb),temp=path.join(root,'reports/forecast_study.tmp.xlsx');await xlsx.save(temp);await fs.rename(temp,path.join(root,'reports/forecast_study.xlsx'));
console.log(JSON.stringify({sheets:names.length,report:path.join(root,'reports/forecast_study.xlsx'),formulaCheck:errors.ndjson,dashboard:inspect.ndjson}));
