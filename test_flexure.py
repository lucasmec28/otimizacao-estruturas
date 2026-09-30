import copy
import unittest
from streamlit.testing.v1 import AppTest
import service,ultimate,design_basis,w_resistance,flexure_check

class FlexureTests(unittest.TestCase):
    def setup_case(self):
        p,s=service.defaults();g=design_basis.blank_rows()
        for r in g:r.update(fy_MPa=345.,Lb_positive_m=3.,Lb_negative_m=6.,Cb_positive=1.,Cb_negative=1.,basis='Synthetic inputs')
        basis=design_basis.make(p,s,1,g)
        elu=ultimate.calculate(p,s,1,[dict(id='SYNTHETIC',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)])
        return basis,elu

    def test_cbca_reference_with_documented_discrepancy(self):
        p=copy.deepcopy(next(p for p in service.catalog() if p['Perfil']=='W 410 x 38,8'))
        p.update({'Wx cm³':640.5,'Zx cm³':736.8,'Iy cm⁴':404.,'It cm⁴':11.69,'Cw cm⁶':150000.,'ry cm':2.83})
        r=w_resistance.capacity(p,3000.,1.14,345.,200000.)
        self.assertAlmostEqual(r['lambda_p_FLT'],42.38,delta=.01)
        self.assertAlmostEqual(r['lambda_FLT'],106.01,delta=.01)
        self.assertAlmostEqual(r['limits_Nmm']['FLM']/1e6,231.087,delta=.001)
        self.assertAlmostEqual(r['limits_Nmm']['FLA']/1e6,231.087,delta=.001)
        # Published lambda_r and FLT do not exactly reproduce from printed inputs.
        # Record the mismatch; 1% is a comparison tolerance, not design permission.
        self.assertLess(abs(r['limits_Nmm']['FLT']/1e6-166.015)/166.015,.01)
        self.assertAlmostEqual(r['limits_Nmm']['FLT']/1e6,165.1760856603,places=7)

    def test_branches_and_rejections(self):
        p=next(p for p in service.catalog() if p['Perfil']=='W 410 x 38,8')
        results=[w_resistance.capacity(p,L,1.,345.,200000.) for L in (100.,3000.,20000.)]
        self.assertEqual([x['branch_FLT'] for x in results],['plastic','inelastic','elastic'])
        self.assertGreater(results[0]['MRd_Nmm'],results[1]['MRd_Nmm'])
        self.assertGreater(results[1]['MRd_Nmm'],results[2]['MRd_Nmm'])
        slender=copy.deepcopy(p);slender["d' mm"]=3000
        with self.assertRaises(ValueError):w_resistance.capacity(slender,3000.,1.,345.,200000.)
        for L in (0.,-1.,True,float('nan')):
            with self.assertRaises(ValueError):w_resistance.capacity(p,L,1.,345.,200000.)

    def test_integration_signs_and_no_approval(self):
        b,e=self.setup_case();r=flexure_check.evaluate(e,b,dict(midheight_loads=True,effective_restraints=True))
        self.assertTrue(r['rows']);self.assertFalse(r['final_design_approved'])
        for row in r['rows']:
            self.assertNotEqual(row['status'],'PENDING')
            self.assertEqual(row['capacity']['inputs']['Lb_mm'],3000 if row['sign']=='positive' else 6000)
            self.assertFalse(row['final_design_approved'])
        b['groups'][0]['Cb_positive']=1.2
        r=flexure_check.evaluate(e,b,dict(midheight_loads=True,effective_restraints=True))
        self.assertTrue(any(row['status']=='PENDING' for row in r['rows']))

    def test_conditions_and_stale_basis(self):
        b,e=self.setup_case()
        with self.assertRaises(ValueError):flexure_check.evaluate(e,b,{})
        b['source_sha256']='stale'
        with self.assertRaises(ValueError):flexure_check.evaluate(e,b,dict(midheight_loads=True,effective_restraints=True))

    def test_ui_conditions(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
from test_flexure import FlexureTests
import flexure_ui
b,e=FlexureTests().setup_case()
flexure_ui.show(e,b)
'''
        at=AppTest.from_string(script,default_timeout=30).run()
        self.assertFalse(at.exception);self.assertEqual(len(at.dataframe),0)
        at.checkbox(key='flexure_midheight').check().run()
        at.checkbox(key='flexure_restraints').check().run()
        self.assertFalse(at.exception);self.assertEqual(len(at.dataframe),1)

if __name__=='__main__':unittest.main()
