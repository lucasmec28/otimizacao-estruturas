# -*- coding: utf-8 -*-
"""
Protótipo consolidado do solver 2D de 2ª ordem usado no desenvolvimento da V4.

Formulação:
- 3 GDL/nó: ux, uy, theta
- viga-coluna Euler-Bernoulli
- matriz geométrica de elemento para esforço axial
- compressão positiva reduz a rigidez tangente
- iteração até convergência dos esforços axiais
- verificação de positividade da matriz tangente
- fator de rigidez EA/EI configurável (ex.: 0,8 em ELU para média deslocabilidade)

Este módulo ainda NÃO está totalmente reintegrado ao arquivo
solver_cobertura_benchmark.py deste checkpoint. Foi preservado separadamente
para não perder a linha de desenvolvimento já validada conceitualmente.
"""

from __future__ import annotations
import math
import numpy as np

def transformation(c, s):
    return np.array([
        [ c, s, 0, 0, 0, 0],
        [-s, c, 0, 0, 0, 0],
        [ 0, 0, 1, 0, 0, 0],
        [ 0, 0, 0, c, s, 0],
        [ 0, 0, 0,-s, c, 0],
        [ 0, 0, 0, 0, 0, 1],
    ], dtype=float)

def k_material(E, A, I, L, reduction=1.0):
    EA = reduction*E*A
    EI = reduction*E*I
    return np.array([
        [ EA/L,          0,           0, -EA/L,          0,           0],
        [    0, 12*EI/L**3,  6*EI/L**2,     0,-12*EI/L**3,  6*EI/L**2],
        [    0,  6*EI/L**2,     4*EI/L,     0, -6*EI/L**2,     2*EI/L],
        [-EA/L,          0,           0,  EA/L,          0,           0],
        [    0,-12*EI/L**3, -6*EI/L**2,     0, 12*EI/L**3, -6*EI/L**2],
        [    0,  6*EI/L**2,     2*EI/L,     0, -6*EI/L**2,     4*EI/L],
    ], dtype=float)

def k_geometric(P_comp, L):
    """
    Matriz geométrica clássica.
    P_comp > 0 para compressão.
    Deve ser SUBTRAÍDA da rigidez material.
    """
    if P_comp <= 0.0:
        return np.zeros((6,6))
    P = P_comp
    return P/(30.0*L)*np.array([
        [0,    0,       0, 0,     0,       0],
        [0,   36,     3*L, 0,   -36,     3*L],
        [0,  3*L, 4*L**2, 0,  -3*L,   -L**2],
        [0,    0,       0, 0,     0,       0],
        [0,  -36,    -3*L, 0,    36,    -3*L],
        [0,  3*L,  -L**2, 0,  -3*L,  4*L**2],
    ], dtype=float)

class Frame2D:
    def __init__(self, E=200000.0):
        self.E = E
        self.nodes = []
        self.elems = []
        self.loads = None
        self.fixed = set()

    def add_node(self, x, y):
        self.nodes.append((float(x),float(y)))
        self.loads = np.zeros(3*len(self.nodes))
        return len(self.nodes)-1

    def add_element(self, n1, n2, A, I):
        self.elems.append((n1,n2,float(A),float(I)))
        return len(self.elems)-1

    def fix(self, node, ux=True, uy=True, rz=True):
        for off,flag in enumerate((ux,uy,rz)):
            if flag: self.fixed.add(3*node+off)

    def add_nodal_load(self, node, Fx=0.0, Fy=0.0, M=0.0):
        self.loads[3*node:3*node+3] += [Fx,Fy,M]

    def _geom(self, elem):
        n1,n2,A,I = elem
        x1,y1 = self.nodes[n1]; x2,y2 = self.nodes[n2]
        dx,dy = x2-x1,y2-y1
        L = math.hypot(dx,dy)
        return L,dx/L,dy/L

    def solve_second_order(self, reduction=1.0, tol=1e-8, max_iter=100):
        nd = 3*len(self.nodes)
        free = np.setdiff1d(np.arange(nd), np.array(sorted(self.fixed), dtype=int))
        u = np.zeros(nd)
        Pcomp = np.zeros(len(self.elems))

        for it in range(max_iter):
            K = np.zeros((nd,nd))
            elem_data = []

            for ie,e in enumerate(self.elems):
                n1,n2,A,I = e
                L,c,s = self._geom(e)
                T = transformation(c,s)
                km = k_material(self.E,A,I,L,reduction)
                kg = k_geometric(Pcomp[ie],L)
                kt = km - kg
                dofs = [3*n1,3*n1+1,3*n1+2,3*n2,3*n2+1,3*n2+2]
                K[np.ix_(dofs,dofs)] += T.T@kt@T
                elem_data.append((dofs,T,km,L))

            Kff = K[np.ix_(free,free)]
            # Falha antes de entrar em ramo pós-crítico.
            try:
                np.linalg.cholesky((Kff+Kff.T)/2.0)
            except np.linalg.LinAlgError:
                raise RuntimeError("INSTABILIDADE ELÁSTICA: matriz tangente não positiva definida.")

            unew = np.zeros(nd)
            unew[free] = np.linalg.solve(Kff, self.loads[free])

            Pnew = np.zeros_like(Pcomp)
            for ie,(dofs,T,km,L) in enumerate(elem_data):
                ul = T@unew[dofs]
                q = km@ul
                # axial local q[0]/q[3]; compressão assumida positiva
                axial_tension_positive = 0.5*(q[3]-q[0])
                Pnew[ie] = max(0.0, -axial_tension_positive)

            du = np.linalg.norm(unew-u)/(1.0+np.linalg.norm(unew))
            dp = np.linalg.norm(Pnew-Pcomp)/(1.0+np.linalg.norm(Pnew))
            u, Pcomp = unew, Pnew
            if max(du,dp) < tol:
                return {"u":u, "Pcomp":Pcomp, "iterations":it+1}

        raise RuntimeError("Não convergiu em max_iter.")

def exact_cantilever_delta(H, P, E, I, L):
    if P <= 1e-12:
        return H*L**3/(3*E*I)
    k = math.sqrt(P/(E*I))
    return H/(P*k)*(math.tan(k*L)-k*L)

def self_test():
    # Coluna engastada com força axial + força horizontal no topo.
    E = 200000.0
    I = 8.0e8
    A = 5000.0
    L = 5000.0
    H = 10_000.0
    Pcr = math.pi**2*E*I/(4*L**2)

    for ratio in (0.2,0.5,0.8):
        P = ratio*Pcr
        # Discretiza em 8 elementos, como no benchmark de desenvolvimento.
        f = Frame2D(E)
        n = [f.add_node(0.0, i*L/8.0) for i in range(9)]
        for a,b in zip(n[:-1],n[1:]):
            f.add_element(a,b,A,I)
        f.fix(n[0])
        f.add_nodal_load(n[-1], Fx=H, Fy=-P)
        r = f.solve_second_order()
        delta_num = r["u"][3*n[-1]]
        delta_ex = exact_cantilever_delta(H,P,E,I,L)
        err = (delta_num/delta_ex-1.0)*100.0
        print(f"P/Pcr={ratio:.1f}: delta_num={delta_num:.6f} mm, delta_ex={delta_ex:.6f} mm, erro={err:.4f}%")

if __name__ == "__main__":
    self_test()
