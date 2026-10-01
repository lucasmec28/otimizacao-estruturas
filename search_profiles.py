"""Exhaustive bounded search. Partial ELS only; no final design approval."""
import itertools
import json
import service

ROLES=('column','primary','secondary')
MAX_CASES=service.engine.MAX_CASES


def signature(study,p,candidates,combinations,selected):
    data=dict(study=study,parameters=p,candidates=candidates,combinations=combinations,
              selected=sorted(selected),engine_id=service.engine.engine_id(),version='M23-PY-12')
    return service.fingerprint(json.dumps(data,sort_keys=True,ensure_ascii=False,allow_nan=False))


def run(study,p,candidates,combinations,selected,progress=None):
    if set(candidates)!=set(ROLES) or any(not candidates[k] for k in ROLES):
        raise ValueError('Selecione ao menos um perfil para cada componente.')
    if any(len(candidates[k])!=len(set(candidates[k])) for k in ROLES):
        raise ValueError('Perfis candidatos duplicados.')
    names={s['Perfil'] for s in service.catalog()}
    if any(n not in names for role in ROLES for n in candidates[role]):
        raise ValueError('Perfil fora do catálogo.')
    geoms=service.grid(p)
    if not selected or not set(selected).issubset({g['id'] for g in geoms}) or len(selected)!=len(set(selected)):
        raise ValueError('Seleção de hipóteses inválida.')
    count=len(selected)*len(combinations)
    for role in ROLES:count*=len(candidates[role])
    if not 1<=count<=MAX_CASES:
        raise ValueError(f'Busca limitada a {MAX_CASES} casos completos. Solicitados: {count}. Reduza hipóteses, combinações ou perfis. Nada foi truncado.')
    summaries=[];details=[]
    sets=list(itertools.product(*(candidates[k] for k in ROLES)))
    for index,nameset in enumerate(sets,1):
        profiles=dict(zip(ROLES,nameset))
        text=service.request(study,p,profiles,combinations,selected)
        result=service.calculate(text)  # includes own weight for each profile tuple
        for gid in selected:
            rows=[r for r in result['rows'] if r['id']==gid]
            governing=max(rows,key=lambda r:r['eta'])
            sid=len(summaries)+1
            summaries.append(dict(solution=sid,hypothesis=gid,**profiles,
                subtotal_kg=governing['subtotal_kg'],kg_m2=governing['kg_m2'],
                eta=governing['eta'],passes_partial_els=governing['eta']<=1,
                governing_component=governing['component'],governing_combination=governing['combination']))
            details.append(dict(solution=sid,rows=rows,request=text,
                request_sha256=result['request_sha256']))
        if progress:progress(index,len(sets))
    summaries.sort(key=lambda r:(r['kg_m2'],r['solution']))
    feasible=[r for r in summaries if r['passes_partial_els']]
    return dict(schema='M23-PY-05-PARTIAL-SEARCH',
        signature=signature(study,p,candidates,combinations,selected),
        engine_id=service.engine.engine_id(),cases=count,profile_sets=len(sets),
        all_requested_cases_completed=True,final_design_approved=False,
        best_partial_solution=feasible[0]['solution'] if feasible else None,
        summaries=summaries,details=details,
        inputs=dict(study=study,parameters=p,candidates=candidates,combinations=combinations,selected=selected))
