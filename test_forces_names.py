import json
import unittest
import numpy as np
from numpy.polynomial import Polynomial as P
from streamlit.testing.v1 import AppTest
import service,diagnostics,grid_names


class ForcesNamesTests(unittest.TestCase):
    def result(self):
        f=json.loads((service.ROOT/'screenshot_case.json').read_text())
        text=service.request('REFERENCIA PRINT',f['parameters'],f['profiles'],f['combinations'],[f['hypothesis']])
        return service.calculate(text)['full'][0]['result']

    def test_names(self):
        self.assertEqual([grid_names.fila(i) for i in (1,26,27,52,53)],['A','Z','AA','AZ','BA'])
        self.assertEqual(grid_names.member('VP-01-02'),'VP-A-2/3')
        self.assertEqual(grid_names.base(2,3),'B3')
        self.assertEqual(grid_names.member('VS-02-03'),'VS-B/C-S3')

    def test_screenshot_shape_and_piece_continuity(self):
        r=self.result();pieces=[p for p in r['displacement_curves'] if p['member']=='VP-01-02']
        data=diagnostics.samples(pieces)
        self.assertAlmostEqual(data['Deslocamento absoluto (mm)'].min(),-.495037917056844,places=9)
        self.assertLess(data['Deslocamento absoluto (mm)'].max(),0)
        self.assertGreater(data['Relativo à corda (mm)'].max(),0)
        for a,b in zip(pieces,pieces[1:]):
            pa=P(a['absolute_coefficients']);pb=P(b['absolute_coefficients'])
            la=a['end_mm']-a['start_mm'];lb=b['end_mm']-b['start_mm']
            for derivative in (0,1,2):
                self.assertAlmostEqual(pa.deriv(derivative)(1)/la**derivative,pb.deriv(derivative)(0)/lb**derivative,places=10)

    def test_moments_match_displacement_curvature(self):
        r=self.result();E=200000.
        for c in r['displacement_curves']:
            forces=next(f for f in r['force_diagrams'] if f['member']==c['member'] and abs(f['start_mm']-c['start_mm'])<1e-6)
            role={'COLUNA_X':'column','PRINCIPAL':'primary','SECUNDARIA':'secondary'}[c['component']]
            I=r['sections'][role]['strong_inertia_mm4'];L=c['end_mm']-c['start_mm']
            factor=-1 if role=='column' else 1
            expected=P(c['absolute_coefficients']).deriv(2)*(factor*E*I/L**2)
            actual=P(forces['M_coefficients'])
            np.testing.assert_allclose(actual(np.linspace(0,1,7)),expected(np.linspace(0,1,7)),rtol=1e-8,atol=1e-5)
            np.testing.assert_allclose(actual.deriv()(np.linspace(0,1,7))/L,P(forces['V_coefficients'])(np.linspace(0,1,7)),rtol=1e-8,atol=1e-5)

    def test_secondary_analytical_moment_and_shear_jump(self):
        r=self.result();c=r['secondary_checks'][0];L=r['geometry']['ly']/r['geometry']['ny'];q=c['q_N_mm']
        f=next(f for f in r['force_diagrams'] if f['member']=='VS-01-01')
        self.assertAlmostEqual(P(f['M_coefficients'])(.5),q*L**2/8)
        self.assertAlmostEqual(P(f['V_coefficients'])(0),q*L/2)
        ff=[f for f in r['force_diagrams'] if f['member']=='VP-01-02']
        internal_q=r['secondary_checks'][1]['q_N_mm']
        for a,b in zip(ff,ff[1:]):
            jump=P(b['V_coefficients'])(0)-P(a['V_coefficients'])(1)
            self.assertAlmostEqual(jump,-internal_q*L/2,places=7)

    def test_force_chart_ui(self):
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=45).run()
        at.button(key='calculate').click().run();self.assertFalse(at.exception)
        for quantity in ('M','V','N'):
            next(s for s in at.selectbox if s.label=='Esforço').set_value(quantity).run()
            self.assertFalse(at.exception)

if __name__=='__main__':unittest.main()
