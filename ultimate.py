"""Explicit ELU action analysis, first order only; never design approval."""
import math
import json
import numpy as np
import service


def signature(p,profiles,gid,combinations):
    return service.fingerprint(json.dumps(dict(parameters=p,profiles=profiles,geometry=gid,combinations=combinations,
        engine=service.engine.engine_id(),version='PY06-ELU-FIRST-ORDER'),sort_keys=True,allow_nan=False))


def calculate(p,profiles,gid,combinations):
    # Reuse geometry/catalog validation without treating ELU as an ELS combination.
    validation=service.request('VALIDAÇÃO DE ENTRADAS',p,profiles,
        [dict(id='VALIDATION_ONLY',family='ELS_RARA',G_STEEL=1,G_FLOOR=1,Q=1,HX=1)],[gid])
    data=service.engine.parse(validation)
    if not 1<=len(combinations)<=service.engine.MAX_CASES:raise ValueError(f'Informe de 1 a {service.engine.MAX_CASES} combinações ELU.')
    seen=set()
    for c in combinations:
        cid=service.engine.text_ok(c['id'])
        if cid in seen:raise ValueError('Identificações ELU repetidas.')
        seen.add(cid)
        for k in ('G_STEEL','G_FLOOR','Q','HX'):
            v=c[k]
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Coeficiente ELU inválido.')
            if k!='HX' and v<0:raise ValueError('Coeficientes gravitacionais devem ser não negativos.')
        if not any(c[k]!=0 for k in ('G_STEEL','G_FLOOR','Q','HX')):raise ValueError('Combinação sem ações.')
    g=next(x for x in data['geometries'] if x['id']==gid)
    geom=service.engine.Geometry(p['lx_mm'],p['ly_mm'],p['height_mm'],g['nx'],g['ny'],g['ns'])
    s=data['sections'];full=[]
    for c in combinations:
        factors={k:c[k] for k in ('G_STEEL','G_FLOOR','Q','HX')}
        direction=-1 if factors['HX']<0 else 1;factors['HX']=abs(factors['HX'])
        pattern=np.full((g['ny']+1,g['nx']+1),direction*p['hx_total_kn']/((g['ny']+1)*(g['nx']+1)))
        r=service.engine.analyze(geom,s['column'],s['primary'],s['secondary'],p['g_floor_kpa'],p['q_floor_kpa'],factors,
            lateral_x_kn=pattern,E=p['E_mpa'])
        # Keep only analysis outputs; ELS checks produced by the legacy routine are discarded.
        keep={k:r[k] for k in ('geometry','sections','base_reactions','force_diagrams','force_balance','moment_balance','mass_subtotal_kg','subtotal_kg_m2','applied_vertical_N','reactions_XZ_N')}
        keep.update(status='ELU_FIRST_ORDER_ACTIONS_ONLY',final_design_approved=False)
        full.append(dict(hypothesis_id=gid,combination=dict(id=c['id'],family='ELU_MANUAL',factors={k:c[k] for k in ('G_STEEL','G_FLOOR','Q','HX')}),result=keep))
    return dict(schema='M23-PY-06-ELU-ANALYSIS',signature=signature(p,profiles,gid,combinations),
        engine_id=service.engine.engine_id(),final_design_approved=False,full=full,
        inputs=dict(parameters=p,profiles=profiles,hypothesis=gid,combinations=combinations),
        pending=['ELU combination normative validation','Resistance and shear checks','Effective restraints','Second-order and imperfections','Y-direction stability','Baseplates and anchors'])
