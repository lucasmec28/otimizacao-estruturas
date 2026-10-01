import unittest
import copy
import math
import numpy as np
from numpy.polynomial import Polynomial as P
from streamlit.testing.v1 import AppTest
import service,design_basis,ultimate,member_strength as ms,combined_search

class MemberStrengthTests(unittest.TestCase):
    def case(self):
        p,s=service.defaults();groups=design_basis.blank_rows()
        for g in groups:g.update(fy_MPa=345.,G_MPa=77000.,Lef_x_m=3.,Lef_y_m=3.,Lef_t_m=3.,Lb_positive_m=3.,Lb_negative_m=3.,Cb_positive=1.,Cb_negative=1.,basis='Synthetic verification inputs')
        elu=[dict(id='TEST',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]
        return p,s,groups,elu,dict(midheight_loads=True,effective_restraints=True)

    def test_axial_compact_against_euler_and_slender_effective_area(self):
        sec=next(p for p in service.catalog() if p['Perfil']=='W 150 x 13,0')
        _,_,gs,_,_=self.case();g=gs[0]
        r=ms.axial(sec,g,200000.)
        A=1660.;Iy=820000.;ne=math.pi**2*200000*Iy/3000**2
        self.assertAlmostEqual(r['Ne_N']['y'],ne)
        chi=.658**(A*345/ne) if A*345/ne<=2.25 else .877/(A*345/ne)
        self.assertAlmostEqual(r['chi'],chi)
        self.assertAlmostEqual(r['Aeff_mm2'],A)
        self.assertAlmostEqual(r['NcRd_N'],chi*A*345/1.1)
        slender=copy.deepcopy(sec);slender['tf mm']=1.;slender['tw mm']=1.
        reduced=ms.axial(slender,g,200000.)
        self.assertGreater(reduced['Aeff_mm2'],0)
        self.assertLess(reduced['Aeff_mm2'],A)

    def test_shear_branches_and_area(self):
        p={'d mm':400.,'tw mm':10.,"d' mm":350.}
        a=ms.shear(p,345.,200000.)
        self.assertEqual(a['kv'],5.34)
        self.assertAlmostEqual(a['VRd_N'],.6*400*10*345/1.1)
        for factor,branch in [(1.05,'inelastic'),(2.,'elastic')]:
            p["d' mm"]=a['lambda_p']*factor*10
            b=ms.shear(p,345.,200000.)
            self.assertEqual(b['branch'],branch)
        # Aw uses d*tw, not clear web height*tw.
        self.assertEqual(b['Aw_mm2'],4000.)

    def test_interaction_interior_and_branch_boundaries(self):
        pc=dict(start_mm=0.,end_mm=1000.,N_coefficients=[10.,20.],M_coefficients=[0.,80.,-80.],V_coefficients=[5.,-10.])
        r=ms.envelope(pc,100.,100.,100.,100.,10.)
        point=r['eta_NM'];self.assertGreater(point['t'],.5);self.assertLess(point['t'],1.)
        t=np.linspace(0,1,100001);n=P(pc['N_coefficients'])(t)/100;m=np.abs(P(pc['M_coefficients'])(t))/100
        y=np.where(n>=.2,n+8/9*m,n/2+m)
        self.assertAlmostEqual(point['eta_NM'],y.max(),places=8)
        self.assertAlmostEqual(point['N_N'],P(pc['N_coefficients'])(point['t']))
        self.assertAlmostEqual(point['M_Nmm'],P(pc['M_coefficients'])(point['t']))

    def test_reversal_and_discontinuous_limit(self):
        pc=dict(start_mm=0.,end_mm=1000.,N_coefficients=[-40.,80.],M_coefficients=[-20.,40.],V_coefficients=[1.])
        r=ms.envelope(pc,80.,100.,50.,100.,10.)
        self.assertAlmostEqual(r['eta_N']['eta_N'],.5)
        self.assertAlmostEqual(r['eta_M']['eta_M'],.4)
        self.assertAlmostEqual(r['eta_NM']['eta_NM'],.4+8/9*.4)

    def test_tension_remains_pending(self):
        p,s,g,c,conditions=self.case();e=ultimate.calculate(p,s,1,c);b=design_basis.make(p,s,1,g)
        for pc in e['full'][0]['result']['force_diagrams']:pc['N_coefficients']=[1000.]
        r=ms.evaluate(e,b,conditions)
        self.assertFalse(r['within_implemented_checks'])
        self.assertTrue(all(any('Tração' in x for x in row['pending']) for row in r['rows']))
        self.assertFalse(r['final_design_approved'])

    def test_combined_search_parity_limits_and_stale_signature(self):
        p,s,g,c,conditions=self.case();candidates={k:[v] for k,v in s.items()}
        candidates['primary']=['W 250 x 17,9','W 250 x 22,3']
        els=[dict(**c[0],family='ELS_RARA')]
        r=combined_search.run(p,candidates,els,c,[1],g,conditions)
        self.assertEqual(r['cases'],4);self.assertEqual(len(r['summaries']),2)
        self.assertFalse(r['final_design_approved'])
        for item in r['summaries']:
            profiles={k:item[k] for k in s}
            direct=ms.evaluate(ultimate.calculate(p,profiles,1,c),design_basis.make(p,profiles,1,g),conditions)
            self.assertAlmostEqual(item['eta_NMV'],max(x['eta'] for x in direct['rows']))
        with self.assertRaises(ValueError):combined_search.run(p,candidates,els*101,c,[1],g,conditions)
        old=r['signature'];g[0]['Lef_y_m']=4.
        self.assertNotEqual(old,combined_search.signature(p,candidates,els,c,[1],g,conditions))

    def test_nmv_ui(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
from test_member_strength import MemberStrengthTests
import ultimate,design_basis,member_strength_ui
p,s,g,c,conditions=MemberStrengthTests().case()
member_strength_ui.show(ultimate.calculate(p,s,1,c),design_basis.make(p,s,1,g),conditions)
'''
        at=AppTest.from_string(script,default_timeout=30).run()
        self.assertFalse(at.exception);self.assertEqual(len(at.dataframe),1)

    def test_combined_ui_execution_and_invalidation(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
import streamlit as st
from test_member_strength import MemberStrengthTests
import service,ultimate,design_basis,combined_search_ui
p,s,g,c,conditions=MemberStrengthTests().case()
st.session_state.flexure_midheight=True
st.session_state.flexure_restraints=True
p['q_floor_kpa']=st.number_input('Test load',value=p['q_floor_kpa'])
combined_search_ui.show(p,{{k:[v] for k,v in s.items()}},[dict(**c[0],family='ELS_RARA')],[1],design_basis.make(p,s,1,g),ultimate.calculate(p,s,1,c))
'''
        at=AppTest.from_string(script,default_timeout=30).run()
        at.button(key='combined_run').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(at.session_state['combined_result']['all_requested_cases_completed'])
        at.number_input[0].set_value(4.).run()
        self.assertTrue(any('Entradas alteradas' in w.value for w in at.warning))

if __name__=='__main__':unittest.main()
