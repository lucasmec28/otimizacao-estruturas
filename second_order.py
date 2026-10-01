"""Initial-axis geometric stiffness, meshed X frames. Not corotational/3D.
Equilibrium recovery: M=-f2+f1*x+q*x²/2-P*(v(x)-v0), P compression.
Cubic FE v; refinement required. Never reuse first-order moment polynomials.
"""
import copy
import math
import time
from execution_control import ExecutionBudget
import numpy as np
from numpy.polynomial import Polynomial as Poly
import service,ultimate,design_basis
from frame import Frame,SolverFailure
from mezzanine import GRAVITY

DEFAULTS=dict(reduction=.8,notional_ratio=.003,mesh_start=4,mesh_max=16,mesh_tolerance=.01)


def validate(options):
    if set(options)!=set(DEFAULTS):raise ValueError('Controles de segunda ordem incompletos.')
    for k in ('reduction','notional_ratio','mesh_tolerance'):
        v=options[k]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Controle numérico inválido.')
    if not .1<=options['reduction']<=1 or not 0<=options['notional_ratio']<=.01 or not 0<options['mesh_tolerance']<=.05:raise ValueError('Controles fora do intervalo suportado.')
    if options['mesh_start'] not in (2,4,8) or options['mesh_max'] not in (4,8,16) or options['mesh_max']<=options['mesh_start']:raise ValueError('Defina pelo menos dois níveis de malha.')


def recover(frame,result,index):
    a,b,A,I,q,tag=frame.members[index];e=result['elements'][index];L=e['L'];u=e['local_displacements'];f=e['generalized_end_forces']
    P=e['axial_compression'] if result['second_order'] else 0.
    # Cubic transverse displacement, expanded directly without Polynomial objects.
    v1=L*u[2];v2=-3*u[1]-2*L*u[2]+3*u[4]-L*u[5];v3=2*u[1]+L*u[2]-2*u[4]+L*u[5]
    m=[float(-f[2]),float(f[1]*L-P*v1),float(e['qy']*L*L/2-P*v2),float(-P*v3)]
    shear=[m[1]/L,2*m[2]/L,3*m[3]/L]
    return dict(N_coefficients=[float(-f[0]),float(-e['qx']*L)],V_coefficients=shear,M_coefficients=m)



def build(p,profiles,gid,c,frame_index,mesh):
    g=next(x for x in service.grid(p) if x['id']==gid)
    cat={s['Perfil']:s for s in service.catalog()};sec={k:cat[v] for k,v in profiles.items()}
    f=Frame(p['E_mpa']);nodes={};meta=[];bases=[];tops=[]
    def node(x,z):
        key=(round(x,8),round(z,8))
        if key not in nodes:nodes[key]=f.node(x,z)
        return nodes[key]
    def member(a,b,role,name,start,end):
        s=sec[role];f.member(a,b,s['Ag cm²']*100,s['Ix cm⁴']*1e4,(0.,-c['G_STEEL']*s['Massa kg/m']*GRAVITY/1000),name)
        meta.append(dict(member=name,component='COLUNA_X' if role=='column' else 'PRINCIPAL',start_mm=start,end_mm=end))
    span=p['lx_mm']/g['nx'];h=p['height_mm'];j=frame_index
    for k in range(g['nx']+1):
        ids=[node(k*span,h*i/mesh) for i in range(mesh+1)];f.fix(ids[0]);bases.append(ids[0]);tops.append(ids[-1])
        for i,(a,b) in enumerate(zip(ids,ids[1:])):member(a,b,'column',f'C-{j+1:02d}-{k+1:02d}',h*i/mesh,h*(i+1)/mesh)
    ns=g['secondary_intervals_per_x_bay'];splits=max(1,math.ceil(mesh/ns))
    for k in range(g['nx']):
        for interval in range(ns):
            for i in range(splits):
                x0=span*(interval+i/splits)/ns;x1=span*(interval+(i+1)/splits)/ns
                member(node(k*span+x0,h),node(k*span+x1,h),'primary',f'VP-{j+1:02d}-{k+1:02d}',x0,x1)
    sy=p['ly_mm']/g['ny'];dx=span/ns;adj=1 if j in (0,g['ny']) else 2
    for k in range(g['nx']*ns+1):
        width=dx/2 if k in (0,g['nx']*ns) else dx
        q=(c['G_FLOOR']*p['g_floor_kpa']+c['Q']*p['q_floor_kpa'])*width/1000+c['G_STEEL']*sec['secondary']['Massa kg/m']*GRAVITY/1000
        f.load(node(k*dx,h),Fy=-q*sy/2*adj)
    if 3*len(f.nodes)>600:raise ValueError('Malha de segunda ordem excede 600 graus de liberdade por pórtico.')
    return f,meta,bases,tops,g


def magnitudes(pieces):
    result={}
    for pc in pieces:
        m=pc['M_coefficients'];ts=[0.,1.]
        # Same polynomial stationary points as before; coefficients are small arrays.
        roots=np.polynomial.polynomial.polyroots(np.polynomial.polynomial.polyder(m))
        ts.extend(float(complex(r).real) for r in roots if abs(complex(r).imag)<1e-9 and 0<complex(r).real<1)
        result[pc['member']]=max(result.get(pc['member'],0.),max(abs(float(np.polynomial.polynomial.polyval(t,m))) for t in ts))
    return result



def run_mesh(p,profiles,gid,c,options,sign,mesh,check_execution=None,progress=None):
    g=next(x for x in service.grid(p) if x['id']==gid)
    forces=[];reactions=[];drifts=[];notionals=[];iterations=[];residuals=[];reference_moments=[]
    frame_cache={}
    for j in range(g['ny']+1):
        if check_execution:check_execution()
        # Current model has uniform horizontal forces and only edge/interior
        # tributary widths. Reuse only exactly equal frames within this run.
        key=1 if j in (0,g['ny']) else 2
        if key in frame_cache:
            f,template,bases,tops,gravity,first,second,notion=frame_cache[key]
            meta=[dict(pc,member=f"{pc['member'].split('-')[0]}-{j+1:02d}-{pc['member'].split('-')[-1]}") for pc in template]
        else:
            if progress:progress(f'Pórtico {j+1}/{g["ny"]+1} · malha {mesh}')
            f,meta,bases,tops,g=build(p,profiles,gid,c,j,mesh)

            gravity=f.solve(second_order=False,reduction=options['reduction'],check_execution=check_execution)
            rz=[float(gravity['reactions'][3*b+1]) for b in bases]
            if min(rz)<-1e-5:raise ValueError('Reação gravitacional de tração: distribuição nocional requer modelo específico.')
            notion=[sign*options['notional_ratio']*max(v,0.) for v in rz]
            hx=p['hx_total_kn']*c['HX']*1000/((g['nx']+1)*(g['ny']+1))
            for top,noc in zip(tops,notion):f.load(top,Fx=hx+noc)
            first=f.solve(second_order=False,reduction=options['reduction'],check_execution=check_execution)
            second=f.solve(second_order=True,reduction=options['reduction'],check_execution=check_execution)
            frame_cache[key]=(f,meta,bases,tops,gravity,first,second,notion)
        iterations.append(second['iterations']);residuals.append(second['residual'])
        for i,pc in enumerate(meta):
            forces.append(dict(**pc,**recover(f,second,i)))
            reference_moments.append(dict(**pc,**recover(f,first,i)))
        for k,(b,t,noc) in enumerate(zip(bases,tops,notion)):
            d1=float(first['u'][3*t]);d2=float(second['u'][3*t]);ratio=abs(d2/d1) if abs(d1)>1e-6 else None
            drifts.append(dict(member=f'C-{j+1:02d}-{k+1:02d}',first_mm=d1,second_mm=d2,amplification=ratio))
            rx,rz,m=map(float,second['reactions'][3*b:3*b+3])
            reactions.append(dict(node=f'B-{j+1:02d}-{k+1:02d}',top=f'T-{j+1:02d}-{k+1:02d}',frame=j+1,column=k+1,x_mm=k*p['lx_mm']/g['nx'],y_mm=j*p['ly_mm']/g['ny'],z_mm=0.,Rx_N=rx,Rz_N=rz,M_plane_Nmm=m))
            notionals.append(dict(node=f'T-{j+1:02d}-{k+1:02d}',Fx_notional_N=noc))
    return dict(force_diagrams=forces,base_reactions=reactions,drifts=drifts,notionals=notionals,
                iterations=max(iterations),relative_residual=max(residuals),mesh=mesh,
                moment_extrema=magnitudes(forces),first_order_moment_extrema=magnitudes(reference_moments),frames_solved=len(frame_cache),frames_reused=g['ny']+1-len(frame_cache),linear_solver='RCM_CHOLESKY_BANDED')


def signature(p,profiles,gid,combinations,options):
    return design_basis.fingerprint(dict(base=ultimate.signature(p,profiles,gid,combinations),options=options,version='PY13'))


def calculate(p,profiles,gid,combinations,options=None,progress=None,max_seconds=180.,cancelled=None):
    budget=ExecutionBudget(max_seconds,cancelled)
    options=dict(DEFAULTS if options is None else options);validate(options)
    cases=len(combinations)*(2 if options['notional_ratio'] else 1)
    if cases>service.engine.MAX_CASES:raise ValueError(f'{cases} casos ELU excedem {service.engine.MAX_CASES}, contando sentidos nocionais. Nada foi truncado.')
    if progress:progress(dict(done=0,total=cases,elapsed=budget.elapsed,stage='Validando ações e obtendo secundárias'))
    budget.check()
    baseline=ultimate.calculate(p,profiles,gid,combinations) # validates inputs + secondary diagrams/mass
    budget.check()
    full=[];diagnostics=[];done=0
    signs=(-1,1) if options['notional_ratio'] else (1,)
    for c,base in zip(combinations,baseline['full']):
        for sign in signs:
            cid=c['id']+('_NI_MINUS' if sign<0 else '_NI_PLUS') if options['notional_ratio'] else c['id']+'_SO'
            def update(stage):
                budget.check()
                if progress:progress(dict(done=done,total=cases,elapsed=budget.elapsed,stage=stage,combination=cid))
            update('Iniciando combinação')
            n=options['mesh_start'];prev=run_mesh(p,profiles,gid,c,options,sign,n,budget.check,update);history=[]
            while n<options['mesh_max']:
                n*=2;now=run_mesh(p,profiles,gid,c,options,sign,n,budget.check,update)
                moment_error=max(abs(v-prev['moment_extrema'][k])/max(abs(v),1.) for k,v in now['moment_extrema'].items())
                drift_error=max(abs(a['second_mm']-b['second_mm'])/max(abs(a['second_mm']),.001) for a,b in zip(now['drifts'],prev['drifts']))
                history.append(dict(mesh=n,moment_error=moment_error,drift_error=drift_error))
                if max(moment_error,drift_error)<=options['mesh_tolerance']:break
                prev=now
            else:raise SolverFailure('MESH_NOT_CONVERGED',mesh_history=history)
            budget.check()
            result=copy.deepcopy(base['result'])
            result['force_diagrams']=now['force_diagrams']+[pc for pc in base['result']['force_diagrams'] if pc['component']=='SECUNDARIA']
            result['base_reactions']=now['base_reactions'];result['status']='SECOND_ORDER_X_INITIAL_AXIS_CONDITIONAL'
            result.pop('moment_balance',None);result.pop('force_balance',None);result.pop('reactions_XZ_N',None)
            result['generalized_equilibrium_residual']=now['relative_residual']
            result['notional_support_reactions_included']=True
            applied_h=p['hx_total_kn']*c['HX']*1000+sum(x['Fx_notional_N'] for x in now['notionals'])
            rx=sum(x['Rx_N'] for x in now['base_reactions']);rz=sum(x['Rz_N'] for x in now['base_reactions'])
            balance=math.hypot(rx+applied_h,rz-result['applied_vertical_N'])/max(1.,abs(applied_h),abs(result['applied_vertical_N']))
            if balance>1e-8:raise SolverFailure('GLOBAL_FORCE_BALANCE',relative_balance=balance)
            result.update(force_balance=balance,reactions_XZ_N=[rx,rz],applied_horizontal_with_notional_N=applied_h)
            combo=dict(id=cid,family='ELU_MANUAL_SECOND_ORDER_X',factors=copy.deepcopy(base['combination']['factors']),notional_sign=sign)
            full.append(dict(hypothesis_id=gid,combination=combo,result=result))
            diagnostics.append(dict(combination=cid,mesh_history=history,mesh=n,iterations=now['iterations'],
                drifts=now['drifts'],notionals=now['notionals'],relative_residual=now['relative_residual'],
                moment_extrema=now['moment_extrema'],first_order_moment_extrema=now['first_order_moment_extrema'],frames_solved=now['frames_solved'],frames_reused=now['frames_reused']))
            done+=1
            update('Combinação concluída')
    return dict(schema='M23-PY13-SECOND-ORDER-X',signature=signature(p,profiles,gid,combinations,options),
        performance=dict(elapsed_seconds=budget.elapsed,completed_cases=done,total_cases=cases,linear_solver='RCM_CHOLESKY_BANDED',blas_threads=1,time_limit_seconds=max_seconds),engine_id=baseline['engine_id'],inputs=baseline['inputs'],options=options,full=full,diagnostics=diagnostics,
        final_design_approved=False,analysis_model='Initial-axis constant-mean-axial geometric stiffness, small rotations',
        pending=['Y analysis/stability','Actual restraint validity','Local imperfections and full normative applicability',
                 'Load-height effects','Net tension section','Concentrated force effects and torsion','Complete steel mass'])
