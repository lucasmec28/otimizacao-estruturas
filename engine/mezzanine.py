"""M15 partial mezzanine solver, N/mm/MPa. X primary frames; Y pinned secondary.
No diaphragm, weak-axis global analysis, resistance checks or optimization yet.
Project loads are mandatory. Synthetic examples are tests, not project defaults.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import math
import numpy as np
from numpy.polynomial import Polynomial as P
from frame import Frame
from serviceability import element_fields,extrema,check

GRAVITY=9.80665

def positive(**kwargs):
    for name,v in kwargs.items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:raise ValueError('INVALID_'+name)

def divisions(length,minimum,maximum):
    positive(length=length,minimum=minimum,maximum=maximum)
    if minimum>maximum:raise ValueError('REVERSED_SPACING_RANGE')
    L,lo,hi=map(lambda x:Decimal(str(x)),(length,minimum,maximum))
    a=int((L/hi).to_integral_value(rounding=ROUND_CEILING));b=int((L/lo).to_integral_value(rounding=ROUND_FLOOR))
    return [dict(spans=n,spacing=float(L/n)) for n in range(a,b+1)]

def hypotheses(lx,ly,x_range,y_range,secondary_range):
    rows=[]
    for x in divisions(lx,*x_range):
        for y in divisions(ly,*y_range):
            for secondary in divisions(x['spacing'],*secondary_range):
                rows.append(dict(id=len(rows)+1,nx=x['spans'],ny=y['spans'],secondary_intervals_per_x_bay=secondary['spans'],x_spacing_mm=x['spacing'],y_spacing_mm=y['spacing'],secondary_spacing_mm=secondary['spacing'],column_count=(x['spans']+1)*(y['spans']+1),analyze=True,geometry_status='VALID',geometry_code=1))
    return dict(status='VALID' if rows else 'NO_UNIFORM_MODULATION_IN_RANGES',rows=rows)

@dataclass(frozen=True)
class Section:
    name:str
    family:str
    area_mm2:float
    strong_inertia_mm4:float
    kg_m:float
    def __post_init__(self):
        if self.family not in ('W','HP','U'):raise ValueError('SECTION_FAMILY_MUST_BE_W_HP_OR_U')
        positive(area=self.area_mm2,inertia=self.strong_inertia_mm4,mass=self.kg_m)

@dataclass(frozen=True)
class Geometry:
    lx:float
    ly:float
    height:float
    nx:int
    ny:int
    secondary_intervals_per_x_bay:int
    def __post_init__(self):
        positive(lx=self.lx,ly=self.ly,height=self.height)
        for n in (self.nx,self.ny,self.secondary_intervals_per_x_bay):
            if isinstance(n,bool) or not isinstance(n,int) or n<1:raise ValueError('INVALID_GRID_COUNT')
    @property
    def dx(self):return self.lx/(self.nx*self.secondary_intervals_per_x_bay)
    @property
    def secondary_x(self):return np.linspace(0,self.lx,self.nx*self.secondary_intervals_per_x_bay+1)
    @property
    def widths(self):
        a=np.full(len(self.secondary_x),self.dx);a[0]/=2;a[-1]/=2;return a

def analyze(g,column,primary,secondary,g_floor_kpa,q_floor_kpa,factors,
            lateral_x_kn=None,column_denominator=400,primary_denominator=350,
            secondary_denominator=350,E=200000.):
    """One explicit SERVICE combination. Factors are caller supplied, no defaults.
    factors keys: G_STEEL, G_FLOOR, Q, optional HX with explicit nodal pattern.
    Returns first-order service checks, not structural approval.
    """
    positive(E=E,column_denominator=column_denominator,primary_denominator=primary_denominator,secondary_denominator=secondary_denominator)
    for v in (g_floor_kpa,q_floor_kpa):
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0:raise ValueError('FLOOR_ACTIONS_REQUIRED_NONNEGATIVE')
    if set(factors)-{'G_STEEL','G_FLOOR','Q','HX'} or not {'G_STEEL','G_FLOOR','Q'}<=set(factors):raise ValueError('EXPLICIT_SERVICE_FACTORS_REQUIRED')
    if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 for v in factors.values()):raise ValueError('INVALID_FACTORS')
    if 'HX' in factors and lateral_x_kn is None:raise ValueError('HX_PATTERN_REQUIRED')
    lateral=None if lateral_x_kn is None else np.asarray(lateral_x_kn,dtype=float)
    if lateral is not None and (lateral.shape!=(g.ny+1,g.nx+1) or not np.all(np.isfinite(lateral))):raise ValueError('INVALID_LATERAL_PATTERN')
    if lateral is not None and 'HX' not in factors:raise ValueError('HX_FACTOR_REQUIRED')
    steel=factors['G_STEEL'];gf=factors['G_FLOOR'];qf=factors['Q'];sy=g.ly/g.ny
    # kPa * tributary width(m) = kN/m = N/mm. Secondary self-weight is separate.
    qlines=(gf*g_floor_kpa+qf*q_floor_kpa)*g.widths/1000+steel*secondary.kg_m*GRAVITY/1000
    frames=[];solutions=[];tops=[];primary_checks=[];column_checks=[]
    for j in range(g.ny+1):
        f=Frame(E);rowtops=[];columns=[]
        for x in g.secondary_x:rowtops.append(f.node(float(x),g.height))
        for k in range(g.nx+1):
            top=rowtops[k*g.secondary_intervals_per_x_bay];base=f.node(k*g.lx/g.nx,0);f.fix(base)
            f.member(base,top,column.area_mm2,column.strong_inertia_mm4,(0,-steel*column.kg_m*GRAVITY/1000),f'column_{k}')
            columns.append((base,top))
            if lateral is not None:f.load(top,Fx=lateral[j,k]*1000*factors['HX'])
        for k,(a,b) in enumerate(zip(rowtops,rowtops[1:])):
            f.member(a,b,primary.area_mm2,primary.strong_inertia_mm4,(0,-steel*primary.kg_m*GRAVITY/1000),f'primary_{k//g.secondary_intervals_per_x_bay}')
        adjoining=1 if j in (0,g.ny) else 2
        for k,node in enumerate(rowtops):f.load(node,Fy=-float(qlines[k]*sy/2*adjoining))
        r=f.solve(second_order=False,reduction=1.);frames.append(f);solutions.append(r);tops.append(rowtops)
        for k,(base,top) in enumerate(columns):
            value=float(r['u'][3*top]-r['u'][3*base]);column_checks.append(dict(frame=j+1,column=k+1,signed_displacement_mm=value,direction='X',lateral_action_status='SUPPLIED' if lateral is not None else 'NOT_SUPPLIED',**check(value,g.height,column_denominator)))
        for bay in range(g.nx):
            es=[idx for idx,m in enumerate(f.members) if m[-1]==f'primary_{bay}'];span=g.lx/g.nx
            na=rowtops[bay*g.secondary_intervals_per_x_bay];nb=rowtops[(bay+1)*g.secondary_intervals_per_x_bay]
            za=float(r['u'][3*na+1]);zb=float(r['u'][3*nb+1]);absolute=[];relative=[]
            for idx in es:
                a,b,*_=f.members[idx];_,z=element_fields(f,r,idx)
                ta=(f.nodes[a][0]-bay*span)/span;tb=(f.nodes[b][0]-bay*span)/span
                chord=P([za+(zb-za)*ta,(zb-za)*(tb-ta)])
                for target,poly in ((absolute,z),(relative,z-chord)):
                    target.extend(dict(x_mm=f.nodes[a][0]+t*(f.nodes[b][0]-f.nodes[a][0]),signed_displacement_mm=v) for t,v in extrema(poly))
            worst=max(absolute,key=lambda x:abs(x['signed_displacement_mm']));rel=max(relative,key=lambda x:abs(x['signed_displacement_mm']))
            primary_checks.append(dict(frame=j+1,bay=bay+1,reference='INITIAL_GLOBAL_VERTICAL',relative_to_chord=rel,**worst,**check(worst['signed_displacement_mm'],span,primary_denominator)))
    secondary_checks=[]
    t=P([0,1])
    for j in range(g.ny):
        for k,x in enumerate(g.secondary_x):
            za=float(solutions[j]['u'][3*tops[j][k]+1]);zb=float(solutions[j+1]['u'][3*tops[j+1][k]+1]);q=float(qlines[k])
            # Exact pinned UDL deflection + displacements of both supporting primaries.
            relative=-q*sy**4/(24*E*secondary.strong_inertia_mm4)*(t-2*t**3+t**4)
            absolute=P([za,zb-za])+relative
            loc,value=max(extrema(absolute),key=lambda tv:abs(tv[1]));rel=5*abs(q)*sy**4/(384*E*secondary.strong_inertia_mm4)
            secondary_checks.append(dict(line=k+1,y_bay=j+1,x_mm=float(x),y_mm=j*sy+loc*sy,tributary_width_mm=float(g.widths[k]),q_N_mm=q,support_z_mm=[za,zb],relative_deflection_mm=rel,relative_eta=rel/(sy/secondary_denominator),signed_displacement_mm=value,reference='INITIAL_GLOBAL_VERTICAL_INCLUDING_SUPPORT_MOVEMENT',**check(value,sy,secondary_denominator)))
    mass=dict(columns=(g.nx+1)*(g.ny+1)*g.height/1000*column.kg_m,primary_beams=(g.ny+1)*g.lx/1000*primary.kg_m,secondary_beams=len(g.secondary_x)*g.ly/1000*secondary.kg_m)
    weight=steel*sum(mass.values())*GRAVITY+(gf*g_floor_kpa+qf*q_floor_kpa)*g.lx*g.ly/1000
    reactions=np.array([sum(float(sum(r['reactions'][axis::3])) for r in solutions) for axis in (0,1)])
    horizontal=0. if lateral is None else float(lateral.sum())*1000*factors['HX']
    balance=float(np.linalg.norm(reactions+np.array([horizontal,-weight]))/max(1.,weight,abs(horizontal)))
    if balance>1e-8:raise ValueError('GLOBAL_FORCE_BALANCE_FAILED')
    return dict(status='PARTIAL_MEZZANINE_FIRST_ORDER_SERVICE',final_design_approved=False,geometry=g.__dict__,sections=dict(column=column.__dict__,primary=primary.__dict__,secondary=secondary.__dict__),actions=dict(g_floor_kpa=g_floor_kpa,q_floor_kpa=q_floor_kpa,factors=factors,lateral_x_kn=None if lateral is None else lateral.tolist()),limits=dict(column=column_denominator,primary=primary_denominator,secondary=secondary_denominator),primary_checks=primary_checks,secondary_checks=secondary_checks,column_checks=column_checks,mass_subtotal_kg=mass,subtotal_kg_m2=sum(mass.values())/(g.lx*g.ly/1e6),mass_status='EXCLUDES_HORIZONTAL_AND_VERTICAL_BRACING_AND_INTERMEDIATE_COLLECTORS',force_balance=balance,applied_vertical_N=weight,reactions_XZ_N=reactions.tolist(),tributary_area_m2=float(sum(g.widths)*g.ly/1e6),pending=['ELU resistance and stability','Horizontal diaphragm and actual beam restraints','Y global stability and column displacement','Bracing and collector mass','Project actions and service combination selection','Independent rolled U benchmark'])
