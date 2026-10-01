"""Prismatic Euler-Bernoulli frame with consistent UDL vectors; N/mm/MPa.
Initial-axis geometric stiffness, constant mean axial per FE. Not corotational.
Mesh subdivision required for variable axial forces and second-order accuracy.
"""
import numpy as np
from legacy_frame import transformation,k_material,k_geometric

class SolverFailure(RuntimeError):
    def __init__(self,message,**data):
        super().__init__(message);self.data=data

class Frame:
    def __init__(self,E=200000.):
        if not np.isfinite(E) or E<=0:raise ValueError('Invalid E')
        self.E=E;self.nodes=[];self.members=[];self.fixed=set();self.nodal={}
    def node(self,x,y):
        if not np.all(np.isfinite([x,y])):raise ValueError('Invalid coordinate')
        self.nodes.append((x,y));return len(self.nodes)-1
    def fix(self,n,dofs=(0,1,2)):
        for d in dofs:self.fixed.add(3*n+d)
    def load(self,n,Fx=0.,Fy=0.,M=0.):
        f=np.array([Fx,Fy,M],float)
        if not np.all(np.isfinite(f)):raise ValueError('Invalid nodal load')
        self.nodal[n]=self.nodal.get(n,np.zeros(3))+f
    def member(self,a,b,A,I,q_global=(0.,0.),tag=None):
        if min(A,I)<=0 or not np.all(np.isfinite([A,I,*q_global])):raise ValueError('Invalid member')
        self.members.append((a,b,A,I,q_global,tag));return len(self.members)-1
    def solve(self,second_order=True,reduction=1.,max_iter=100,tol=1e-9):
        if reduction<=0 or not np.isfinite(reduction) or max_iter<1:raise ValueError('Invalid solver controls')
        nd=3*len(self.nodes);free=np.array(sorted(set(range(nd))-self.fixed),dtype=int)
        F=np.zeros(nd);data=[]
        for n,f in self.nodal.items():F[3*n:3*n+3]+=f
        for a,b,A,I,q,tag in self.members:
            delta=np.subtract(self.nodes[b],self.nodes[a]);L=float(np.linalg.norm(delta))
            if L<=0:raise ValueError('Zero length')
            c,s=delta/L;T=transformation(c,s);qx=c*q[0]+s*q[1];qy=-s*q[0]+c*q[1]
            fl=np.array([qx*L/2,qy*L/2,qy*L*L/12,qx*L/2,qy*L/2,-qy*L*L/12])
            dof=np.array([3*a,3*a+1,3*a+2,3*b,3*b+1,3*b+2])
            F[dof]+=T.T@fl
            data.append((dof,T,k_material(self.E,A,I,L,reduction),fl,L,qx,qy,tag))
        axial=np.zeros(len(data));u=np.zeros(nd)
        for iteration in range(1,max_iter+1):
            K=np.zeros((nd,nd));tangents=[]
            for i,(dof,T,km,fl,L,qx,qy,tag) in enumerate(data):
                # Signed compression: negative means tension, which stiffens.
                kg=np.sign(axial[i])*k_geometric(abs(axial[i]),L) if second_order else np.zeros((6,6))
                kt=km-kg;tangents.append(kt);K[np.ix_(dof,dof)]+=T.T@kt@T
            try:
                ff=K[np.ix_(free,free)]
                scale=np.sqrt(np.maximum(np.diag(ff),1e-300));equilibrated=ff/np.outer(scale,scale)
                np.linalg.cholesky(equilibrated)
                unew=np.zeros(nd);unew[free]=np.linalg.solve(equilibrated,F[free]/scale)/scale
                for _ in range(2):unew[free]+=np.linalg.solve(equilibrated,(F[free]-ff@unew[free])/scale)/scale
            except np.linalg.LinAlgError as ex:raise SolverFailure('INSTABILITY_OR_MECHANISM') from ex
            anew=np.array([-.5*((km@(T@unew[dof])-fl)[3]-(km@(T@unew[dof])-fl)[0]) for dof,T,km,fl,L,qx,qy,tag in data])
            du=np.linalg.norm(unew-u)/(1+np.linalg.norm(unew));dp=np.linalg.norm(anew-axial)/(1+np.linalg.norm(anew))
            u=unew
            if not second_order or max(du,dp)<tol:
                reaction=K@u-F
                raw_residual=float(np.linalg.norm(reaction[free])/max(1.,np.linalg.norm(F[free])))
                # Equilibrium norm in force units: divide moment equations by a
                # characteristic member length, avoiding a mixed N/N.mm norm.
                arm=float(np.median([row[4] for row in data]));unit_scale=np.ones(nd);unit_scale[2::3]=arm
                residual=float(np.linalg.norm(reaction[free]/unit_scale[free])/max(1.,np.linalg.norm(F[free]/unit_scale[free])))
                if residual>tol*10:raise SolverFailure('RESIDUAL',relative_residual=residual,limit=tol*10)
                elements=[]
                for i,(dof,T,km,fl,L,qx,qy,tag) in enumerate(data):
                    ul=T@u[dof]
                    elements.append(dict(tag=tag,L=L,qx=qx,qy=qy,local_displacements=ul,
                         material_end_forces=km@ul-fl,generalized_end_forces=tangents[i]@ul-fl,axial_compression=anew[i]))
                return dict(u=u,reactions=reaction,iterations=iteration,residual=residual,elements=elements,
                            second_order=second_order,reduction=reduction,raw_mixed_unit_residual=raw_residual,residual_moment_arm_mm=arm,axial_iteration_change=float(dp))
            axial=anew
        raise SolverFailure('NO_CONVERGENCE')
