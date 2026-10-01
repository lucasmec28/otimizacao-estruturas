import math
import unittest
import numpy as np
from numpy.polynomial import Polynomial
from streamlit.testing.v1 import AppTest
import service,second_order,combined_search,design_basis,ultimate
from frame import Frame,SolverFailure

class SecondOrderTests(unittest.TestCase):
    def cantilever(self,ratio,mesh):
        E=200000.;I=1e8;A=10000.;L=4000.;H=1000.;P=ratio*math.pi**2*E*I/(4*L**2)
        f=Frame(E);ns=[f.node(0,L*i/mesh) for i in range(mesh+1)]
        f.fix(ns[0]);f.load(ns[-1],Fx=H,Fy=-P)
        for a,b in zip(ns,ns[1:]):f.member(a,b,A,I)
        return f,ns,P,E,I,L,H

    def test_independent_beam_column_analytical_solution(self):
        f,nodes,P,E,I,L,H=self.cantilever(.3,16)
        r=f.solve(second_order=True);delta=r['u'][3*nodes[-1]]
        k=math.sqrt(P/(E*I));exact=H/P*(math.tan(k*L)/k-L)
        self.assertLess(abs(delta/exact-1),1e-5)
        self.assertAlmostEqual(r['reactions'][2],H*L+P*delta,delta=.01)
        for i,e in enumerate(r['elements']):
            m=Polynomial(second_order.recover(f,r,i)['M_coefficients'])
            self.assertAlmostEqual(m(0),-e['generalized_end_forces'][2],places=6)
            self.assertAlmostEqual(m(1),e['generalized_end_forces'][5],places=5)
        self.assertAlmostEqual(Polynomial(second_order.recover(f,r,len(f.members)-1)['M_coefficients'])(1),0.,places=5)

    def test_instability_is_failure(self):
        f,*_=self.cantilever(1.2,16)
        with self.assertRaises(SolverFailure):f.solve(second_order=True)

    def test_zero_axial_recovers_first_order(self):
        f,nodes,_,E,I,L,H=self.cantilever(0.,8)
        a=f.solve(second_order=False);b=f.solve(second_order=True)
        np.testing.assert_allclose(a['u'],b['u'],rtol=1e-10,atol=1e-10)
        self.assertAlmostEqual(b['u'][3*nodes[-1]],H*L**3/(3*E*I),places=9)

    def test_real_model_mesh_notional_balance_and_rigidity(self):
        p,s=service.defaults();c=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]
        r=second_order.calculate(p,s,1,c)
        self.assertEqual(len(r['full']),2);self.assertFalse(r['final_design_approved'])
        for case,d in zip(r['full'],r['diagnostics']):
            self.assertLessEqual(max(d['mesh_history'][-1][k] for k in ('moment_error','drift_error')),.01)
            applied=case['result']['applied_vertical_N']
            self.assertAlmostEqual(abs(sum(n['Fx_notional_N'] for n in d['notionals'])),.003*applied,places=6)
            self.assertLess(case['result']['force_balance'],1e-8)
            self.assertTrue(case['result']['notional_support_reactions_included'])
        old=r['signature'];options=dict(second_order.DEFAULTS,reduction=1.)
        self.assertNotEqual(old,second_order.signature(p,s,1,c,options))
        full=second_order.calculate(p,s,1,c,options)
        self.assertGreater(max(abs(x['second_mm']) for x in r['diagnostics'][0]['drifts']),max(abs(x['second_mm']) for x in full['diagnostics'][0]['drifts']))

    def test_mesh_convergence_gate(self):
        p,s=service.defaults();c=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]
        with self.assertRaisesRegex(SolverFailure,'MESH_NOT_CONVERGED'):
            second_order.calculate(p,s,1,c,dict(second_order.DEFAULTS,mesh_start=2,mesh_max=4,mesh_tolerance=1e-12))

    def test_second_order_combined_search(self):
        from test_member_strength import MemberStrengthTests
        p,s,g,c,conditions=MemberStrengthTests().case()
        r=combined_search.run(p,{k:[v] for k,v in s.items()},[dict(**c[0],family='ELS_RARA')],c,[1],g,conditions,second_order_options=dict(second_order.DEFAULTS))
        self.assertEqual(r['cases'],3)
        self.assertEqual(len(r['details'][0]['second_order_diagnostics']),2)
        self.assertEqual(r['details'][0]['nmv']['analysis_schema'],'M23-PY13-SECOND-ORDER-X')
        direct=second_order.calculate(p,s,1,c)
        import member_strength
        check=member_strength.evaluate(direct,design_basis.make(p,s,1,g),conditions)
        self.assertAlmostEqual(r['summaries'][0]['eta_NMV'],max(x['eta'] for x in check['rows']))

    def test_second_order_ui_execution(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
import streamlit as st
import pandas as pd
from unittest.mock import patch
import service,ultimate_ui
p,s=service.defaults()
with patch.object(st,'data_editor',return_value=pd.DataFrame([dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)])):
    ultimate_ui.show(p,s,1)
'''
        at=AppTest.from_string(script,default_timeout=40).run()
        at.selectbox(key='elu_order').set_value('Segunda ordem X com forças nocionais').run()
        at.checkbox(key='elu_confirm').check().run()
        at.button(key='elu_run').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['elu_result']['schema'],'M23-PY13-SECOND-ORDER-X')
        at.number_input(key='so_reduction').set_value(1.).run()
        self.assertTrue(any('Entradas ELU' in w.value for w in at.warning))

if __name__=='__main__':unittest.main()
