"""Exhaustive ELS + conditional first-order N/M/V search; no final approval."""
import itertools
import math
import service,ultimate,design_basis,member_strength,search_profiles
MAX_CASES=200


def signature(p,candidates,els,elu,selected,groups,conditions):
    return design_basis.fingerprint(dict(version='PY09',engine=service.engine.engine_id(),catalog=service.catalog(),
        p=p,candidates=candidates,els=els,elu=elu,selected=selected,groups=groups,conditions=conditions))


def run(p,candidates,els,elu,selected,groups,conditions,progress=None):
    names={r['Perfil'] for r in service.catalog()}
    if set(candidates)!=set(search_profiles.ROLES) or any(not candidates[k] or len(candidates[k])!=len(set(candidates[k])) or any(n not in names for n in candidates[k]) for k in search_profiles.ROLES):
        raise ValueError('Listas de perfis inválidas.')
    valid={g['id'] for g in service.grid(p)}
    if not selected or len(selected)!=len(set(selected)) or not set(selected)<=valid:raise ValueError('Hipóteses inválidas.')
    if not els or not elu:raise ValueError('Informe combinações ELS e ELU.')
    design_basis.validate(groups)
    if not all(conditions.get(k) is True for k in ('midheight_loads','effective_restraints')):raise ValueError('Hipóteses de FLT e contenções pendentes.')
    count=math.prod(len(candidates[k]) for k in search_profiles.ROLES)*len(selected)*(len(els)+len(elu))
    if count>MAX_CASES:raise ValueError(f'{count} casos excedem {MAX_CASES}. Nada foi truncado.')
    # Validate all action inputs before expensive enumeration.
    initial={k:candidates[k][0] for k in search_profiles.ROLES}
    service.request('VALIDATION',p,initial,els,selected)
    summaries=[];details=[];done=0
    total=math.prod(len(candidates[k]) for k in search_profiles.ROLES)*len(selected)
    for nameset in itertools.product(*(candidates[k] for k in search_profiles.ROLES)):
        profiles=dict(zip(search_profiles.ROLES,nameset))
        for gid in selected:
            els_result=service.calculate(service.request('BUSCA CONJUNTA PY09',p,profiles,els,[gid]))
            elu_result=ultimate.calculate(p,profiles,gid,elu)
            basis=design_basis.make(p,profiles,gid,groups)
            nmv=member_strength.evaluate(elu_result,basis,conditions)
            worst_els=max(els_result['rows'],key=lambda r:r['eta'])
            computed=[r for r in nmv['rows'] if 'eta' in r]
            worst_nmv=max(computed,key=lambda r:r['eta']) if computed else None
            pending=sum(bool(r['pending']) for r in nmv['rows'])
            sid=len(summaries)+1
            qualifies=worst_els['eta']<=1 and nmv['within_implemented_checks']
            summaries.append(dict(solution=sid,hypothesis=gid,**profiles,kg_m2=worst_els['kg_m2'],
                subtotal_kg=worst_els['subtotal_kg'],eta_ELS=worst_els['eta'],
                eta_NMV=worst_nmv['eta'] if worst_nmv else None,pending_members=pending,
                within_conditional_scope=qualifies,governing_member=worst_nmv['member'] if worst_nmv else None,
                governing_combination=worst_nmv['combination'] if worst_nmv else None))
            details.append(dict(solution=sid,els_rows=els_result['rows'],nmv=nmv,elu_signature=elu_result['signature']))
            done+=1
            if progress:progress(done,total)
    summaries.sort(key=lambda r:(r['kg_m2'],r['solution']))
    suitable=[r for r in summaries if r['within_conditional_scope']]
    return dict(schema='M23-PY09-CONDITIONAL-SEARCH',signature=signature(p,candidates,els,elu,selected,groups,conditions),
        cases=count,all_requested_cases_completed=True,final_design_approved=False,
        best_conditional_solution=suitable[0]['solution'] if suitable else None,summaries=summaries,details=details,
        inputs=dict(parameters=p,candidates=candidates,els=els,elu=elu,selected=selected,groups=groups,conditions=conditions),
        global_pending=nmv['global_pending'])
