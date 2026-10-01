"""Design-input checkpoint and exact individual action extrema; no resistance verdict."""
import copy
import hashlib
import json
import math
from numbers import Real
from numpy.polynomial import Polynomial
import service

ROLES = {'column': 'Colunas', 'primary': 'Vigas principais', 'secondary': 'Vigas secundárias'}
COMPONENTS = {'COLUNA_X': 'column', 'PRINCIPAL': 'primary', 'SECUNDARIA': 'secondary'}
FIELDS = ('fy_MPa', 'fu_MPa', 'G_MPa', 'Lef_x_m', 'Lef_y_m', 'Lef_t_m', 'Lb_positive_m', 'Lb_negative_m', 'Cb_positive', 'Cb_negative')


def blank_rows():
    return [dict(group=k, **{f: 0. for f in FIELDS}, basis='') for k in ROLES]


def validate(rows):
    if len(rows) != 3 or {r.get('group') for r in rows} != set(ROLES):
        raise ValueError('Informe exatamente uma linha por grupo: column, primary e secondary.')
    pending = []
    for r in rows:
        label = ROLES[r['group']]
        for f in FIELDS:
            v = r.get(f)
            if isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) or v < 0:
                raise ValueError(f'{label}: {f} deve ser um número finito não negativo.')
            if v == 0:
                pending.append(f'{label}: preencher {f}')
        if r['fy_MPa'] and r['fu_MPa'] and r['fu_MPa'] < r['fy_MPa']:
            raise ValueError(f'{label}: fu não pode ser inferior a fy.')
        if not isinstance(r.get('basis'), str) or not r['basis'].strip():
            pending.append(f'{label}: registrar justificativa dos materiais e travamentos')
    return pending


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False).encode()).hexdigest()


def make(p, profiles, gid, rows):
    # Also validate the selected geometry and sections against the analysis boundary.
    service.request('BASE DE DIMENSIONAMENTO', p, profiles,
                    [dict(id='VALIDATION_ONLY',family='ELS_RARA',G_STEEL=1,G_FLOOR=1,Q=1,HX=1)], [gid])
    geom = next((g for g in service.grid(p) if g['id'] == gid), None)
    if geom is None:
        raise ValueError('Hipótese não encontrada.')
    pending = validate(rows)
    cat = {r['Perfil']: r for r in service.catalog()}
    catalog_selected = {role: cat[name] for role, name in profiles.items()}
    source = dict(parameters=p, profiles=profiles, hypothesis=gid)
    result = dict(schema='M23-PY07-DESIGN-BASIS', source=source, E_MPa=p['E_mpa'],
                  geometry=geom, groups=rows, section_properties=catalog_selected,
                  catalog_sha256=fingerprint(catalog_selected), source_sha256=fingerprint(source),
                  input_status='INCOMPLETE' if pending else 'FILLED_UNVERIFIED',
                  pending_inputs=pending, final_design_approved=False,
                  scope='Input registration only; restraints and material properties require technical validation.',
                  pending_checks=['Material certification', 'Restraint effectiveness and segment layout',
                                  'Normative resistance verification', 'Second-order and imperfections',
                                  'Y-direction stability', 'Shear and interactions'])
    return copy.deepcopy(result)


def extrema(full):
    """Min/max per action per member/case with all three simultaneous resultants.

    Coefficients use t in [0,1]. Keep both sides at element interfaces; a shear
    jump must never be interpolated. These locations do not generally maximize
    an interaction equation; that remains a separate resistance operation.
    """
    out = []
    for case in full:
        grouped = {}
        for index, piece in enumerate(case['result']['force_diagrams']):
            member = piece['member']
            polys = {q: Polynomial(piece[q+'_coefficients']) for q in ('N','V','M')}
            points = {0., 1.}
            for poly in polys.values():
                for root in poly.deriv().roots():
                    if abs(complex(root).imag) < 1e-10 and 0 < float(complex(root).real) < 1:
                        points.add(float(complex(root).real))
            for t in sorted(points):
                grouped.setdefault(member, []).append(dict(
                    member=member, component=piece['component'], piece_index=index,
                    x_mm=piece['start_mm']+t*(piece['end_mm']-piece['start_mm']),
                    t=t, N_N=float(polys['N'](t)), V_N=float(polys['V'](t)), M_Nmm=float(polys['M'](t))))
        for member, candidates in grouped.items():
            for q, key in [('N','N_N'),('V','V_N'),('M','M_Nmm')]:
                for kind, choose in [('min',min),('max',max)]:
                    point = choose(candidates, key=lambda r:r[key])
                    out.append(dict(hypothesis_id=case['hypothesis_id'],
                                    combination=case['combination']['id'], action=q, extreme=kind, **point))
    return out
