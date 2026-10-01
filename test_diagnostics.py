import csv
import unittest
import numpy as np
from numpy.polynomial import Polynomial as P
from streamlit.testing.v1 import AppTest
import service
import diagnostics


class DiagnosticsTests(unittest.TestCase):
    def calculate(self,hx=0):
        p,s=service.defaults();p['hx_total_kn']=hx
        co=[dict(id='DEMO_G_Q',family='ELS_RARA',G_STEEL=1,G_FLOOR=1,Q=1,HX=1)]
        return service.calculate(service.request('TESTE',p,s,co,[1]))

    def test_original_results_unchanged(self):
        text=(service.ROOT/'referencia_m22.tsv').read_text()
        rows=service.calculate(text)['rows']
        lines=(service.ROOT/'regression_m22.tsv').read_text().splitlines()
        old=list(csv.DictReader(lines[1:],delimiter='\t'))
        self.assertEqual(len(rows),len(old))
        for a,b in zip(rows,old):
            for k in ('eta','kg_m2','subtotal_kg','limit_mm'):
                self.assertAlmostEqual(a[k],float(b[k]),places=8)
            self.assertAlmostEqual(abs(a['signed_mm']),abs(float(b['signed_mm'])),places=8)

    def test_base_equilibrium_and_foundation_sign(self):
        for hx in (0,10,-10):
            full=self.calculate(hx)['full'];r=full[0]['result'];bases=r['base_reactions']
            self.assertEqual(len(bases),9)
            self.assertEqual(len({b['node'] for b in bases}),9)
            self.assertAlmostEqual(sum(b['Rx_N'] for b in bases),-hx*1000,places=7)
            self.assertAlmostEqual(sum(b['Rz_N'] for b in bases),r['applied_vertical_N'],places=7)
            self.assertLess(r['moment_balance'],1e-8)
            for row in diagnostics.reaction_table(full):
                self.assertEqual(row['Rx apoio→estrutura (kN)'],-row['Fx estrutura→fundação (kN)'])
                self.assertEqual(row['M plano apoio→estrutura (kN·m)'],-row['M plano estrutura→fundação (kN·m)'])

    def test_curves_reproduce_checks(self):
        r=self.calculate(10)['full'][0]['result']
        curves=r['displacement_curves']
        for key in ('primary_checks','secondary_checks','column_checks'):
            for check in r[key]:
                if key=='primary_checks':name=f'VP-{check["frame"]:02d}-{check["bay"]:02d}'
                elif key=='secondary_checks':name=f'VS-{check["y_bay"]:02d}-{check["line"]:02d}'
                else:name=f'C-{check["frame"]:02d}-{check["column"]:02d}'
                pieces=[c for c in curves if c['member']==name]
                data=diagnostics.samples(pieces)
                value=data.iloc[-1]['Deslocamento absoluto (mm)'] if key=='column_checks' else data['Deslocamento absoluto (mm)'].abs().max()
                self.assertAlmostEqual(abs(value),abs(check['signed_displacement_mm']),places=8)

    def test_secondary_analytical_midspan(self):
        r=self.calculate()['full'][0]['result']
        c=next(c for c in r['displacement_curves'] if c['component']=='SECUNDARIA')
        ch=r['secondary_checks'][0];I=r['sections']['secondary']['strong_inertia_mm4'];L=c['end_mm']
        expected=-5*ch['q_N_mm']*L**4/(384*200000*I)
        poly=P(c['relative_coefficients'])
        self.assertAlmostEqual(poly(0),0);self.assertAlmostEqual(poly(1),0)
        self.assertAlmostEqual(poly(.5),expected)

    def test_ui_diagrams(self):
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=40).run()
        at.button(key='calculate').click().run()
        self.assertFalse(at.exception)
        select=next(s for s in at.selectbox if s.label=='Componente do diagrama')
        select.set_value('PRINCIPAL').run();self.assertFalse(at.exception)
        select=next(s for s in at.selectbox if s.label=='Componente do diagrama')
        select.set_value('SECUNDARIA').run();self.assertFalse(at.exception)

if __name__=='__main__':unittest.main()
