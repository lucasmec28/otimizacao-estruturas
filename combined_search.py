"""Exhaustive ELS + conditional first-order N/M/V search; no final approval."""
import itertools
import math
from execution_control import ExecutionBudget
import second_order
import automatic_basis
import service,ultimate,design_basis,member_strength,search_profiles
MAX_CASES=service.engine.MAX_CASES


def signature(p,candidates,els,elu,selected,groups,conditions,second_order_options=None,basis_policy=None):
    return design_basis.fingerprint(dict(version='PY13',basis_policy=basis_policy,second_order_options=second_order_options,engine=service.engine.engine_id(),catalog=service.catalog(),
        p=p,candidates=candidates,els=els,elu=elu,selected=selected,groups=groups,conditions=conditions))


def run(p,candidates,els,elu,selected,groups,conditions,progress=None,second_order_options=None,basis_policy=None,max_seconds=300.,phase_progress=None):
    if basis_policy not in (None,automatic_basis.POLICY):raise ValueError('Política de comprimentos desconhecida.')
    names={r['Perfil'] for r in service.catalog()}
    if set(candidates)!=set(search_profiles.ROLES) or any(not candidates[k] or len(candidates[k])!=len(set(candidates[k])) or any(n not in names for n in candidates[k]) for k in search_profiles.ROLES):
        raise ValueError('Listas de perfis inválidas.')
    valid={g['id'] for g in service.grid(p)}
    if not selected or len(selected)!=len(set(selected)) or not set(selected)<=valid:raise ValueError('Hipóteses inválidas.')
    if not els or not elu:raise ValueError('Informe combinações ELS e ELU.')
    design_basis.validate(groups)
    if not all(conditions.get(k) is True for k in ('midheight_loads','effective_restraints')):raise ValueError('Hipóteses de FLT e contenções pendentes.')
    directions=2 if second_order_options and second_order_options['notional_ratio'] else 1
    count=math.prod(len(candidates[k]) for k in search_profiles.ROLES)*len(selected)*(len(els)+directions*len(elu))
    if count>MAX_CASES:raise ValueError(f'{count} casos excedem {MAX_CASES}. Nada foi truncado.')
    # Validate all action inputs before expensive enumeration.
    initial={k:candidates[k][0] for k in search_profiles.ROLES}
    service.request('VALIDATION',p,initial,els,selected)
    budget=ExecutionBudget(max_seconds)
    summaries=[];details=[];done=0
    total=math.prod(len(candidates[k]) for k in search_profiles.ROLES)*len(selected)
    for nameset in itertools.product(*(candidates[k] for k in search_profiles.ROLES)):
        profiles=dict(zip(search_profiles.ROLES,nameset))
        for gid in selected:
            budget.check()
            els_result=service.calculate(service.request('BUSCA CONJUNTA PY13',p,profiles,els,[gid]),check_execution=budget.check)
            elu_result=ultimate.calculate(p,profiles,gid,elu) if second_order_options is None else second_order.calculate(p,profiles,gid,elu,second_order_options,max_seconds=max(1e-6,budget.max_seconds-budget.elapsed),progress=(lambda e:phase_progress(dict(e,solution=done+1,total_solutions=total))) if phase_progress else None)
            basis=automatic_basis.make(p,profiles,gid) if basis_policy==automatic_basis.POLICY else design_basis.make(p,profiles,gid,groups)
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
            details.append(dict(solution=sid,els_rows=els_result['rows'],nmv=nmv,elu_signature=elu_result['signature'],second_order_diagnostics=elu_result.get('diagnostics',[])))
            budget.check()
            done+=1
            if progress:progress(done,total)
    summaries.sort(key=lambda r:(r['kg_m2'],r['solution']))
    suitable=[r for r in summaries if r['within_conditional_scope']]
    return dict(schema='M23-PY13-CONDITIONAL-SEARCH',basis_policy=basis_policy,second_order_options=second_order_options,signature=signature(p,candidates,els,elu,selected,groups,conditions,second_order_options,basis_policy),
        elapsed_seconds=budget.elapsed,time_limit_seconds=max_seconds,cases=count,all_requested_cases_completed=True,final_design_approved=False,
        best_conditional_solution=suitable[0]['solution'] if suitable else None,summaries=summaries,details=details,
        inputs=dict(parameters=p,candidates=candidates,els=els,elu=elu,selected=selected,groups=groups,conditions=conditions),
        global_pending=nmv['global_pending'])
