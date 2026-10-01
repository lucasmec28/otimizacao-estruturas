"""Python application boundary. Frozen M22 engine retained for traceability."""
from pathlib import Path
import hashlib
import json
import math
import sys
from decimal import Decimal

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
import bridge_m22 as engine


def catalog():
    return json.loads((ROOT / 'catalogo.json').read_text(encoding='utf-8'))


def defaults():
    q = engine.parse((ROOT / 'referencia_m22.tsv').read_text(encoding='utf-8-sig'))
    return q['parameters'], {k: v.name for k, v in q['sections'].items()}


def grid(p):
    for k in engine.PARAMS:
        v = p[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('Informe números finitos em todos os campos.')
        if k not in ('g_floor_kpa', 'q_floor_kpa', 'hx_total_kn') and v <= 0:
            raise ValueError('Dimensões, módulo de elasticidade e denominadores devem ser positivos.')
    if min(p['g_floor_kpa'], p['q_floor_kpa']) < 0:
        raise ValueError('As ações verticais devem ser não negativas.')
    for axis in ('x', 'y', 's'):
        if p[f'{axis}min_mm'] > p[f'{axis}max_mm']:
            raise ValueError('Espaçamento mínimo superior ao máximo.')
    if max(p['lx_mm']/p['xmin_mm'], p['ly_mm']/p['ymin_mm'], p['lx_mm']/p['smin_mm']) > 10000:
        raise ValueError('Intervalos excedem a capacidade desta versão.')
    xs = engine.divisions(p['lx_mm'], p['xmin_mm'], p['xmax_mm'])
    ys = engine.divisions(p['ly_mm'], p['ymin_mm'], p['ymax_mm'])
    if len(xs) > 100 or sum(len(engine.divisions(x['spacing'], p['smin_mm'], p['smax_mm']))*len(ys) for x in xs) > 1000:
        raise ValueError('Máximo de 1.000 hipóteses e 100 modulações X.')
    return engine.hypotheses(p['lx_mm'], p['ly_mm'], [p['xmin_mm'], p['xmax_mm']], [p['ymin_mm'], p['ymax_mm']], [p['smin_mm'], p['smax_mm']])['rows']


def request(study, p, profiles, combinations, selected):
    def row(*values):
        return '\t'.join([str(v) for v in values] + ['']*(8-len(values)))
    lines = [row('M22_REQUEST', engine.engine_id()), row('STUDY', engine.text_ok(study))]
    lines += [row('PARAM', k, p[k]) for k in engine.PARAMS]
    cat = {s['Perfil']: s for s in catalog()}
    for role, name in profiles.items():
        s = cat[name]
        lines.append(row('SECTION', role, name, s['Tipo'], Decimal(str(s['Ag cm²']))*100, Decimal(str(s['Ix cm⁴']))*10000, s['Massa kg/m']))
    for c in combinations:
        lines.append(row('COMB', engine.text_ok(c['id']), c['family'], *(c[k] for k in ('G_STEEL','G_FLOOR','Q','HX'))))
    for g in grid(p):
        lines.append(row('GEOM', g['id'], g['nx'], g['ny'], g['secondary_intervals_per_x_bay'], 'SIM' if g['id'] in selected else 'NÃO'))
    text = '\n'.join(lines)+'\n'
    engine.parse(text)
    return text


def fingerprint(text):
    return hashlib.sha256(engine.normalized(text).encode()).hexdigest()


def calculate(text,check_execution=None):
    rows, full = engine.solve(text,check_execution=check_execution)
    if any(not 0 <= r[10] <= 1e-8 for r in rows):
        raise ValueError('Falha no equilíbrio de forças. Resultados não liberados.')
    return dict(schema='M23-PY-05', application_version='M23-PY-13', engine_id=engine.engine_id(), request_sha256=fingerprint(text),
                final_design_approved=False, rows=[dict(zip(engine.COLUMNS, r)) for r in rows],
                full=full, request=text)
