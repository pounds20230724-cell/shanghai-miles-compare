#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《上海出发·里程票综合对比表》—— 单表整合：里程 / 税费 / 现金票价 / 里程价值 / 火车 / 时间 / 综合建议"""
import re, os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.normpath(os.path.join(HERE, '..'))

ns = {}
ns['__file__'] = os.path.join(HERE, 'gen_full_table.py')
exec(open(os.path.join(HERE, 'gen_full_table.py'), encoding='utf-8').read(), ns)

DOMESTIC  = ns['DOMESTIC'];  INTL = ns['INTL']
ca_dom, mu_dom, cz_dom, cz_intl = ns['ca_dom'], ns['mu_dom'], ns['cz_dom'], ns['cz_intl']
CA_ZONE, MU_ZONE = ns['CA_ZONE'], ns['MU_ZONE']
tax_dom, TAX_INTL, fly_total = ns['tax_dom'], ns['TAX_INTL'], ns['fly_total']
rail_info, verdict = ns['rail_info'], ns['verdict']
cash_dom, cash_intl = ns['cash_dom'], ns['cash_intl']
cash_biz = ns['cash_biz']
mile_value, worth_tag, CLS = ns['mile_value'], ns['worth_tag'], ns['CLS']
dom_direct = ns['dom_direct']
DIRC = {'●':'y','○':'s','':'n'}

def fmt(t): return f"{t[0]:,} / {t[1]:,}"

rows = []
n_good = n_up = n_tie = n_rail = n_bad = 0

def build_air_cells(airs):
    """airs: [(名称, (经济,公务) 或 None, 是否理论值)] → 三列 HTML
    绿＝经济舱三家最低；紫＝公务舱三家最低；理论值（南航国际）不参与最低比较"""
    comparable = [(n, t) for n, t, th in airs if t and not th]
    min_e = min((t[0] for _, t in comparable), default=None)
    min_b = min((t[1] for _, t in comparable), default=None)
    out = []
    for name, t, th in airs:
        if not t:
            out.append('<td class="num air"><span class="dim">—</span></td>')
            continue
        e = f'<span class="{"be" if (not th and min_e is not None and t[0] == min_e) else "pe"}">{t[0]:,}</span>'
        b = f'<span class="{"bb" if (not th and min_b is not None and t[1] == min_b) else "pb"}">{t[1]:,}</span>'
        tip = ' title="南航国际为距离制理论值（上海无洲际直飞），仅供参考"' if th else ''
        out.append(f'<td class="num air{" theory" if th else ""}"{tip}>{e}<span class="h">/</span>{b}</td>')
    return ''.join(out)

def emit(city, reg, d, dr, airs, eco_miles, eco_name, biz_miles, tax,
         cash_eco, cash_biz_val, val_eco, val_biz, rail, ft):
    """经济舱优先 · 阈值：经济>500；公务>1000 且 ≥经济2倍；火车与飞机比现金票"""
    global n_good, n_up, n_tie, n_rail, n_bad
    dcode = DIRC[dr]
    up_miles = biz_miles - eco_miles
    up_val = round((cash_biz_val - cash_eco) / up_miles * 10000) if up_miles > 0 else 0
    if rail is None:
        dh = dc = None
        train_line = '无铁路替代'
    else:
        rp, rh = rail
        dh = round(rh - ft, 1)
        dc = rp - cash_eco
        th = f'飞机快{dh}h' if dh >= 0 else f'火车快{abs(dh)}h'
        tc = f'火车省¥{abs(dc):,}' if dc < 0 else f'机票省¥{dc:,}'
        train_line = f'{th} · {tc}'
    if rail is not None and dc <= 0 and dh <= 0:
        rec, rcls = '🚄 坐火车', 'rail'
    elif val_eco > 500:
        rec, rcls = '✅ 里程换经济', 'good'
    elif val_biz > 1000 and val_biz >= 2 * val_eco:
        rec, rcls = '💺 里程换公务', 'up'
    elif rail is None or dh > 6:
        rec, rcls = '❌ 买现金票', 'bad'
    elif dc <= 0 and dh <= 2:
        rec, rcls = '🚄 坐火车', 'rail'      # 火车更便宜，飞机只快 ≤2h → 坐火车
    elif dc > 0 and dh <= 0 and dc <= 150:
        rec, rcls = '🚄 坐火车', 'rail'
    elif dc <= 0 and dh <= 3:
        rec, rcls = '⚖️ 看情况', 'tie'
    else:
        rec, rcls = '❌ 买现金票', 'bad'
    if rcls == 'good': n_good += 1
    elif rcls == 'up': n_up += 1
    elif rcls == 'rail': n_rail += 1
    elif rcls == 'tie': n_tie += 1
    else: n_bad += 1
    rail_cell = f'¥{rail[0]:,}<span class="h">/</span>{rail[1]}h' if rail else '<span class="dim">—</span>'
    dirb = {'y':'<span class="yes">●</span>','s':'<span class="q">○</span>','n':''}[dcode]
    ce = 'v-good' if val_eco > 500 else ('v-mid' if val_eco > 350 else 'v-bad')
    cb = 'v-good' if (val_biz > 1000 and val_biz >= 2 * val_eco) else ('v-mid' if val_biz > 800 else 'v-bad')
    up_note = f'<span class="upn">升公务 +{up_miles:,} · 增益 {up_val:,}/万</span>' if rcls == 'up' else ''
    rows.append(
        f'<tr data-k="{city}" data-reg="{reg}" data-direct="{dcode}" data-d="{d}" '
        f'data-air="{eco_name}" data-rec="{rcls}" data-val="{val_eco}" data-valb="{val_biz}" data-up="{up_miles}">'
        f'<td class="c-city"><b>{city}</b><span class="reg">{reg}</span></td>'
        f'<td class="num">{d:,}</td>'
        f'<td class="ctr">{dirb}</td>'
        f'{build_air_cells(airs)}'
        f'<td class="num">¥{tax:,}</td>'
        f'<td class="num">¥{cash_eco:,}<span class="h">/</span>¥{cash_biz_val:,}</td>'
        f'<td class="num"><b class="{ce}">{val_eco:,}</b><span class="h">/</span><b class="{cb}">{val_biz:,}</b></td>'
        f'<td class="num">{rail_cell}</td>'
        f'<td class="num">{ft}h</td>'
        f'<td class="vd"><span class="tag {rcls}">{rec}</span>{up_note}<span class="sub">{train_line}</span></td>'
        f'</tr>')

# ---------- 国内 ----------
for city, d in DOMESTIC:
    ca, mu, cz = ca_dom(d), mu_dom(d), cz_dom(d)
    cands = [('东航', mu), ('国航', ca), ('南航', cz)]  # 并列时优先东航（上海主基地）
    eco_miles = min(x[1][0] for x in cands); eco_name = [x[0] for x in cands if x[1][0] == eco_miles][0]
    biz_miles = min(x[1][1] for x in cands)
    tax = tax_dom(d)
    cash_eco = cash_dom(d); cash_bv = cash_biz(cash_eco, False)
    val_eco = mile_value(cash_eco, tax, eco_miles)
    val_biz = mile_value(cash_bv, tax, biz_miles)
    emit(city, '国内', d, dom_direct(city),
         [('国航', ca, False), ('东航', mu, False), ('南航', cz, False)],
         eco_miles, eco_name, biz_miles,
         tax, cash_eco, cash_bv, val_eco, val_biz, rail_info(city), fly_total(d, False))

# ---------- 国际（最优不含南航理论值） ----------
for region, city, d, caz, muz, direct in INTL:
    ca = CA_ZONE[caz] if caz else None
    mu = MU_ZONE[muz] if muz else None
    cz = cz_intl(d)
    cand = ([('东航', mu)] if mu else []) + ([('国航', ca)] if ca else [])  # 并列时优先东航
    eco_miles = min(x[1][0] for x in cand); eco_name = [x[0] for x in cand if x[1][0] == eco_miles][0]
    biz_miles = min(x[1][1] for x in cand)
    tax = TAX_INTL.get(region, 0)
    cash_eco = cash_intl(d); cash_bv = cash_biz(cash_eco, True)
    val_eco = mile_value(cash_eco, tax, eco_miles)
    val_biz = mile_value(cash_bv, tax, biz_miles)
    emit(city, region, d, direct,
         [('国航', ca, False), ('东航', mu, False), ('南航', cz, True)],
         eco_miles, eco_name, biz_miles,
         tax, cash_eco, cash_bv, val_eco, val_biz, None, fly_total(d, True))

rows_html = ''.join(rows)
total = len(rows)

CSS = """
:root{--ink:#16181d;--ink2:#414855;--mut:#8a93a3;--line:#e3e6ec;--bg:#f5f6f8;--card:#fff;
--ca:#C8102E;--mu:#1D4E9E;--cz:#0F766E;--up:#7A1FA2;--ok:#0F766E;--mid:#B8860B;--no:#C8102E;--rad:10px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",-apple-system,BlinkMacSystemFont,sans-serif;
background:var(--bg);color:var(--ink);font-size:13px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1420px;margin:0 auto;padding:0 16px 40px}
/* ---- 顶栏 ---- */
.top{background:#171c25;color:#fff;padding:14px 0 12px}
.top h1{font-size:16px;font-weight:800;letter-spacing:.01em;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.top h1 small{font-weight:500;font-size:12px;color:#8d99ab;letter-spacing:.02em}
.top .meta{margin-top:7px;display:flex;flex-wrap:wrap;gap:14px;font-size:11.5px;color:#93a0b3}
.top .meta b{color:#e6ebf3;font-weight:700}
/* ---- 卡片/控件 ---- */
.panel{background:var(--card);border:1px solid var(--line);border-radius:var(--rad);padding:9px 11px;margin-top:10px}
.panel.sticky{position:sticky;top:0;z-index:30;box-shadow:0 2px 10px rgba(16,24,40,.06)}
.row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.row+.row{margin-top:7px;padding-top:7px;border-top:1px dashed var(--line)}
input[type=text]{flex:0 1 168px;min-width:120px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;outline:none;background:#fbfcfd}
input[type=text]:focus{border-color:#9db2cf;background:#fff}
.sel{padding:6px 8px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;background:#fbfcfd;color:var(--ink2);outline:none;max-width:150px}
.sel:focus{border-color:#9db2cf;background:#fff}
.btn{padding:6px 11px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;background:#fff;color:var(--ink2);cursor:pointer}
.btn:hover{background:#f0f3f7;border-color:#c9d2df}
.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chipbtn{padding:5px 11px;border:1px solid var(--line);border-radius:999px;font-size:12px;background:#fff;color:var(--ink2);cursor:pointer;white-space:nowrap}
.chipbtn:hover{background:#f0f3f7}
.chipbtn.on{background:#1b2028;color:#fff;border-color:#1b2028}
.spacer{flex:1}
.hint{color:#b6bcc7;font-size:11.5px}
/* ---- 状态条 ---- */
.status{display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:12px;color:var(--mut);padding:7px 2px 0}
.status b{font-variant-numeric:tabular-nums;color:var(--ink)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;vertical-align:1px}
.d-g{background:var(--ok)}.d-u{background:var(--up)}.d-r{background:#1D4E9E}.d-b{background:#b6bcc7}
/* ---- 折叠说明 ---- */
details{border:1px solid var(--line);border-radius:var(--rad);background:#fff;margin-top:10px}
summary{cursor:pointer;padding:9px 12px;font-size:12.5px;font-weight:700;color:var(--ink2);list-style:none;display:flex;align-items:center;gap:7px}
summary::-webkit-details-marker{display:none}
summary:before{content:'';width:0;height:0;border-left:4.5px solid #8a93a3;border-top:4px solid transparent;border-bottom:4px solid transparent;transition:.15s}
details[open] summary:before{transform:rotate(90deg)}
details[open] summary{border-bottom:1px solid var(--line)}
.doc{padding:10px 13px 12px;font-size:12.2px;color:var(--ink2);line-height:1.75}
.doc b{color:var(--ink)}
.doc br{display:block;content:'';margin-top:3px}
/* ---- 表格 ---- */
.tw{margin-top:10px;border:1px solid var(--line);border-radius:var(--rad);background:#fff;overflow:auto;max-height:76vh}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:12.3px;min-width:1220px}
th,td{padding:6px 9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:middle;white-space:nowrap}
thead th{background:#242b36;color:#dfe5ee;font-weight:700;font-size:11.5px;position:sticky;top:0;z-index:6;cursor:pointer;user-select:none}
thead th:hover{background:#2c3542}
thead th:after{content:'';display:inline-block;width:0;height:0;margin-left:5px;
  border-left:3.5px solid transparent;border-right:3.5px solid transparent;border-bottom:4.5px solid rgba(255,255,255,.32);vertical-align:middle}
thead th[data-dir="asc"]:after{border-bottom-color:#fff}
thead th[data-dir="desc"]:after{border-bottom-color:transparent;border-top:4.5px solid #fff}
tbody tr:nth-child(even){background:#fafbfc}
tbody tr:hover{background:#eef4fc}
td:first-child,th:first-child{position:sticky;left:0;z-index:5;background:#fff;box-shadow:1px 0 0 var(--line)}
thead th:first-child{z-index:9;background:#242b36}
tbody tr:nth-child(even) td:first-child{background:#fafbfc}
tbody tr:hover td:first-child{background:#eef4fc}
td.num{font-variant-numeric:tabular-nums}
td.ctr{text-align:center}
.pe,.pb{color:#7c8694}
.be{color:var(--ok);font-weight:800}
.bb{color:var(--up);font-weight:800}
td.air.theory .pe,td.air.theory .pb{color:#c9d0da}
.h{color:#c3cad6;margin:0 3px;font-weight:400}
.dim{color:#b0b7c3}
.c-city b{font-size:12.6px}
.c-city .reg{display:block;font-size:10.5px;color:var(--mut);font-weight:400;margin-top:-1px}
.yes{color:var(--ok);font-weight:800}.q{color:var(--mid);font-weight:800}
.v-good{color:var(--ok)}.v-mid{color:var(--mid)}.v-bad{color:#9aa3b2}
.upn{display:block;font-size:10.5px;color:var(--up);font-weight:700}
td.vd{white-space:normal;min-width:150px}
td.vd .sub{display:block;font-size:10.8px;color:var(--mut);line-height:1.35;margin-top:1px}
.tag{display:inline-block;font-size:10.6px;font-weight:700;padding:1px 7px;border-radius:5px;line-height:1.6}
.tag.ca{background:#fdecef;color:var(--ca)}.tag.mu{background:#e9eefa;color:var(--mu)}.tag.cz{background:#e5f4f2;color:var(--cz)}
.tag.good{background:#e3f4f0;color:var(--ok)}.tag.up{background:#f0e8f8;color:var(--up)}
.tag.rail{background:#e9eefa;color:#1D4E9E}.tag.bad{background:#f6f7f9;color:#8a93a3}.tag.tie{background:#fff5e0;color:var(--mid)}
/* ---- 附表 ---- */
.sub-tbl{margin-top:10px}
footer{margin-top:16px;padding-top:12px;border-top:1px solid var(--line);font-size:11.5px;color:var(--mut);line-height:1.7}
.hide{display:none}
"""

SCRIPT_JS = r"""
<script>
function bandOK(d,band){ if(!band) return true; d=parseInt(d,10); var p=band.split('-');
  return d>=parseInt(p[0],10)&&d<=parseInt(p[1],10); }
function makeSortable(id){
  var t=document.getElementById(id); if(!t) return;
  var heads=t.tHead.rows[0].cells;
  for(var i=0;i<heads.length;i++){(function(i){
    heads[i].addEventListener('click',function(){
      var tb=t.tBodies[0], rows=Array.prototype.slice.call(tb.rows);
      var dir=heads[i].getAttribute('data-dir')==='asc'?-1:1;
      for(var k=0;k<heads.length;k++) heads[k].removeAttribute('data-dir');
      heads[i].setAttribute('data-dir',dir===1?'asc':'desc');
      rows.sort(function(a,b){
        var x=a.cells[i].innerText.trim(), y=b.cells[i].innerText.trim();
        var nx=parseFloat(x.replace(/[^0-9.]/g,'')), ny=parseFloat(y.replace(/[^0-9.]/g,''));
        if(!isNaN(nx)&&!isNaN(ny)&&/[0-9]/.test(x)&&/[0-9]/.test(y)) return (nx-ny)*dir;
        return x.localeCompare(y,'zh')*dir;});
      for(var k=0;k<rows.length;k++) tb.appendChild(rows[k]);
    });})(i);
  }
}
['master','tD','tE'].forEach(makeSortable);

var CNT={good:0,up:0,rail:0,tie:0,bad:0};
function run(){
  var q=document.getElementById('q').value.trim().toLowerCase();
  var reg=document.getElementById('fr').value, dir=document.getElementById('fdir').value;
  var band=document.getElementById('fd').value, air=document.getElementById('fa').value;
  var rec=document.getElementById('frec').value;
  var t=document.getElementById('master').tBodies[0].rows;
  var n=0, c={good:0,up:0,rail:0,tie:0,bad:0};
  for(var i=0;i<t.length;i++){
    var r=t[i], ok=true;
    if(q) ok=(r.getAttribute('data-k')||'').toLowerCase().indexOf(q)>-1;
    if(ok && reg) ok=(r.getAttribute('data-reg')||'')===reg;
    if(ok && dir) ok=(r.getAttribute('data-direct')||'')===dir;
    if(ok) ok=bandOK(r.getAttribute('data-d'),band);
    if(ok && air) ok=(r.getAttribute('data-air')||'')===air;
    if(ok && rec) ok=(r.getAttribute('data-rec')||'')===rec;
    r.classList.toggle('hide',!ok);
    if(ok){ n++; var k=r.getAttribute('data-rec'); if(c[k]!==undefined) c[k]++; }
  }
  document.getElementById('cntAll').textContent=n;
  for(var k2 in c){ var el=document.getElementById('cnt-'+k2); if(el) el.textContent=c[k2]; }
}
function resetAll(){
  ['q','fr','fdir','fd','fa','frec'].forEach(function(x){document.getElementById(x).value='';});
  setChip(null); run();
}
function setChip(el){
  var cs=document.querySelectorAll('.chipbtn');
  for(var i=0;i<cs.length;i++) cs[i].classList.remove('on');
  if(el) el.classList.add('on');
  else document.querySelector('.chipbtn[data-p="all"]').classList.add('on');
}
function preset(el,p){
  ['q','fr','fdir','fd','fa','frec'].forEach(function(x){document.getElementById(x).value='';});
  if(p==='muup'){ document.getElementById('fa').value='东航'; document.getElementById('frec').value='up'; }
  if(p==='eco') document.getElementById('frec').value='good';
  if(p==='rail') document.getElementById('frec').value='rail';
  if(p==='direct') document.getElementById('fdir').value='y';
  setChip(el); run();
}
function exportCSV(){
  var t=document.getElementById('master');
  var hs=[].map.call(t.tHead.rows[0].cells,function(c){return c.innerText.replace(/\n/g,' ').trim();});
  var out=[hs.join(',')], rows=t.tBodies[0].rows;
  for(var i=0;i<rows.length;i++){
    if(rows[i].classList.contains('hide')) continue;
    out.push([].map.call(rows[i].cells,function(c){return '"'+c.innerText.replace(/\s+/g,' ').replace(/"/g,'""').trim()+'"';}).join(','));
  }
  var blob=new Blob(['\ufeff'+out.join('\n')],{type:'text/csv;charset=utf-8'});
  var a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='上海出发里程票对比.csv'; a.click();
}
document.getElementById('q').addEventListener('input',run);
['fr','fdir','fd','fa','frec'].forEach(function(x){document.getElementById(x).addEventListener('change',run);});
document.querySelector('.chipbtn[data-p="all"]').classList.add('on');
run();
</script>
</body>
</html>
"""

BODY = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>上海出发 · 里程票对比工具</title>
<style>{CSS}</style>
</head>
<body>
<div class="top"><div class="wrap">
  <h1>上海出发 · 里程票对比 <small>国航 / 东航 / 南航 ｜ {total} 个目的地 ｜ 2026-10</small></h1>
  <div class="meta">
    <span>✅ 里程换经济 <b>{n_good}</b></span>
    <span>💺 里程换公务 <b>{n_up}</b></span>
    <span>🚄 坐火车 <b>{n_rail}</b></span>
    <span>❌ 买现金票 <b>{n_bad}</b></span>
  </div>
</div></div>

<div class="wrap">

<details>
<summary>口径与判定规则</summary>
<div class="doc">
<b>里程</b>＝三家官方标准兑换表单程值（经济/公务），每行<b>三列分列完整展示</b>：<b style="color:#0F766E">绿字</b>＝经济舱三家最低，<b style="color:#7A1FA2">紫字</b>＝公务舱三家最低，灰字为其余报价。<b>南航*</b>：国际航线为距离制换算的理论值（上海无南航洲际直飞），灰色显示、不参与"最低"比较，仅供对照。<br>
<b>税费</b>＝民航发展基金 50 + 燃油附加费（≤800km 50 / &gt;800km 90）→ 国内 ¥100/¥140；国际按区域中值（港澳台 250、日韩 350、东南亚 400、南亚中亚 600、北美 1,000、大洋洲 1,100、欧洲 1,400、非洲南美 1,300）。<br>
<b>现金票</b>＝一般折扣价（排除红眼航班与廉航特价）：国内 300+0.25×距离；国际 ≤3,000km 800+0.24×距离、&gt;3,000km 分段；公务舱＝经济舱 ×3（国内）/ ×4（国际）。<br>
<b>里程价值（元/万）</b>＝（现金票 − 税费）÷ 里程 × 10,000，即"每用一万里程能省多少钱"。<br>
<b>判定</b>：① 火车又便宜又快 → 🚄；② 经济舱 &gt;500 → ✅ 里程换经济；③ 公务舱 &gt;1000 且 ≥经济 2 倍 → 💺 里程换公务；④ 无铁路或火车慢 &gt;6h → ❌ 买现金票；⑤ 火车更便宜且飞机只快 ≤2h → 🚄 坐火车；⑥ 其余按现金价差与时间差裁决。<br>
<b>火车比价</b>直接比现金票（火车二等座票价 vs 机票现金价），不拿火车票比里程票税费。<b>飞行+值机</b>＝飞行时长 + 国内 2h / 国际 3h。<b>火车</b>按线路等级推算，误差 ±15–20%，以 12306 为准。
</div>
</details>

<div class="panel sticky">
  <div class="row">
    <input type="text" id="q" placeholder="搜索目的地">
    <select id="fr" class="sel">
      <option value="">区域不限</option><option value="国内">国内</option>
      <option value="中国港澳台">中国港澳台</option><option value="东北亚">东北亚</option>
      <option value="东南亚">东南亚</option><option value="南亚·中亚·中东·北非">南亚·中亚·中东·北非</option>
      <option value="欧洲">欧洲</option><option value="北美·夏威夷">北美·夏威夷</option>
      <option value="大洋洲">大洋洲</option><option value="非洲·南美">非洲·南美</option>
    </select>
    <select id="fdir" class="sel">
      <option value="">直飞不限</option><option value="y">● 有直飞</option>
      <option value="s">○ 季节性</option><option value="n">无直飞</option>
    </select>
    <select id="fd" class="sel">
      <option value="">距离不限</option><option value="0-600">≤600km</option>
      <option value="600-1200">600–1,200</option><option value="1200-2000">1,200–2,000</option>
      <option value="2000-3000">2,000–3,000</option><option value="3000-5000">3,000–5,000</option>
      <option value="5000-99999">&gt;5,000km</option>
    </select>
    <select id="fa" class="sel" title="筛出某家航司经济舱里程最划算的航线">
      <option value="">航司不限</option><option value="国航">国航最优</option>
      <option value="东航">东航最优</option><option value="南航">南航最优</option>
    </select>
    <select id="frec" class="sel">
      <option value="">建议不限</option><option value="good">✅ 里程换经济</option>
      <option value="up">💺 里程换公务</option><option value="rail">🚄 坐火车</option>
      <option value="tie">⚖️ 看情况</option><option value="bad">❌ 买现金票</option>
    </select>
    <button class="btn" onclick="resetAll()">重置</button>
  </div>
  <div class="row">
    <div class="chips">
      <button class="chipbtn" data-p="all" onclick="preset(this,'all')">全部</button>
      <button class="chipbtn" data-p="muup" onclick="preset(this,'muup')">东航升公务</button>
      <button class="chipbtn" data-p="eco" onclick="preset(this,'eco')">里程换经济</button>
      <button class="chipbtn" data-p="rail" onclick="preset(this,'rail')">坐火车</button>
      <button class="chipbtn" data-p="direct" onclick="preset(this,'direct')">有直飞</button>
    </div>
    <div class="spacer"></div>
    <button class="btn" onclick="exportCSV()">导出 CSV</button>
  </div>
  <div class="status">
    显示 <b id="cntAll">{total}</b> / {total} 条
    <span><i class="dot d-g"></i>经济 <b id="cnt-good">0</b></span>
    <span><i class="dot d-u"></i>公务 <b id="cnt-up">0</b></span>
    <span><i class="dot d-r"></i>火车 <b id="cnt-rail">0</b></span>
    <span><i class="dot d-b"></i>买票 <b id="cnt-bad">0</b></span>
    <span class="spacer"></span>
    <span class="hint">点列头可排序 · 航司筛选＝该航司经济舱里程最划算 · 绿/紫＝三家最低</span>
  </div>
</div>

<div class="tw">
<table id="master">
<thead><tr>
  <th>目的地</th><th>距离<br>km</th><th>直飞</th>
  <th>国航<br>经/公</th><th>东航<br>经/公</th><th>南航*<br>经/公</th>
  <th>税费</th><th>现金票 经/公</th><th>里程价值 经/公<br>元/万</th>
  <th>火车</th><th>飞行<br>+值机</th><th>建议</th>
</tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>

<details class="sub-tbl">
<summary>附表 · 南航 26 条国内特殊航线（往返价，低于距离表）</summary>
<div class="tw" style="margin:0;border:0;border-radius:0;max-height:none">
<table id="tD">
<thead><tr><th>国内航段</th><th>经济舱</th><th>明珠经济舱</th><th>公务舱</th><th>头等舱</th></tr></thead>
<tbody>{ns['rows_sp_dom']}</tbody>
</table>
</div>
</details>

<details class="sub-tbl">
<summary>附表 · 南航 8 条国际特殊航线（往返价）</summary>
<div class="tw" style="margin:0;border:0;border-radius:0;max-height:none">
<table id="tE">
<thead><tr><th>国际航段</th><th>经济舱</th><th>明珠经济舱</th><th>公务舱</th><th>头等舱</th></tr></thead>
<tbody>{ns['rows_sp_intl']}</tbody>
</table>
</div>
</details>

<footer>
数据来源：三家官方标准兑换表（国航凤凰知音 / 东航东方万里行 / 南航明珠俱乐部，含 26+8 条特殊航线）；燃油附加费为 2026-10-10 起标准。<br>
距离为约值，边界航线（600/800/1,200/1,700/1,800/2,000/2,400km）请以航司里程计算器复核；现金票价与火车票价为模型估算，以购票系统与 12306 实时为准。整理日期 2026-10-15，不构成消费建议。
</footer>

</div>
"""

path = os.path.join(OUT, 'index.html')
open(path, 'w', encoding='utf-8').write(BODY + SCRIPT_JS)
print('OK ->', path)
print('rows:', total, '| 经济:', n_good, '| 公务:', n_up, '| 火车:', n_rail, '| 买票:', n_bad)
