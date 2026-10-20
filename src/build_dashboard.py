"""Build a self-contained, offline interactive Plotly dashboard from cleaned data."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from plotly.offline.offline import get_plotlyjs

ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/'data'/'processed'/'customers_cleaned.csv')
fields=['customer_country','customer_segment','region','gender','age_group','customer_age','customer_acquisition_cost']
records=df[fields].rename(columns={
    'customer_country':'country','customer_segment':'segment',
    'customer_age':'age','customer_acquisition_cost':'cost'
}).to_dict(orient='records')
records_js=json.dumps(records,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
plotly_js=get_plotlyjs().replace('</script','<\\/script')
html=r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Customer Acquisition | Analytics Dashboard</title>
<style>
:root{--navy:#132c4d;--slate:#62738b;--bg:#f4f7fc;--blue:#3763c9;--teal:#1f9984;--orange:#e7a54d;--line:#e4eaf3}
*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--navy)}
.top{background:linear-gradient(115deg,#172f55,#315e9f);padding:31px max(24px,calc((100% - 1320px)/2));color:white}
.top .mini{font-size:12px;letter-spacing:2.2px;font-weight:800;color:#bdd6ff}.top h1{margin:9px 0 5px;font-size:clamp(24px,3vw,38px);font-weight:750}
.top p{margin:0;opacity:.88;font-size:14px;line-height:1.7}.container{max-width:1360px;margin:auto;padding:23px 24px 44px}
.filters{display:flex;gap:12px;align-items:end;flex-wrap:wrap;background:white;padding:18px;border-radius:15px;border:1px solid var(--line);box-shadow:0 6px 24px #1637620a}
.field{min-width:175px;flex:1}.field label{display:block;font-weight:750;font-size:11px;color:var(--slate);text-transform:uppercase;letter-spacing:.8px;margin-bottom:7px}
.field select{width:100%;height:41px;border:1px solid #d7dfec;background:#fff;border-radius:9px;padding:0 10px;color:var(--navy);font-size:14px;cursor:pointer}
button{height:41px;padding:0 18px;border:0;border-radius:9px;background:#e8eefb;font-weight:700;color:#2c579d;cursor:pointer}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}.kpi{padding:18px 20px;border:1px solid var(--line);border-radius:14px;background:white;box-shadow:0 6px 24px #1637620a}
.kpi span{display:block;color:var(--slate);font-size:12px;font-weight:650;margin-bottom:8px}.kpi strong{font-size:28px;letter-spacing:-.6px}.kpi .units{font-size:11px;color:var(--slate);margin-top:8px}
.visuals{display:grid;grid-template-columns:repeat(2,1fr);gap:15px}.chartbox{background:#fff;border:1px solid var(--line);box-shadow:0 6px 24px #1637620a;padding:15px;border-radius:15px;min-width:0}
.chartbox h2{margin:0 0 4px 6px;font-size:16px}.chart{height:320px;width:100%}
.info{margin-top:18px;border-radius:13px;border:1px solid #dbe5f5;background:#ecf2fc;padding:17px 20px;color:#394b6a;font-size:13px;line-height:1.7}
.info strong{color:var(--navy)}.footer{text-align:center;color:var(--slate);font-size:12px;margin-top:22px}
@media(max-width:850px){.visuals{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.kpis{grid-template-columns:1fr}.field{min-width:100%}.container{padding:16px}.top{padding:24px 18px}}
</style><script>__PLOTLY__</script></head><body>
<header class="top"><div class="mini">CUSTOMER INTELLIGENCE / PORTFOLIO PROJECT</div><h1>Acquisition &amp; Segmentation Dashboard</h1>
<p>Explore customer records across markets, demographics and recorded acquisition costs. Filter to compare slices of the dataset.</p></header>
<main class="container"><div class="filters" aria-label="Dashboard filters">
<div class="field"><label for="country">Country</label><select id="country"><option value="">All countries</option></select></div>
<div class="field"><label for="segment">Segment</label><select id="segment"><option value="">All segments</option></select></div>
<div class="field"><label for="region">Region (source label)</label><select id="region"><option value="">All regions</option></select></div>
<div class="field"><label for="gender">Gender</label><select id="gender"><option value="">All genders</option></select></div>
<button type="button" id="reset">Reset filters</button></div>
<section class="kpis">
<div class="kpi"><span>Customers in selection</span><strong id="count">–</strong><div class="units" id="share">Share of total</div></div>
<div class="kpi"><span>Average acquisition cost</span><strong id="meanCost">–</strong><div class="units">Unspecified cost units</div></div>
<div class="kpi"><span>Total recorded acquisition cost</span><strong id="totalCost">–</strong><div class="units">Sum of per-customer cost entries</div></div>
<div class="kpi"><span>Mean customer age</span><strong id="meanAge">–</strong><div class="units">Years</div></div>
</section>
<section class="visuals">
<div class="chartbox"><h2>Customers by country</h2><div id="chartCountry" class="chart"></div></div>
<div class="chartbox"><h2>Customers by segment</h2><div id="chartSegment" class="chart"></div></div>
<div class="chartbox"><h2>Mean acquisition cost by segment</h2><div id="chartSegmentCost" class="chart"></div></div>
<div class="chartbox"><h2>Acquisition cost distribution</h2><div id="chartCostHist" class="chart"></div></div>
<div class="chartbox"><h2>Customer age groups</h2><div id="chartAge" class="chart"></div></div>
<div class="chartbox"><h2>Acquisition cost by country</h2><div id="chartCountryCost" class="chart"></div></div>
</section>
<div class="info"><strong>How to interpret:</strong> Compare customer *counts* separately from mean cost—large segments naturally have larger total cost. Cost currency, acquisition dates, channels and revenue are absent. Source-level postal-code checks have anomalies; this public extract omits names and actual postcodes, and the source may be simulated; it is not verified market intelligence. Dashboard figures recalculate from the rows selected by your filters.</div>
<p class="footer">Offline-ready · All charts reflect the filtered subset · Source: privacy-reduced customer analytics extract</p></main>
<script>
'use strict';
const records=__RECORDS__;
const BLUE='#3763c9',TEAL='#1f9984',ORANGE='#e7a54d',INK='#193655';
const axes={gridcolor:'#eef2f8',zerolinecolor:'#e8edf5',automargin:true};
const chartConfig={displayModeBar:false,responsive:true};
for(const key of ['country','segment','region','gender']){
  const sel=document.getElementById(key);
  [...new Set(records.map(r=>r[key]))].filter(v=>v!=null).sort().forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o)});
  sel.addEventListener('change',render);
}
document.getElementById('reset').addEventListener('click',()=>{['country','segment','region','gender'].forEach(k=>document.getElementById(k).value='');render()});
const num=new Intl.NumberFormat('en-US',{maximumFractionDigits:0});
const fixed=(v)=>Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
function groups(rows,key){const m=new Map();for(const r of rows){const val=r[key]??'Unknown';let x=m.get(val)||{n:0,cost:0};x.n++;x.cost+=r.cost;m.set(val,x)}return [...m.entries()].map(([name,s])=>({name,n:s.n,cost:s.cost,avg:s.cost/s.n})).sort((a,b)=>b.n-a.n)}
function draw(id,traces,layout={}){Plotly.react(id,traces,Object.assign({margin:{t:15,r:15,b:54,l:62},paper_bgcolor:'white',plot_bgcolor:'white',font:{family:'Inter,system-ui,sans-serif',color:'#52647d',size:11},showlegend:false,xaxis:{...axes},yaxis:{...axes}},layout),chartConfig)}
function render(){
 const filters=Object.fromEntries(['country','segment','region','gender'].map(k=>[k,document.getElementById(k).value]));
 const rows=records.filter(r=>Object.entries(filters).every(([key,val])=>!val||r[key]===val));
 const n=rows.length;const costSum=rows.reduce((s,r)=>s+r.cost,0);const ageSum=rows.reduce((s,r)=>s+r.age,0);
 document.getElementById('count').textContent=num.format(n);
 document.getElementById('share').textContent=(100*n/records.length).toFixed(1)+'% of all records';
 document.getElementById('meanCost').textContent=n?fixed(costSum/n):'—';
 document.getElementById('totalCost').textContent=fixed(costSum);
 document.getElementById('meanAge').textContent=n?(ageSum/n).toFixed(1):'—';
 const country=groups(rows,'country'),seg=groups(rows,'segment');
 draw('chartCountry',[{type:'bar',orientation:'h',y:country.map(x=>x.name).reverse(),x:country.map(x=>x.n).reverse(),marker:{color:BLUE},hovertemplate:'%{y}: %{x:,} customers<extra></extra>'}],{margin:{t:15,r:18,b:40,l:94},xaxis:{...axes,title:'Customers'}});
 draw('chartSegment',[{type:'bar',x:seg.map(x=>x.name),y:seg.map(x=>x.n),marker:{color:TEAL},hovertemplate:'%{x}: %{y:,} customers<extra></extra>'}],{yaxis:{...axes,title:'Customers'}});
 draw('chartSegmentCost',[{type:'bar',x:seg.map(x=>x.name),y:seg.map(x=>x.avg),marker:{color:ORANGE},hovertemplate:'%{x}: %{y:.2f} cost units<extra></extra>'}],{yaxis:{...axes,title:'Mean cost (units)'}});
 draw('chartCostHist',[{type:'histogram',x:rows.map(r=>r.cost),nbinsx:25,marker:{color:BLUE},hovertemplate:'Cost: %{x:.2f}<br>Customers: %{y:,}<extra></extra>'}],{xaxis:{...axes,title:'Cost (units)'},yaxis:{...axes,title:'Customers'},bargap:.05});
 const ageOrder=['18–24','25–34','35–44','45–54','55–64','65+'];const ages=groups(rows,'age_group');const agemap=new Map(ages.map(g=>[g.name,g.n]));
 draw('chartAge',[{type:'bar',x:ageOrder,y:ageOrder.map(k=>agemap.get(k)||0),marker:{color:TEAL},hovertemplate:'%{x}: %{y:,} customers<extra></extra>'}],{xaxis:{...axes,title:'Age group'},yaxis:{...axes,title:'Customers'}});
 draw('chartCountryCost',[{type:'bar',orientation:'h',y:country.map(x=>x.name).reverse(),x:country.map(x=>x.avg).reverse(),marker:{color:ORANGE},hovertemplate:'%{y}: %{x:.2f} cost units<extra></extra>'}],{margin:{t:15,r:18,b:45,l:94},xaxis:{...axes,title:'Mean cost (units)'}});
}
render();
</script></body></html>'''
html=html.replace('__PLOTLY__',plotly_js).replace('__RECORDS__',records_js)
path=ROOT/'dashboard'/'customer_dashboard.html'
path.write_text(html,encoding='utf-8')
print('Created',path,'bytes',path.stat().st_size)
