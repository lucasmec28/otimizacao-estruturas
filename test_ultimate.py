import unittest
import copy
import service,ultimate
from streamlit.testing.v1 import AppTest


class UltimateTests(unittest.TestCase):
    def setUp(self):
        self.p,self.s=service.defaults()
        self.c=[dict(id='SYNTHETIC',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)]

    def test_scale_and_scope(self):
        a=ultimate.calculate(self.p,self.s,1,self.c)
        c=[dict(id='DOUBLE',G_STEEL=2.,G_FLOOR=2.,Q=2.,HX=2.)]
        b=ultimate.calculate(self.p,self.s,1,c)
        ar=a['full'][0]['result'];br=b['full'][0]['result']
        self.assertFalse(a['final_design_approved'])
        self.assertNotIn('column_checks',ar)
        self.assertEqual(ar['subtotal_kg_m2'],br['subtotal_kg_m2'])
        for x,y in zip(ar['base_reactions'],br['base_reactions']):
            for key in ('Rx_N','Rz_N','M_plane_Nmm'):self.assertAlmostEqual(2*x[key],y[key],places=6)
        for x,y in zip(ar['force_diagrams'],br['force_diagrams']):
            for key in ('N_coefficients','V_coefficients','M_coefficients'):
                for u,v in zip(x[key],y[key]):self.assertAlmostEqual(2*u,v,places=5)

    def test_signed_horizontal_and_els_limits_independent(self):
        self.p['hx_total_kn']=10
        self.c[0]['HX']=-2.
        r=ultimate.calculate(self.p,self.s,1,self.c)
        self.assertAlmostEqual(sum(b['Rx_N'] for b in r['full'][0]['result']['base_reactions']),20000,places=7)
        p=copy.deepcopy(self.p);p['column_limit']=1000
        s=ultimate.calculate(p,self.s,1,self.c)
        self.assertEqual(r['full'],s['full'])

    def test_invalid_coefficients(self):
        for value in (float('nan'),-1.,True):
            c=copy.deepcopy(self.c);c[0]['Q']=value
            with self.assertRaises(ValueError):ultimate.calculate(self.p,self.s,1,c)
        c=[dict(id='EMPTY',G_STEEL=0.,G_FLOOR=0.,Q=0.,HX=0.)]
        with self.assertRaises(ValueError):ultimate.calculate(self.p,self.s,1,c)

    def test_ui_requires_explicit_input(self):
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=45).run()
        at.button(key='calculate').click().run();self.assertFalse(at.exception)
        self.assertTrue(at.button(key='elu_run').disabled)
        at.checkbox(key='elu_confirm').check().run()
        at.button(key='elu_run').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('sem ações' in e.value for e in at.error))

    def test_successful_ui_render(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
import streamlit as st
import pandas as pd
import service,ultimate_ui
from unittest.mock import patch
p,s=service.defaults()
with patch.object(st,"data_editor",return_value=pd.DataFrame([dict(id="SYNTHETIC",G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)])):
    ultimate_ui.show(p,s,1)
'''
        at=AppTest.from_string(script,default_timeout=40).run()
        at.checkbox(key='elu_confirm').check().run()
        at.button(key='elu_run').click().run()
        self.assertFalse(at.exception)
        self.assertFalse(at.session_state['elu_result']['final_design_approved'])
        self.assertTrue(any(s.label=='Esforço ELU' for s in at.selectbox))

if __name__=='__main__':unittest.main()
