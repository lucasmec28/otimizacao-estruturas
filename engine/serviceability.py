"""User-defined displacement criteria. N/mm. First-order frame recovery only."""
import json, math
from pathlib import Path
import numpy as np
from numpy.polynomial import Polynomial as P
KEYS=('roof_column_horizontal','roof_beam_vertical','purlin_down','purlin_up','mezzanine_column_horizontal','mezzanine_floor_beam_vertical')
def settings(path=None):
    d=json.loads(Path(path or Path(__file__).with_name('serviceability.json')).read_text())
    for k in KEYS:
        if not isinstance(d.get(k),(int,float)) or isinstance(d[k],bool) or not math.isfinite(d[k]) or d[k]<=0:raise ValueError('Invalid denominator: '+k)
    families=d.get("service_families")
    if not isinstance(families,list) or not families or any(f not in ("ELS_RARA","ELS_FREQUENTE","ELS_QUASE_PERMANENTE") for f in families) or len(set(families))!=len(families):raise ValueError("Invalid service families")
    return d

def check(displacement,length,denominator):
    if not all(math.isfinite(x) for x in (displacement,length,denominator)) or min(length,denominator)<=0:raise ValueError('Invalid displacement check')
    limit=length/denominator
    return dict(displacement_mm=abs(displacement),reference_length_mm=length,denominator=denominator,limit_mm=limit,eta=abs(displacement)/limit,status='PASS_PARTIAL' if abs(displacement)<=limit else 'FAIL_PARTIAL')

def extrema(poly):
    roots=poly.deriv().roots()
    ts=[0.,1.]+[float(r.real) for r in roots if abs(r.imag)<1e-9 and 0<r.real<1]
    return [(t,float(poly(t))) for t in ts]

def element_fields(frame,result,index):
    if result['second_order']:raise ValueError('Exact first-order recovery cannot be used for second-order fields')
    a,b,A,I,q,tag=frame.members[index];e=result['elements'][index];L=e['L']
    c,s=(np.array(frame.nodes[b])-frame.nodes[a])/L
    u0,v0,r0,u1,v1,r1=e['local_displacements'];E=frame.E*result['reduction']
    t=P([0,1]);one=P([1]);u=u0*(one-t)+u1*t+e['qx']*L*L/(2*E*A)*t*(one-t)
    v=v0*(one-3*t*t+2*t**3)+L*r0*(t-2*t*t+t**3)+v1*(3*t*t-2*t**3)+L*r1*(-t*t+t**3)+e['qy']*L**4/(24*E*I)*t*t*(one-t)**2
    return c*u-s*v,s*u+c*v

def roof_result(frame,result,limits):
    indices=[i for i,m in enumerate(frame.members) if m[-1]=='beam']
    length=sum(result['elements'][i]['L'] for i in indices)
    candidates=[]
    for i in indices:
        a,b,*_=frame.members[i];_,z=element_fields(frame,result,i)
        for t,d in extrema(z):
            xyz=np.array(frame.nodes[a])+t*(np.array(frame.nodes[b])-frame.nodes[a])
            candidates.append(dict(element=i,t=t,x_mm=float(xyz[0]),z_mm=float(xyz[1]),signed_vertical_mm=d))
    worst=max(candidates,key=lambda c:abs(c['signed_vertical_mm']))
    return worst|check(worst['signed_vertical_mm'],length,limits['roof_beam_vertical'])

def column_results(frame,result,limits):
    rows=[]
    tags=sorted({m[-1] for m in frame.members if str(m[-1]).startswith('column_')})
    for tag in tags:
        ids={n for m in frame.members if m[-1]==tag for n in m[:2]}
        top=max(ids,key=lambda n:frame.nodes[n][1]);base=min(ids,key=lambda n:frame.nodes[n][1]);H=frame.nodes[top][1]-frame.nodes[base][1]
        dx=float(result['u'][3*top]-result['u'][3*base])
        rows.append(dict(tag=tag,direction='X_TRANSVERSE',signed_horizontal_mm=dx,longitudinal_status='NOT_ANALYZED')|check(dx,H,limits['roof_column_horizontal']))
    return rows
