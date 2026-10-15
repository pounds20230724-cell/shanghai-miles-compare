#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验《上海出发·里程票综合对比表》—— 适配 11 列工具版布局"""
import re, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
from collections import Counter

ns = {}
ns['__file__'] = os.path.join(ROOT, 'src', 'gen_full_table.py')
exec(open(os.path.join(ROOT, 'src', 'gen_full_table.py'), encoding='utf-8').read(), ns)
ca_dom, mu_dom, cz_dom, cz_intl = ns['ca_dom'], ns['mu_dom'], ns['cz_dom'], ns['cz_intl']
CA_ZONE, MU_ZONE = ns['CA_ZONE'], ns['MU_ZONE']
tax_dom, TAX_INTL, fly_total = ns['tax_dom'], ns['TAX_INTL'], ns['fly_total']
rail_info, cash_dom, cash_intl = ns['rail_info'], ns['cash_dom'], ns['cash_intl']
cash_biz, mile_value = ns['cash_biz'], ns['mile_value']
DOMESTIC = ns['DOMESTIC']

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
i0 = html.find('id="master"'); i1 = html.find('</tbody>', i0)
raw = re.findall(r'(<tr[^>]*data-k="([^"]+)"[^>]*>)(.*?)</tr>', html[i0:i1], re.S)
print('行数:', len(raw), '(应为 281)')

def nums(cell):
    t = cell.replace('¥', '').replace(',', '')
    return re.findall(r'\d+(?:\.\d+)?', t)

def cells_of(h):
    return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip()
            for c in re.findall(r'<td[^>]*>(.*?)</td>', h, re.S)]

dom_map = {c: d for c, d in DOMESTIC}
intl_map = {}
for r in ns['INTL']:
    intl_map.setdefault(r[1], []).append(r)

errs = 0; seen = set()
for trow, city, rh in raw:
    c = cells_of(rh)
    if len(c) != 11:
        errs += 1; print(f'  [{city}] 列数 {len(c)} != 11'); continue
    d = int(nums(c[1])[0])
    if city in seen: errs += 1; print('  重复:', city)
    seen.add(city)

    if city in dom_map:
        if dom_map[city] != d: errs += 1; print(f'  [{city}] 距离 {d} != {dom_map[city]}')
        ca, mu, cz = ca_dom(d), mu_dom(d), cz_dom(d)
        cand = [('东航', mu), ('国航', ca), ('南航', cz)]
        exp_reg = '国内'
        exp_tax = tax_dom(d); exp_cash = cash_dom(d); exp_cb = cash_biz(exp_cash, False)
        exp_ft = fly_total(d, False); exp_rail = rail_info(city)
    else:
        m = [r for r in intl_map.get(city, []) if r[2] == d]
        if not m: errs += 1; print(f'  [国际{city}] 无匹配'); continue
        r = m[0]
        ca = CA_ZONE[r[3]] if r[3] else None
        mu = MU_ZONE[r[4]] if r[4] else None
        cand = ([('东航', mu)] if mu else []) + ([('国航', ca)] if ca else [])
        exp_reg = r[0]
        exp_tax = TAX_INTL.get(r[0], 0); exp_cash = cash_intl(d); exp_cb = cash_biz(exp_cash, True)
        exp_ft = fly_total(d, True); exp_rail = None

    got_reg = re.search(r'data-reg="([^"]*)"', trow).group(1)
    if got_reg != exp_reg: errs += 1; print(f'  [{city}] 区域 {got_reg} != {exp_reg}')

    exp_eco = min(x[1][0] for x in cand); exp_bn = [x[0] for x in cand if x[1][0] == exp_eco][0]
    exp_biz = min(x[1][1] for x in cand)
    mn = nums(c[4])
    if not mn or int(float(mn[0])) != exp_eco: errs += 1; print(f'  [{city}] 经济里程 {c[4]} != {exp_eco}')
    if len(mn) < 2 or int(float(mn[1])) != exp_biz: errs += 1; print(f'  [{city}] 公务里程 {c[4]} != {exp_biz}')
    if exp_bn not in c[3]: errs += 1; print(f'  [{city}] 航司 {c[3]} != {exp_bn}')
    if exp_tax != int(nums(c[5])[0]): errs += 1; print(f'  [{city}] 税费 {c[5]} != {exp_tax}')
    cn = nums(c[6])
    if int(float(cn[0])) != exp_cash or int(float(cn[1])) != exp_cb:
        errs += 1; print(f'  [{city}] 现金 {c[6]} != {exp_cash}/{exp_cb}')
    exp_ve = mile_value(exp_cash, exp_tax, exp_eco)
    exp_vb = mile_value(exp_cb, exp_tax, exp_biz)
    vn = nums(c[7])
    if int(float(vn[0])) != exp_ve or int(float(vn[1])) != exp_vb:
        errs += 1; print(f'  [{city}] 价值 {c[7]} != {exp_ve}/{exp_vb}')
    if exp_rail is None:
        if '—' not in c[8]: errs += 1; print(f'  [{city}] 火车应为—: {c[8]}')
    else:
        rn = nums(c[8])
        if int(float(rn[0])) != exp_rail[0] or abs(float(rn[1]) - exp_rail[1]) > .05:
            errs += 1; print(f'  [{city}] 火车 {c[8]} != ¥{exp_rail[0]}/{exp_rail[1]}h')
    if abs(float(nums(c[9])[0]) - exp_ft) > .05: errs += 1; print(f'  [{city}] 飞行 {c[9]} != {exp_ft}')

    if exp_rail is not None:
        dh2 = round(exp_rail[1] - exp_ft, 1); dc2 = exp_rail[0] - exp_cash
    else:
        dh2 = dc2 = None
    if exp_rail is not None and dc2 <= 0 and dh2 <= 0: erc = 'rail'
    elif exp_ve > 500: erc = 'good'
    elif exp_vb > 1000 and exp_vb >= 2 * exp_ve: erc = 'up'
    elif exp_rail is None or dh2 > 6: erc = 'bad'
    elif dc2 <= 0 and dh2 <= 2: erc = 'rail'
    elif dc2 > 0 and dh2 <= 0 and dc2 <= 150: erc = 'rail'
    elif dc2 <= 0 and dh2 <= 3: erc = 'tie'
    else: erc = 'bad'
    a = re.search(r'data-rec="(\w+)"', trow)
    if not a or a.group(1) != erc: errs += 1; print(f'  [{city}] 建议 {a.group(1) if a else "?"} != {erc}')

for need in ['id="cntAll"', 'id="cnt-good"', 'id="cnt-up"', 'id="cnt-rail"', 'id="cnt-bad"',
             'function run()', 'function preset(', 'function exportCSV()', 'function resetAll()',
             'id="tD"', 'id="tE"', 'makeSortable', 'id="fa"']:
    if need not in html: errs += 1; print('  缺少前端要素:', need)
if 'id="fup"' in html: errs += 1; print('  fup 筛选器应已移除')
if html.count('<td') < 281 * 11: errs += 1; print('  单元格总数偏少')

print('分布:', dict(Counter(re.findall(r'data-rec="(\w+)"', html[i0:i1]))))
print('错误数:', errs)
print('OK' if errs == 0 and len(raw) == 281 else 'HAS ERRORS')
