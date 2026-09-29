import unittest
from pathlib import Path
import service
from streamlit.testing.v1 import AppTest

class ApplicationTests(unittest.TestCase):
    def test_reference_parity(self):
        p,s=service.defaults()
        text=service.request('DEMONSTRAÇÃO',p,s,[dict(id='DEMO_G_Q',family='ELS_RARA',G_STEEL=1,G_FLOOR=1,Q=1,HX=1)],list(range(1,19)))
        self.assertEqual(service.calculate(text)['rows'],service.calculate((service.ROOT/'referencia_m22.tsv').read_text(encoding='utf-8-sig'))['rows'])

    def test_ui_and_stale_results(self):
        at=AppTest.from_file(str(service.ROOT/'app.py'),default_timeout=30).run()
        self.assertFalse(at.exception)
        at.button(key='calculate').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric),3)
        self.assertEqual(at.metric[0].value,'18')
        self.assertEqual(at.metric[2].value,'54')
        at.number_input(key='q_floor_kpa').set_value(2.0).run()
        self.assertFalse(at.exception)
        self.assertFalse(at.metric)
        self.assertTrue(any('Entradas alteradas' in w.value for w in at.warning))
        at.button(key='calculate').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric),3)
        at.number_input(key='xmin_mm').set_value(7.0).run()
        self.assertFalse(at.exception)
        self.assertTrue(at.error)
        self.assertFalse(at.metric)

if __name__=='__main__':
    unittest.main()
