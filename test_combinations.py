import json
import unittest
import combinations_adapter as a
import combinations_engine as ce
import service,ultimate,automatic_basis,member_strength,combined_search

class CombinationIntegrationTests(unittest.TestCase):
    def test_ui_automatic_and_family_change(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=45).run()
        self.assertEqual(at.multiselect(key='combo_families').value,['ELUN','ELSF'])
        at.button(key='calculate').click().run()
        at.checkbox(key='elu_confirm').check().run()
        at.button(key='elu_run').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state['elu_result']['full']),8)
        self.assertEqual(at.session_state['elu_result']['combination_provenance']['counts'],{'ELUN':8,'ELSF':2})
        at.multiselect(key='combo_families').set_value(['ELUN','ELSR']).run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Entradas alteradas' in w.value for w in at.warning))
        at.number_input(key='hx_total_kn').set_value(10.).run()
        self.assertFalse(at.exception)
        self.assertFalse(at.button)
        at.selectbox(key='combo_horizontal').set_value('Vento — testar +X e −X').run()
        self.assertFalse(at.exception)
        self.assertTrue(at.button(key='calculate'))

    def test_default_coefficients_and_no_wind(self):
        r=a.generate()
        self.assertEqual(r['counts'],{'ELUN':8,'ELSF':2})
        self.assertEqual({c['Q'] for c in r['els']},{0.,.7})
        self.assertEqual({c['G_STEEL'] for c in r['elu']},{1.,1.25})
        self.assertEqual({c['G_FLOOR'] for c in r['elu']},{1.,1.5})
        self.assertEqual({c['Q'] for c in r['elu']},{0.,1.5})
        self.assertTrue(all(c['HX']==0 for c in r['els']+r['elu']))
        json.dumps(r,allow_nan=False)

    def test_opposite_winds_exclusive_and_signed(self):
        r=a.generate(horizontal='WIND_X')
        self.assertEqual(len(r['elu']),32)
        for c in r['audit']:
            self.assertFalse({4,5}<={i for i,v in c['cases']})
        for family in ('elu','els'):
            coefficients={(c['G_STEEL'],c['G_FLOOR'],c['Q'],c['HX']) for c in r[family]}
            self.assertTrue(any(c[-1]>0 for c in coefficients))
            self.assertTrue(all((*c[:3],-c[3]) in coefficients for c in coefficients))

    def test_families_inputs_and_identity(self):
        r=a.generate(('ELSR','ELSQP'))
        self.assertFalse(r['elu'])
        self.assertEqual({c['family'] for c in r['els']},{'ELS_RARA','ELS_QUASE_PERMANENTE'})
        self.assertNotEqual(a.generate()['signature'],a.generate(occupancy='USO1')['signature'])
        for kw in ({'families':[]},{'families':['ELUX']},{'horizontal':'SISMO'}):
            with self.assertRaises(ValueError):a.generate(**kw)

    def test_wind_runs_all_cases_in_structural_solver(self):
        p,s=service.defaults();p['hx_total_kn']=10
        r=a.generate(horizontal='WIND_X')
        u=ultimate.calculate(p,s,1,r['elu'])
        self.assertEqual(len(u['full']),32)
        e=service.calculate(service.request('AUTO TEST',p,s,r['els'],[1]))
        self.assertEqual(len(e['full']),6)
        self.assertTrue(all(abs(x['result']['force_balance'])<1e-8 for x in u['full']))

    def test_automatic_geometry_lengths_and_pending(self):
        p,s=service.defaults();gs=service.grid(p)
        for g in (gs[0],gs[-1]):
            b=automatic_basis.make(p,s,g['id'])
            self.assertEqual(b['groups'][0]['Lef_x_m'],2*p['height_mm']/1000)
            self.assertEqual(b['groups'][1]['Lef_x_m'],g['x_spacing_mm']/1000)
            self.assertEqual(b['groups'][2]['Lef_x_m'],g['y_spacing_mm']/1000)
            self.assertFalse(b['restraints_validated'])
        u=ultimate.calculate(p,s,1,a.generate()['elu'][:1])
        check=member_strength.evaluate(u,automatic_basis.make(p,s,1),dict(midheight_loads=True,effective_restraints=True))
        self.assertTrue(all(x['pending'] for x in check['rows']))
        self.assertFalse(check['within_implemented_checks'])

    def test_combined_search_recomputes_basis_per_hypothesis(self):
        p,s=service.defaults();r=a.generate();b=automatic_basis.make(p,s,1)
        result=combined_search.run(p,{k:[v] for k,v in s.items()},r['els'],r['elu'],[1,18],b['groups'],dict(midheight_loads=True,effective_restraints=True),basis_policy=automatic_basis.POLICY)
        self.assertEqual(result['cases'],20)
        self.assertIsNone(result['best_conditional_solution'])
        for d in result['details']:
            basis=d['nmv']['basis'];gid=next(x['hypothesis'] for x in result['summaries'] if x['solution']==d['solution'])
            self.assertEqual(basis['groups'],automatic_basis.make(p,s,gid)['groups'])

if __name__=='__main__':unittest.main()
