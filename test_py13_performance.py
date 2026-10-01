import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from numpy.polynomial import Polynomial as P
from streamlit.testing.v1 import AppTest
import service
from frame import Frame,SolverFailure
import second_order,execution_control,combined_search,automatic_basis
from threadpoolctl import threadpool_info

class PY13PerformanceTests(unittest.TestCase):
    def frame(self):
        f=Frame(200000.);cols=[]
        # Inclined top beam, nonuniform axial/lateral nodal actions.
        for x,h in [(0.,3000.),(4000.,3400.),(8000.,3000.)]:
            ns=[f.node(x,h*i/8) for i in range(9)];f.fix(ns[0]);cols.append(ns)
            f.load(ns[-1],Fx=7000.+x,Fy=-60000.-2*x)
            for a,b in zip(ns,ns[1:]):f.member(a,b,2500.,2e7,(0.,-.12))
        for k in range(2):f.member(cols[k][-1],cols[k+1][-1],3300.,5e7,(0.,-.9))
        return f

    def test_banded_vs_dense_reference_both_orders(self):
        f=self.frame()
        for order in (False,True):
            a=f.solve(second_order=order,reduction=.8,linear_solver='dense_reference');b=f.solve(second_order=order,reduction=.8)
            np.testing.assert_allclose(a['u'],b['u'],rtol=1e-8,atol=1e-9)
            np.testing.assert_allclose(a['reactions'],b['reactions'],rtol=1e-8,atol=1e-5)
            for x,y in zip(a['elements'],b['elements']):np.testing.assert_allclose(x['generalized_end_forces'],y['generalized_end_forces'],rtol=1e-8,atol=1e-5)
            self.assertLess(b['bandwidth'],b['free_dofs']-1)

    def test_fast_force_recovery_matches_original_polynomial(self):
        f=self.frame();r=f.solve(second_order=True)
        for i,e in enumerate(r['elements']):
            u=e['local_displacements'];L=e['L'];t=P([0,1]);F=e['generalized_end_forces'];N=e['axial_compression']
            v=u[1]*(1-3*t*t+2*t**3)+L*u[2]*(t-2*t*t+t**3)+u[4]*(3*t*t-2*t**3)+L*u[5]*(-t*t+t**3)
            old=-F[2]+F[1]*L*t+e['qy']*L*L*t*t/2-N*(v-u[1]);new=second_order.recover(f,r,i)
            x=np.linspace(0,1,41)
            np.testing.assert_allclose(old(x),P(new['M_coefficients'])(x),rtol=1e-9,atol=1e-6)
            np.testing.assert_allclose(old.deriv()(x)/L,P(new['V_coefficients'])(x),rtol=1e-9,atol=1e-8)

    def test_equal_frame_reuse_preserves_reactions_names_and_counts(self):
        p,s=service.defaults();c=dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=-1.)
        r=second_order.run_mesh(p,s,1,c,second_order.DEFAULTS,-1,8)
        g=next(x for x in service.grid(p) if x['id']==1)
        self.assertEqual(r['frames_solved'],2)
        self.assertEqual(r['frames_solved']+r['frames_reused'],g['ny']+1)
        self.assertEqual(len(r['base_reactions']),(g['ny']+1)*(g['nx']+1))
        for j in range(g['ny']+1):
            f,meta,bases,tops,_=second_order.build(p,s,1,c,j,8)
            grav=f.solve(second_order=False,reduction=.8)
            notion=[-.003*float(grav['reactions'][3*b+1]) for b in bases]
            hx=p['hx_total_kn']*c['HX']*1000/((g['nx']+1)*(g['ny']+1))
            for t,n in zip(tops,notion):f.load(t,Fx=hx+n)
            independent=f.solve(second_order=True,reduction=.8)
            for k,b in enumerate(bases):
                found=next(x for x in r['base_reactions'] if x['frame']==j+1 and x['column']==k+1)
                np.testing.assert_allclose([found['Rx_N'],found['Rz_N'],found['M_plane_Nmm']],independent['reactions'][3*b:3*b+3],rtol=1e-9,atol=1e-6)
            self.assertTrue(any(x['member'].startswith(f'VP-{j+1:02d}-') for x in r['force_diagrams']))

    def test_progress_completes_and_reports_both_notional_directions(self):
        p,s=service.defaults();c=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)];events=[]
        r=second_order.calculate(p,s,1,c,progress=events.append)
        self.assertEqual(events[-1]['done'],2);self.assertEqual(events[-1]['total'],2)
        self.assertEqual(r['performance']['completed_cases'],2)
        self.assertEqual({x['combination']['notional_sign'] for x in r['full']},{-1,1})
        self.assertTrue(any('malha' in e['stage'] for e in events))

    def test_timeout_and_cancellation_never_return_partial_analysis(self):
        p,s=service.defaults();c=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]
        with self.assertRaises(execution_control.ExecutionLimit):second_order.calculate(p,s,1,c,max_seconds=1e-12)
        flag=[False]
        def progress(e):
            if e['done']==1:flag[0]=True
        with self.assertRaisesRegex(execution_control.ExecutionLimit,'cancelada'):
            second_order.calculate(p,s,1,c,progress=progress,cancelled=lambda:flag[0])

    def test_combined_global_deadline(self):
        p,s=service.defaults();basis=automatic_basis.make(p,s,1);c=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]
        with self.assertRaises(execution_control.ExecutionLimit):
            combined_search.run(p,{k:[v] for k,v in s.items()},[dict(c[0],family='ELS_RARA')],c,[1],basis['groups'],dict(midheight_loads=True,effective_restraints=True),second_order_options=dict(second_order.DEFAULTS),basis_policy=automatic_basis.POLICY,max_seconds=1e-12)

    def test_blas_threads_controlled(self):
        libraries=[x for x in threadpool_info() if x['user_api']=='blas']
        self.assertTrue(libraries)
        self.assertTrue(all(x['num_threads']==1 for x in libraries))

    def test_cache_reuses_complete_result_and_invalidates_changed_input(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
import streamlit as st
import check_cache
x=st.number_input('Input',value=1.,key='x')
def compute():
    st.session_state['computations']=st.session_state.get('computations',0)+1
    return dict(value=x*2)
r=check_cache.get_or_compute('test',dict(x=x),compute)
st.write(r)
'''
        at=AppTest.from_string(script).run();self.assertEqual(at.session_state['computations'],1)
        at.run();self.assertEqual(at.session_state['computations'],1)
        at.number_input(key='x').set_value(2.).run();self.assertEqual(at.session_state['computations'],2)
        self.assertFalse(at.exception)

if __name__=='__main__':unittest.main()
