"""Rolled doubly symmetric W/HP strong flexure, NBR 8800 Annex D.
Units N, mm, MPa. Conditional on scope and effective restraint; not member approval.
"""
import math
from numbers import Real


def positive(**values):
    for key,value in values.items():
        if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value) or value<=0:
            raise ValueError(f'{key}: informe número finito positivo.')


def capacity(p,Lb,Cb,fy,E,gamma=1.1):
    if p.get('Tipo') not in ('W','HP'):
        raise ValueError('Somente W/HP laminados duplamente simétricos.')
    positive(Lb=Lb,Cb=Cb,fy=fy,E=E,gamma=gamma)
    keys=('Wx cm³','Zx cm³','Iy cm⁴','It cm⁴','Cw cm⁶','ry cm','bf mm','tf mm',"d' mm",'tw mm')
    positive(**{k:p[k] for k in keys})
    W=p['Wx cm³']*1000;Z=p['Zx cm³']*1000;Iy=p['Iy cm⁴']*1e4
    J=p['It cm⁴']*1e4;Cw=p['Cw cm⁶']*1e6;ry=p['ry cm']*10
    mp=min(Z,1.5*W)*fy;mr=.7*fy*W
    beta=mr/(E*J);lp=1.76*math.sqrt(E/fy)
    lr=1.38*Cb*math.sqrt(Iy*J)/(ry*J*beta)*math.sqrt(1+math.sqrt(1+27*Cw*beta**2/(Cb**2*Iy)))
    if lr<=lp:raise ValueError('Intervalo de esbeltez FLT não suportado.')
    lam=Lb/ry
    mcr=Cb*math.pi**2*E*Iy/Lb**2*math.sqrt(Cw/Iy*(1+.039*J*Lb**2/Cw))
    flt=mp if lam<=lp else mp-(mp-mr)*(lam-lp)/(lr-lp) if lam<=lr else mcr
    lf=p['bf mm']/(2*p['tf mm']);fp=.38*math.sqrt(E/fy);fr=.83*math.sqrt(E/(.7*fy))
    flm=mp if lf<=fp else mp-(mp-mr)*(lf-fp)/(fr-fp) if lf<=fr else .69*E*W/lf**2
    lw=p["d' mm"]/p['tw mm'];wp=3.76*math.sqrt(E/fy);wr=5.7*math.sqrt(E/fy)
    if lw>wr:raise ValueError('Alma esbelta: Anexo E ainda não implementado.')
    fla=mp if lw<=wp else mp-(mp-fy*W)*(lw-wp)/(wr-wp)
    limits={k:min(mp,v)/gamma for k,v in [('FLT',flt),('FLM',flm),('FLA',fla)]}
    return dict(MRd_Nmm=min(limits.values()),governing=min(limits,key=limits.get),limits_Nmm=limits,
                lambda_FLT=lam,lambda_p_FLT=lp,lambda_r_FLT=lr,
                branch_FLT='plastic' if lam<=lp else 'inelastic' if lam<=lr else 'elastic',
                lambda_FLM=lf,lambda_p_FLM=fp,lambda_r_FLM=fr,
                lambda_FLA=lw,lambda_p_FLA=wp,lambda_r_FLA=wr,
                inputs=dict(Lb_mm=Lb,Cb=Cb,fy_MPa=fy,E_MPa=E,gamma_a1=gamma),
                source='NBR 8800:2024 D.2.1/D.2.2/Table D.1/D.2.8 a,e,f,h',
                final_design_approved=False)
