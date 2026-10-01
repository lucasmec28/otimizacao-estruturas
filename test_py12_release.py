import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import service,search_profiles,combined_search,combinations_adapter,automatic_basis,release_check,second_order

class PY12Tests(unittest.TestCase):
    def test_native_capacity_1000_and_1001_rejected(self):
        p,s=service.defaults()
        base=dict(family='ELS_FREQUENTE',G_STEEL=1.,G_FLOOR=1.,Q=.7,HX=0.)
        c=[dict(base,id=f'CASE_{i}') for i in range(1000)]
        text=service.request('CAPACITY',p,s,c,[9])
        self.assertEqual(len(service.engine.parse(text)['combinations']),1000)
        with self.assertRaisesRegex(ValueError,'MAX_1000'):
            service.request('CAPACITY',p,s,c[:501],[9,18])
        with self.assertRaisesRegex(ValueError,'INVALID_COMBINATIONS'):
            service.request('CAPACITY',p,s,c+[dict(base,id='EXTRA')],[9])
        self.assertEqual(service.engine.MAX_CASES,search_profiles.MAX_CASES)
        self.assertEqual(service.engine.MAX_CASES,combined_search.MAX_CASES)

    def test_real_288_cases_preserve_all_families(self):
        p,s=service.defaults();p['hx_total_kn']=5.
        c=combinations_adapter.generate(['ELUN','ELSR','ELSF','ELSQP'],horizontal='WIND_X')['els']
        result=service.calculate(service.request('OVER OLD CAP',p,s,c,list(range(1,19))))
        self.assertEqual(len(result['full']),288)
        self.assertEqual(len(result['rows']),864)
        self.assertEqual({x['family'] for x in result['rows']},{'ELS_RARA','ELS_FREQUENTE','ELS_QUASE_PERMANENTE'})
        self.assertTrue(all(abs(x['balance'])<1e-8 for x in result['rows']))

    def test_one_extra_profile_with_wind_runs_216_cases(self):
        p,s=service.defaults();p['hx_total_kn']=5.
        c=combinations_adapter.generate(horizontal='WIND_X')['els']
        candidates={k:[v] for k,v in s.items()};candidates['secondary'].append('W 150 x 18,0')
        result=search_profiles.run('USER SCENARIO',p,candidates,c,list(range(1,19)))
        self.assertEqual(result['cases'],216)
        self.assertEqual(len(result['summaries']),36)
        self.assertTrue(result['all_requested_cases_completed'])

    def test_combined_search_228_cases_and_over_limit_guard(self):
        p,s=service.defaults();p['hx_total_kn']=5.
        c=combinations_adapter.generate(horizontal='WIND_X')
        candidates={k:[v] for k,v in s.items()};candidates['secondary'].append('W 150 x 18,0')
        groups=automatic_basis.make(p,s,9)['groups'];conditions=dict(midheight_loads=True,effective_restraints=True)
        r=combined_search.run(p,candidates,c['els'],c['elu'],[9,13,18],groups,conditions,basis_policy=automatic_basis.POLICY)
        self.assertEqual(r['cases'],228)
        self.assertEqual(len(r['summaries']),6)
        self.assertTrue(r['all_requested_cases_completed'])
        self.assertFalse(r['final_design_approved'])
        with self.assertRaisesRegex(ValueError,'1368 casos excedem 1000'):
            combined_search.run(p,candidates,c['els'],c['elu'],list(range(1,19)),groups,conditions,basis_policy=automatic_basis.POLICY)
        with self.assertRaisesRegex(ValueError,'1002 casos ELU excedem 1000'):
            second_order.calculate(p,s,9,[dict(c['elu'][0],id=f'C_{i}') for i in range(501)])

    def test_mixed_and_missing_files_stop_before_importing_ui(self):
        self.assertEqual(release_check.problems(service.ROOT,'M23-PY-12'),[])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'app';shutil.copytree(service.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            (root/'ultimate_ui.py').write_text('def show(p,profiles,gid,basis=None):\n    pass\n')
            problems=release_check.problems(root,'M23-PY-12')
            self.assertTrue(any('ultimate_ui.py' in x for x in problems))
            at=AppTest.from_file(str(root/'app.py')).run()
            self.assertFalse(at.exception)
            self.assertTrue(any('Atualização incompleta' in x.value for x in at.error))
            self.assertFalse(at.number_input)
            (root/'release_manifest.json').unlink()
            self.assertTrue(any('release_manifest' in x for x in release_check.problems(root,'M23-PY-12')))

    def test_user_geometry_automatic_default_and_elu_no_typeerror(self):
        # Reproduce supplied characteristic actions, profiles and geometry 9.
        p,s=service.defaults();p.update(q_floor_kpa=5.,hx_total_kn=5.)
        s.update(column='W 150 x 13,0',primary='W 250 x 17,9',secondary='W 150 x 13,0')
        with patch.object(service,'defaults',return_value=(p,s)):
            at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=45).run()
            at.selectbox(key='combo_horizontal').set_value('Vento — testar +X e −X').run()
            selection=next(x for x in at.multiselect if x.label=='Hipóteses a calcular')
            selection.set_value([9]).run()
            at.button(key='calculate').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.radio(key='basis_mode').value,'Automáticos pela concepção')
            self.assertFalse(at.get('data_editor'))
            at.checkbox(key='elu_confirm').check().run()
            at.button(key='elu_run').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.session_state['elu_result']['full']),32)
            self.assertFalse(any('campos pendentes' in x.value for x in at.info))
            self.assertFalse(at.session_state['elu_result']['final_design_approved'])

if __name__=='__main__':unittest.main()
