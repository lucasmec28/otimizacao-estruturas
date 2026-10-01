"""Conditional strong flexure comparisons. Does not change the ELS search."""
import design_basis
import w_resistance


def evaluate(elu,basis,conditions):
    if not all(conditions.get(k) is True for k in ('midheight_loads','effective_restraints')):
        raise ValueError('Defina altura de aplicação das cargas e contenções eficazes antes da comparação.')
    source=dict(parameters=elu['inputs']['parameters'],profiles=elu['inputs']['profiles'],hypothesis=elu['inputs']['hypothesis'])
    if design_basis.fingerprint(source)!=basis['source_sha256']:
        raise ValueError('Dados de dimensionamento e análise ELU pertencem a entradas diferentes.')
    groups={r['group']:r for r in basis['groups']};rows=[]
    for point in design_basis.extrema(elu['full']):
        if point['action']!='M':continue
        moment=point['M_Nmm']
        # Two rows represent positive and negative envelopes only; skip duplicates
        # when both min and max have the same sign.
        if (point['extreme']=='max' and moment<=0) or (point['extreme']=='min' and moment>=0):continue
        role=design_basis.COMPONENTS[point['component']];g=groups[role]
        sign='positive' if moment>0 else 'negative'
        entry=dict(**point,role=role,sign=sign,profile=basis['source']['profiles'][role],final_design_approved=False)
        try:
            if not isinstance(g['basis'],str) or not g['basis'].strip():raise ValueError('Justificativa de material/travamento pendente.')
            # No segment geometry exists yet to support diagram-dependent Cb.
            if g['Cb_'+sign]!=1.:raise ValueError('Nesta integração por grupo, use Cb=1. Outros valores exigem trechos explícitos ainda não implementados.')
            c=w_resistance.capacity(basis['section_properties'][role],g['Lb_'+sign+'_m']*1000,g['Cb_'+sign],g['fy_MPa'],basis['E_MPa'])
            eta=abs(moment)/c['MRd_Nmm']
            entry.update(status='WITHIN_ISOLATED_FLEXURE' if eta<=1 else 'EXCEEDS_ISOLATED_FLEXURE',eta_M=eta,capacity=c)
        except (ValueError,KeyError,TypeError) as exc:
            entry.update(status='PENDING',reason=str(exc))
        rows.append(entry)
    return dict(schema='M23-PY08-CONDITIONAL-STRONG-FLEXURE',rows=rows,conditions=conditions,
                elu_signature=elu['signature'],basis=basis,final_design_approved=False,
                pending=['N-M interaction','Shear and interaction','Second-order and imperfections','Y stability',
                         'Explicit restraint segments','Independent validation of restraint effectiveness'])
