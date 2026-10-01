"""SPD band solve with structural reordering; no change to stiffness equations."""
import numpy as np
from scipy.linalg import cholesky_banded,cho_solve_banded
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import reverse_cuthill_mckee

class BandPlan:
    def __init__(self,nd,free,element_dofs):
        free=np.asarray(free,dtype=int)
        if not len(free):raise ValueError('No free degrees of freedom')
        rows=[];cols=[]
        for dofs in element_dofs:
            rows.extend(np.repeat(dofs,len(dofs)));cols.extend(np.tile(dofs,len(dofs)))
        graph=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(nd,nd)).tocsr()
        reduced=graph[free][:,free]
        perm=reverse_cuthill_mckee(reduced,symmetric_mode=True)
        self.order=free[perm]
        graph=reduced[perm][:,perm].toarray()!=0
        self.rows,self.cols=np.where(np.tril(graph))
        self.bandwidth=int(max(self.rows-self.cols,default=0))
        self.free_dofs=len(free)

    def factor(self,K):
        ff=K[np.ix_(self.order,self.order)]
        diag=np.diag(ff)
        if not np.all(np.isfinite(ff)) or np.any(diag<=0):raise np.linalg.LinAlgError('Nonpositive or nonfinite stiffness')
        scale=np.sqrt(diag)
        band=np.zeros((self.bandwidth+1,self.free_dofs))
        band[self.rows-self.cols,self.cols]=ff[self.rows,self.cols]/(scale[self.rows]*scale[self.cols])
        ch=cholesky_banded(band,lower=True,check_finite=True)
        return BandFactor(ch,scale,ff)

class BandFactor:
    def __init__(self,ch,scale,ff):self.ch=ch;self.scale=scale;self.ff=ff
    def solve(self,rhs):
        return cho_solve_banded((self.ch,True),rhs/self.scale,check_finite=True)/self.scale
    def refined(self,rhs):
        x=self.solve(rhs)
        for _ in range(2):x+=self.solve(rhs-self.ff@x)
        return x
