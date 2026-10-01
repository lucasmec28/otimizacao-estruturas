"""M22 Excel interchange. Partial first-order service, never design approval."""
import argparse, hashlib, json, math, re
from pathlib import Path
import numpy as np
from mezzanine import Geometry, Section, hypotheses, analyze, divisions

FILES=('bridge_m22.py','mezzanine.py','frame.py','linear_algebra.py','legacy_frame.py','serviceability.py')
PARAMS=('lx_mm','ly_mm','height_mm','xmin_mm','xmax_mm','ymin_mm','ymax_mm','smin_mm','smax_mm','g_floor_kpa','q_floor_kpa','hx_total_kn','E_mpa','column_limit','primary_limit','secondary_limit')
FAMILIES=('ELS_RARA','ELS_FREQUENTE','ELS_QUASE_PERMANENTE')
MAX_CASES=1000
MAX_COMBINATIONS=1000
COMPONENTS=('COLUNA_X','PRINCIPAL','SECUNDARIA')
COLUMNS=('id','combination','family','component','signed_mm','limit_mm','eta','location','subtotal_kg','kg_m2','balance','horizontal_action')
def engine_id():
    h=hashlib.sha256()
    for name in FILES:h.update(name.encode()+b'\0'+Path(__file__).with_name(name).read_bytes())
    return h.hexdigest()
def normalized(text):return text.lstrip('\ufeff').replace('\r\n','\n').rstrip('\n')+'\n'
def number(x):
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',x):raise ValueError('INVALID_NUMBER: '+x)
    n=float(x)
    if not math.isfinite(n):raise ValueError('NONFINITE_NUMBER')
    return n
def integer(x):
    n=number(x)
    if n!=int(n) or n<1:raise ValueError('INVALID_INTEGER')
    return int(n)
def text_ok(x):
    if not x or x[0] in '=+@-' or any(ord(c)<32 for c in x):raise ValueError('INVALID_TEXT')
    return x
def parse(text):
    lines=[r.split('\t') for r in normalized(text).splitlines() if r.strip('\t')]
    if any(len(r)!=8 for r in lines):raise ValueError('EXPECTED_EIGHT_COLUMNS')
    if lines[0][:2]!=['M22_REQUEST',engine_id()]:raise ValueError('WRONG_ENGINE_OR_SCHEMA')
    p={};s={};com=[];geo=[];study=None
    for r in lines[1:]:
        tag=r[0]
        if tag=='STUDY':
            if study is not None:raise ValueError('DUPLICATE_STUDY')
            study=text_ok(r[1])
        elif tag=='PARAM':
            if r[1] not in PARAMS or r[1] in p:raise ValueError('INVALID_OR_DUPLICATE_PARAMETER')
            p[r[1]]=number(r[2])
        elif tag=='SECTION':
            if r[1] not in ('column','primary','secondary') or r[1] in s:raise ValueError('INVALID_OR_DUPLICATE_SECTION')
            s[r[1]]=Section(text_ok(r[2]),r[3],number(r[4]),number(r[5]),number(r[6]))
        elif tag=='COMB':
            if r[2] not in FAMILIES:raise ValueError('INVALID_FAMILY')
            com.append(dict(id=text_ok(r[1]),family=r[2],factors=dict(zip(('G_STEEL','G_FLOOR','Q','HX'),map(number,r[3:7])))))
        elif tag=='GEOM':
            if r[5] not in ('SIM','NÃO'):raise ValueError('INVALID_SELECTION')
            geo.append(dict(id=integer(r[1]),nx=integer(r[2]),ny=integer(r[3]),ns=integer(r[4]),selected=r[5]=='SIM'))
        else:raise ValueError('UNKNOWN_RECORD: '+tag)
    if set(p)!=set(PARAMS) or len(s)!=3 or study is None:raise ValueError('MISSING_INPUTS')
    if any(p[k]<=0 for k in PARAMS if k not in ('g_floor_kpa','q_floor_kpa','hx_total_kn')) or min(p['g_floor_kpa'],p['q_floor_kpa'])<0:raise ValueError('INVALID_INPUT_DOMAIN')
    if not 1<=len(com)<=MAX_COMBINATIONS or len({c['id'] for c in com})!=len(com):raise ValueError('INVALID_COMBINATIONS')
    if any(min(c['factors'][k] for k in ('G_STEEL','G_FLOOR','Q'))<0 for c in com):raise ValueError('NEGATIVE_GRAVITY_FACTOR')
    # Bound the generator before enumerating and report resource limits explicitly.
    if any(p[f'{axis}min_mm']>p[f'{axis}max_mm'] for axis in ('x','y','s')):raise ValueError('REVERSED_SPACING_RANGE')
    if p['lx_mm']/p['xmin_mm']>10000 or p['ly_mm']/p['ymin_mm']>10000 or p['lx_mm']/p['smin_mm']>10000:raise ValueError('GEOMETRY_RESOURCE_LIMIT')
    xs=divisions(p['lx_mm'],p['xmin_mm'],p['xmax_mm']);ys=divisions(p['ly_mm'],p['ymin_mm'],p['ymax_mm'])
    if len(xs)>100 or sum(len(divisions(x['spacing'],p['smin_mm'],p['smax_mm']))*len(ys) for x in xs)>1000:raise ValueError('GEOMETRY_TABLE_CAPACITY')
    grid=hypotheses(p['lx_mm'],p['ly_mm'],[p['xmin_mm'],p['xmax_mm']],[p['ymin_mm'],p['ymax_mm']],[p['smin_mm'],p['smax_mm']])['rows']
    if not grid or len(grid)>1000 or len(grid)!=len(geo):raise ValueError('INCOMPLETE_OR_EXCESS_GEOMETRIES')
    for g,h in zip(geo,grid):
        if [g[k] for k in ('id','nx','ny','ns')]!=[h[k] for k in ('id','nx','ny','secondary_intervals_per_x_bay')]:raise ValueError('GEOMETRY_MISMATCH')
    selected=[g for g in geo if g['selected']]
    if not selected:raise ValueError('NO_GEOMETRIES_SELECTED')
    if len(selected)*len(com)>MAX_CASES:raise ValueError(f'MAX_{MAX_CASES}_GEOMETRY_COMBINATION_CASES_SELECT_FEWER')
    if any(3*(g['nx']*g['ns']+g['nx']+2)>600 for g in selected):raise ValueError('MAX_600_DOF_PER_FRAME')
    return dict(parameters=p,sections=s,combinations=com,geometries=geo,study=study)
def solve(text,check_execution=None):
    q=parse(text);p=q['parameters'];s=q['sections'];rows=[];full=[]
    for g in q['geometries']:
        if not g['selected']:continue
        if check_execution:check_execution()
        geom=Geometry(p['lx_mm'],p['ly_mm'],p['height_mm'],g['nx'],g['ny'],g['ns'])
        pattern=np.full((g['ny']+1,g['nx']+1),p['hx_total_kn']/((g['ny']+1)*(g['nx']+1)))
        for co in q['combinations']:
            if check_execution:check_execution()
            factors=co['factors'].copy();direction=1 if factors['HX']>=0 else -1;factors['HX']=abs(factors['HX'])
            r=analyze(geom,s['column'],s['primary'],s['secondary'],p['g_floor_kpa'],p['q_floor_kpa'],factors,lateral_x_kn=pattern*direction,column_denominator=p['column_limit'],primary_denominator=p['primary_limit'],secondary_denominator=p['secondary_limit'],E=p['E_mpa'])
            full.append(dict(hypothesis_id=g['id'],combination=co,result=r))
            for component,key in zip(COMPONENTS,('column_checks','primary_checks','secondary_checks')):
                c=max(r[key],key=lambda z:z['eta'])
                where=','.join(f'{k}={c[k]:.8g}' for k in ('frame','column','bay','line','y_bay','x_mm','y_mm') if k in c)
                rows.append([g['id'],co['id'],co['family'],component,c['signed_displacement_mm'],c['limit_mm'],c['eta'],where,sum(r['mass_subtotal_kg'].values()),r['subtotal_kg_m2'],r['force_balance'],'ZERO_EXPLICITO' if p['hx_total_kn']*co['factors']['HX']==0 else 'HX_UNIFORME_NOS_TOPOS'])
    return rows,full
def export(text,folder):
    text=normalized(text);folder=Path(folder)
    if folder.exists():raise ValueError('OUTPUT_FOLDER_EXISTS')
    rows,full=solve(text)
    digest=hashlib.sha256(text.encode()).hexdigest()
    lines=['\t'.join(['M22_COMPLETE',engine_id(),digest,str(len(rows))]),'\t'.join(COLUMNS)]
    for row in rows:lines.append('\t'.join(format(v,'.15g') if isinstance(v,(int,float)) else v for v in row))
    result='\n'.join(lines)+'\n'
    folder.mkdir(parents=True)
    (folder/'request_echo.tsv').write_text(text,encoding='utf-8')
    (folder/'full_result.json').write_text(json.dumps(dict(schema='M22',engine_id=engine_id(),request_sha256=digest,final_design_approved=False,results=full),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (folder/'result.tsv').write_text(result,encoding='utf-8')
    receipt=dict(schema='M22',engine_id=engine_id(),request_sha256=digest,result_sha256=hashlib.sha256(result.encode()).hexdigest(),rows=len(rows),final_design_approved=False)
    # Receipt is the completion marker, created only after every data file.
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    verify(text,folder)
    return receipt
def verify(text,folder):
    q=parse(text);text=normalized(text);folder=Path(folder)
    receipt=json.loads((folder/'receipt.json').read_text(encoding='utf-8'))
    result=normalized((folder/'result.tsv').read_text(encoding='utf-8'))
    digest=hashlib.sha256(text.encode()).hexdigest()
    if normalized((folder/'request_echo.tsv').read_text(encoding='utf-8'))!=text:raise ValueError('REQUEST_MISMATCH')
    if receipt.get('engine_id')!=engine_id() or receipt.get('request_sha256')!=digest or receipt.get('result_sha256')!=hashlib.sha256(result.encode()).hexdigest() or receipt.get('final_design_approved') is not False:raise ValueError('RECEIPT_MISMATCH')
    lines=result.splitlines();head=lines[0].split('\t')
    expected={(g['id'],c['id'],component) for g in q['geometries'] if g['selected'] for c in q['combinations'] for component in COMPONENTS}
    if head!=['M22_COMPLETE',engine_id(),digest,str(len(expected))] or lines[1].split('\t')!=list(COLUMNS) or len(lines)!=len(expected)+2 or receipt.get('rows')!=len(expected):raise ValueError('RESULT_LAYOUT_MISMATCH')
    seen=set();geoms={g['id']:g for g in q['geometries']};coms={c['id']:c for c in q['combinations']};p=q['parameters'];s=q['sections']
    for line in lines[2:]:
        f=line.split('\t')
        if len(f)!=12:raise ValueError('INCOMPLETE_RESULT_ROW')
        key=(integer(f[0]),f[1],f[3])
        if key not in expected or key in seen or f[2]!=coms[f[1]]['family']:raise ValueError('RESULT_KEY_MISMATCH')
        seen.add(key);g=geoms[key[0]]
        d,limit,eta=map(number,f[4:7]);mass,area_mass,balance=map(number,f[8:11])
        expected_limit={'COLUNA_X':p['height_mm']/p['column_limit'],'PRINCIPAL':p['lx_mm']/g['nx']/p['primary_limit'],'SECUNDARIA':p['ly_mm']/g['ny']/p['secondary_limit']}[key[2]]
        expected_mass=(g['nx']+1)*(g['ny']+1)*p['height_mm']/1000*s['column'].kg_m+(g['ny']+1)*p['lx_mm']/1000*s['primary'].kg_m+(g['nx']*g['ns']+1)*p['ly_mm']/1000*s['secondary'].kg_m
        if limit<=0 or eta<0 or abs(limit-expected_limit)>1e-8*max(1,limit) or abs(eta-abs(d)/limit)>1e-9*max(1,eta):raise ValueError('RESULT_ELS_MISMATCH')
        if abs(mass-expected_mass)>1e-8*expected_mass or abs(area_mass-mass/(p['lx_mm']*p['ly_mm']/1e6))>1e-8*max(1,area_mass) or not 0<=balance<=1e-8:raise ValueError('RESULT_MASS_OR_BALANCE_MISMATCH')
        horizontal='ZERO_EXPLICITO' if p['hx_total_kn']*coms[f[1]]['factors']['HX']==0 else 'HX_UNIFORME_NOS_TOPOS'
        if f[11]!=horizontal:raise ValueError('HORIZONTAL_ACTION_MISMATCH')
    return receipt
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('request');ap.add_argument('output');ap.add_argument('--verify',action='store_true');a=ap.parse_args()
    try:
        text=Path(a.request).read_text(encoding='utf-8-sig')
        result=verify(text,a.output) if a.verify else export(text,a.output)
        print(json.dumps(result))
    except Exception as exc:raise SystemExit(f'M22 INTERROMPIDO: {exc}')
