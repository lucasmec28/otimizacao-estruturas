import copy
import unittest
import numpy as np
from numpy.polynomial import Polynomial
from streamlit.testing.v1 import AppTest
import service, ultimate, design_basis

class DesignBasisTests(unittest.TestCase):
    def test_draft_and_filled_remain_unapproved(self):
        p,s=service.defaults(); rows=design_basis.blank_rows()
        a=design_basis.make(p,s,1,rows)
        self.assertEqual(a['input_status'],'INCOMPLETE')
        self.assertEqual(len(a['pending_inputs']),33)
        for row in rows:
            row.update({f:1. for f in design_basis.FIELDS})
            row.update(fy_MPa=345.,fu_MPa=450.,G_MPa=77000.,basis='Synthetic test, no project endorsement')
        b=design_basis.make(p,s,1,rows)
        self.assertEqual(b['input_status'],'FILLED_UNVERIFIED')
        self.assertFalse(b['final_design_approved'])
        self.assertEqual(b['E_MPa'],p['E_mpa'])
        rows[0]['fy_MPa']=999.
        self.assertEqual(b['groups'][0]['fy_MPa'],345.)
        changed=copy.deepcopy(p); changed['E_mpa']=190000.
        self.assertNotEqual(a['source_sha256'],design_basis.make(changed,s,1,design_basis.blank_rows())['source_sha256'])

    def test_invalid_inputs(self):
        for v in (-1.,float('nan'),True,'345'):
            rows=design_basis.blank_rows();rows[0]['fy_MPa']=v
            with self.assertRaises(ValueError):design_basis.validate(rows)
        rows=design_basis.blank_rows();rows[0].update(fy_MPa=345.,fu_MPa=300.)
        with self.assertRaises(ValueError):design_basis.validate(rows)
        with self.assertRaises(ValueError):design_basis.validate([rows[0]]*3)

    def test_extrema_interior_simultaneity_and_jump(self):
        # First piece M=10t-10t² has its maximum at t=.5, with N=3, V=0.
        pieces=[dict(member='VP-01-01',component='PRINCIPAL',start_mm=0,end_mm=1000,
                     N_coefficients=[2,2],V_coefficients=[.01,-.02],M_coefficients=[0,10,-10]),
                dict(member='VP-01-01',component='PRINCIPAL',start_mm=1000,end_mm=2000,
                     N_coefficients=[4,0],V_coefficients=[-.03,0],M_coefficients=[0,-30])]
        case=dict(hypothesis_id=1,combination={'id':'TEST'},result={'force_diagrams':pieces})
        rows=design_basis.extrema([case])
        maximum=next(r for r in rows if r['action']=='M' and r['extreme']=='max')
        self.assertEqual(maximum['x_mm'],500.)
        self.assertEqual((maximum['N_N'],maximum['V_N'],maximum['M_Nmm']),(3.,0.,2.5))
        minimum=next(r for r in rows if r['action']=='V' and r['extreme']=='min')
        self.assertEqual((minimum['x_mm'],minimum['piece_index'],minimum['t']),(1000.,1,0.))
        self.assertEqual(minimum['M_Nmm'],0.)

    def test_real_model_extrema_bound_dense_samples(self):
        p,s=service.defaults()
        a=ultimate.calculate(p,s,1,[dict(id='SYNTHETIC',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)])
        rows=design_basis.extrema(a['full'])
        pieces=a['full'][0]['result']['force_diagrams']
        for row in rows:
            q=row['action'];key={'N':'N_N','V':'V_N','M':'M_Nmm'}[q]
            values=np.concatenate([Polynomial(piece[q+'_coefficients'])(np.linspace(0,1,501)) for piece in pieces if piece['member']==row['member']])
            if row['extreme']=='min':self.assertLessEqual(row[key],values.min()+1e-7)
            else:self.assertGreaterEqual(row[key],values.max()-1e-7)
            piece=pieces[row['piece_index']]
            for other,k in [('N','N_N'),('V','V_N'),('M','M_Nmm')]:
                self.assertAlmostEqual(row[k],Polynomial(piece[other+'_coefficients'])(row['t']))

    def test_ui_basis_and_demand_table(self):
        script=f'''import sys
sys.path.insert(0,{str(service.ROOT)!r})
import service,ultimate,design_basis_ui
p,s=service.defaults()
design_basis_ui.show(p,s,1)
r=ultimate.calculate(p,s,1,[dict(id='SYNTHETIC',G_STEEL=1.,G_FLOOR=1.,Q=1.,HX=1.)])
design_basis_ui.show_demands(r)
'''
        at=AppTest.from_string(script,default_timeout=30).run()
        self.assertFalse(at.exception)
        at.radio(key='basis_mode').set_value('Manual avançado').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('33 campos pendentes' in x.value for x in at.info))
        at.selectbox(key='demand_member').set_value(at.selectbox(key='demand_member').options[-1]).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.dataframe[-1].value),6)

if __name__=='__main__':unittest.main()
