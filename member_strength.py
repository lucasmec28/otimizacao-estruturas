"""W/HP axial compression, gross yielding in tension, one-axis shear and N-M.
First-order actions only in this integration; never final structural approval.
"""
import math
from numpy.polynomial import Polynomial as P
import design_basis
from w_resistance import positive,capacity


def axial(p,g,E):
    fy=g['fy_MPa'];G=g['G_MPa'];Lx=g['Lef_x_m']*1000;Ly=g['Lef_y_m']*1000;Lt=g['Lef_t_m']*1000
    positive(fy=fy,G=G,E=E,Lx=Lx,Ly=Ly,Lt=Lt)
    A=p['Ag cm²']*100;Ix=p['Ix cm⁴']*1e4;Iy=p['Iy cm⁴']*1e4;J=p['It cm⁴']*1e4;Cw=p['Cw cm⁶']*1e6
    positive(A=A,Ix=Ix,Iy=Iy,J=J,Cw=Cw)
    ne={'x':math.pi**2*E*Ix/Lx**2,'y':math.pi**2*E*Iy/Ly**2,'torsion':(math.pi**2*E*Cw/Lt**2+G*J)/((Ix+Iy)/A)}
    lam2=A*fy/min(ne.values());chi=.658**lam2 if lam2<=2.25 else .877/lam2
    def effective(b,t,limit,c1,c2):
        if b/t<=limit/math.sqrt(chi):return b
        factor=c2*limit/(b/t*math.sqrt(chi))
        return min(b,b*(1-c1*factor)*factor)
    b=p['bf mm']/2;h=p["d' mm"];tf=p['tf mm'];tw=p['tw mm']
    positive(b=b,h=h,tf=tf,tw=tw)
    bef=effective(b,tf,.56*math.sqrt(E/fy),.22,1.49)
    hef=effective(h,tw,1.49*math.sqrt(E/fy),.18,1.31)
    ae=A-4*(b-bef)*tf-(h-hef)*tw
    if not 0<ae<=A:raise ValueError('Área efetiva inválida.')
    return dict(NcRd_N=chi*ae*fy/1.1,Nt_gross_N=A*fy/1.1,Ne_N=ne,
                buckling_mode=min(ne,key=ne.get),chi=chi,lambda0=math.sqrt(lam2),
                Aeff_mm2=ae,Ag_mm2=A,bef_mm=bef,hef_mm=hef,
                effective_slenderness=max(Lx/math.sqrt(Ix/A),Ly/math.sqrt(Iy/A)))


def shear(p,fy,E):
    positive(fy=fy,E=E,d=p['d mm'],tw=p['tw mm'],h=p["d' mm"])
    lam=p["d' mm"]/p['tw mm'];lp=1.10*math.sqrt(5.34*E/fy);lr=1.37*math.sqrt(5.34*E/fy)
    vpl=.6*p['d mm']*p['tw mm']*fy
    factor=1 if lam<=lp else lp/lam if lam<=lr else 1.24*(lp/lam)**2
    return dict(VRd_N=factor*vpl/1.1,Aw_mm2=p['d mm']*p['tw mm'],kv=5.34,
                slenderness=lam,lambda_p=lp,lambda_r=lr,
                branch='plastic' if lam<=lp else 'inelastic' if lam<=lr else 'elastic')


def roots(poly):
    return [float(complex(r).real) for r in poly.roots() if abs(complex(r).imag)<1e-9 and 0<float(complex(r).real)<1]


def envelope(piece,Nc,Nt,Mpositive,Mnegative,VRd):
    """Exact supremum of piecewise N-M equations, including both branch limits.
    Capacities constant within the element per moment sign; t normalized [0,1].
    """
    positive(Nc=Nc,Nt=Nt,Mpositive=Mpositive,Mnegative=Mnegative,VRd=VRd)
    n=P(piece['N_coefficients']);m=P(piece['M_coefficients']);v=P(piece['V_coefficients'])
    bounds=sorted(set([0.,1.]+roots(n)+roots(m)+roots(n+.2*Nc)+roots(n-.2*Nt)))
    candidates=[]
    for a,b in zip(bounds,bounds[1:]):
        mid=(a+b)/2;nr=Nc if n(mid)<0 else Nt;mr=Mpositive if m(mid)>=0 else Mnegative
        sn=-1 if n(mid)<0 else 1;sm=-1 if m(mid)<0 else 1
        nn=n*(sn/nr);mm=m*(sm/mr)
        high=nn(mid)>=.2
        interaction=nn+8/9*mm if high else nn/2+mm
        points=set([a,b]+[r for poly in (interaction,nn,mm,v) for r in roots(poly.deriv()) if a<r<b])
        for t in points:
            candidates.append(dict(t=t,x_mm=piece['start_mm']+t*(piece['end_mm']-piece['start_mm']),
                N_N=float(n(t)),M_Nmm=float(m(t)),V_N=float(v(t)),
                eta_N=float(nn(t)),eta_M=float(mm(t)),eta_V=abs(float(v(t)))/VRd,
                eta_NM=float(interaction(t)),interaction_branch='N/NRd>=0.2' if high else 'N/NRd<0.2',
                interval=[a,b]))
    return {key:max(candidates,key=lambda x:x[key]) for key in ('eta_N','eta_M','eta_V','eta_NM')}


def evaluate(elu,basis,conditions):
    if not all(conditions.get(k) is True for k in ('midheight_loads','effective_restraints')):
        raise ValueError('Condições de aplicação das cargas e contenções pendentes.')
    src=dict(parameters=elu['inputs']['parameters'],profiles=elu['inputs']['profiles'],hypothesis=elu['inputs']['hypothesis'])
    if design_basis.fingerprint(src)!=basis['source_sha256']:raise ValueError('Base de dimensionamento desatualizada.')
    rows=[];groups={g['group']:g for g in basis['groups']}
    for case in elu['full']:
        members={}
        for i,piece in enumerate(case['result']['force_diagrams']):members.setdefault(piece['member'],[]).append((i,piece))
        for member,pieces in members.items():
            role=design_basis.COMPONENTS[pieces[0][1]['component']];g=groups[role];p=basis['section_properties'][role];E=basis['E_MPa']
            entry=dict(member=member,role=role,combination=case['combination']['id'],profile=p['Perfil'],pending=[],final_design_approved=False)
            try:
                positive(fy=g['fy_MPa'])
                if not g['basis'].strip():raise ValueError('Justificativa de materiais e travamentos pendente.')
                if g['Cb_positive']!=1 or g['Cb_negative']!=1:raise ValueError('Cb diferente de 1 exige trechos explícitos.')
                mp=capacity(p,g['Lb_positive_m']*1000,1,g['fy_MPa'],E)
                mn=capacity(p,g['Lb_negative_m']*1000,1,g['fy_MPa'],E)
                vc=shear(p,g['fy_MPa'],E)
                # N is linear in this engine. Both ends detect compression/tension.
                low=min(P(pc['N_coefficients'])(t) for _,pc in pieces for t in (0.,1.))
                high=max(P(pc['N_coefficients'])(t) for _,pc in pieces for t in (0.,1.))
                nt=p['Ag cm²']*100*g['fy_MPa']/1.1
                ac=axial(p,g,E) if low < -1e-6 else None
                nc=ac['NcRd_N'] if ac else nt
                if high>1e-6:entry['pending'].append('Tração: ruptura da seção líquida efetiva não verificada; apenas escoamento bruto.')
                found=[]
                for index,pc in pieces:
                    for key,point in envelope(pc,nc,nt,mp['MRd_Nmm'],mn['MRd_Nmm'],vc['VRd_N']).items():
                        found.append(dict(check=key,piece_index=index,**point))
                governing={key:max((r for r in found if r['check']==key),key=lambda r:r[key]) for key in ('eta_N','eta_M','eta_V','eta_NM')}
                worst=max(governing.values(),key=lambda r:r[r['check']])
                eta=worst[worst['check']]
                if ac and ac['effective_slenderness']>200:
                    entry['pending'].append('Lef/r > 200: revisão da recomendação de esbeltez e dos comprimentos geométricos necessária.')
                entry.update(eta=eta,governing=worst,checks=governing,
                    capacities=dict(axial=ac,Nt_gross_N=nt,positive=mp,negative=mn,shear=vc),
                    status='EXCEEDS_IMPLEMENTED_CHECKS' if eta>1 else 'PENDING' if entry['pending'] else 'WITHIN_CONDITIONAL_FIRST_ORDER_CHECKS')
            except (ValueError,KeyError,TypeError) as exc:
                entry['pending'].append(str(exc));entry['status']='PENDING'
            rows.append(entry)
    complete=all(r['status']=='WITHIN_CONDITIONAL_FIRST_ORDER_CHECKS' for r in rows) and bool(rows)
    return dict(schema='M23-PY09-NMV-CONDITIONAL',rows=rows,within_implemented_checks=complete,
                final_design_approved=False,elu_signature=elu['signature'],basis=basis,conditions=conditions,
                global_pending=['Second-order and imperfections','Y-direction analysis/stability','Actual restraint validation',
                    'Torsion/warping and local concentrated forces','Normative load combination validation',
                    'Complete steel mass including bracing/collectors'])
