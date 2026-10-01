import unittest
import service
import search_profiles as search
from streamlit.testing.v1 import AppTest

class SearchTests(unittest.TestCase):
    def setUp(self):
        self.p,self.profiles=service.defaults()
        self.c={k:[v] for k,v in self.profiles.items()}
        self.c['secondary'].append('W 150 x 18,0')
        self.com=[dict(id='DEMO_G_Q',family='ELS_RARA',G_STEEL=1,G_FLOOR=1,Q=1,HX=1)]

    def test_search_matches_individual_calculations(self):
        r=search.run('TESTE',self.p,self.c,self.com,[1,13])
        self.assertEqual(r['cases'],4)
        self.assertEqual(len(r['summaries']),4)
        self.assertFalse(r['final_design_approved'])
        for summary in r['summaries']:
            profiles={k:summary[k] for k in search.ROLES}
            manual=service.calculate(service.request('TESTE',self.p,profiles,self.com,[summary['hypothesis']]))
            self.assertEqual(summary['eta'],max(x['eta'] for x in manual['rows']))
            self.assertEqual(summary['subtotal_kg'],manual['rows'][0]['subtotal_kg'])
        ok=[s for s in r['summaries'] if s['passes_partial_els']]
        self.assertEqual(r['best_partial_solution'],ok[0]['solution'] if ok else None)
        a=[s for s in r['summaries'] if s['hypothesis']==1]
        self.assertNotEqual(a[0]['subtotal_kg'],a[1]['subtotal_kg'])

    def test_limits_and_no_feasible(self):
        self.p['primary_limit']=1e8
        r=search.run('TESTE',self.p,self.c,self.com,[1])
        self.assertIsNone(r['best_partial_solution'])
        c={k:[s['Perfil'] for s in service.catalog()][:11] for k in search.ROLES}
        with self.assertRaisesRegex(ValueError,'limitada'):
            search.run('TESTE',self.p,c,self.com,[1])
        c['column']=[]
        with self.assertRaises(ValueError):search.run('TESTE',self.p,c,self.com,[1])

    def test_ui_search_and_invalidation(self):
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=40).run()
        self.assertFalse(at.exception)
        at.multiselect(key='candidates_secondary').set_value(self.c['secondary']).run()
        at.button(key='search').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['search_result']['cases'],72)
        at.number_input(key='q_floor_kpa').set_value(2.0).run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Dados da busca alterados' in w.value for w in at.warning))

if __name__=='__main__':unittest.main()
