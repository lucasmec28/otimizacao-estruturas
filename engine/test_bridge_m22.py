import copy, hashlib, json, tempfile, unittest
from pathlib import Path
import bridge_m22 as b

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.lines=[x.split('\t') for x in Path(__file__).parents[1].joinpath('demo_request.tsv').read_text().splitlines()]
        self.lines[0][1]=b.engine_id()
        for r in self.lines:
            if r[0]=='GEOM' and r[1]!='1':r[5]='NÃO'
    def text(self,lines=None):return '\n'.join('\t'.join(r) for r in (self.lines if lines is None else lines))+'\n'
    def param(self,key,value):
        next(r for r in self.lines if r[:2]==['PARAM',key])[2]=str(value)
    def test_blank_and_zero_actions(self):
        self.param('hx_total_kn',0);self.assertEqual(b.parse(self.text())['parameters']['hx_total_kn'],0)
        self.param('hx_total_kn','')
        with self.assertRaisesRegex(ValueError,'INVALID_NUMBER'):b.parse(self.text())
    def test_missing_duplicate_and_altered_geometry(self):
        g=next(r for r in self.lines if r[0]=='GEOM');g[2]='99'
        with self.assertRaisesRegex(ValueError,'GEOMETRY_MISMATCH'):b.parse(self.text())
        self.setUp();self.lines.append(copy.copy(next(r for r in self.lines if r[0]=='COMB')))
        with self.assertRaisesRegex(ValueError,'INVALID_COMBINATIONS'):b.parse(self.text())
        self.setUp();self.lines.pop()
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):b.parse(self.text())
    def test_uniform_horizontal_force_and_superposition(self):
        self.param('hx_total_kn',0);_,zero=b.solve(self.text())
        self.param('hx_total_kn',10);rows,pos=b.solve(self.text())
        self.assertEqual(rows[0][-1],'HX_UNIFORME_NOS_TOPOS')
        self.assertAlmostEqual(pos[0]['result']['reactions_XZ_N'][0],-10000,places=5)
        self.param('hx_total_kn',-10);_,neg=b.solve(self.text())
        for z,p,n in zip(zero[0]['result']['column_checks'],pos[0]['result']['column_checks'],neg[0]['result']['column_checks']):
            self.assertAlmostEqual(p['signed_displacement_mm']+n['signed_displacement_mm'],2*z['signed_displacement_mm'],places=8)
    def test_load_scaling_and_mass_unchanged(self):
        rows,_=b.solve(self.text())
        c=next(r for r in self.lines if r[0]=='COMB');c[3:7]=['2']*4
        twice,_=b.solve(self.text())
        for a,z in zip(rows,twice):
            self.assertAlmostEqual(z[4],2*a[4],places=8);self.assertAlmostEqual(z[6],2*a[6],places=8);self.assertEqual(z[8],a[8])
    def test_atomic_completion_stale_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'result';receipt=b.export(self.text(),out);self.assertEqual(receipt['rows'],3);b.verify(self.text(),out)
            with self.assertRaisesRegex(ValueError,'OUTPUT_FOLDER_EXISTS'):b.export(self.text(),out)
            self.param('q_floor_kpa',2)
            with self.assertRaisesRegex(ValueError,'REQUEST_MISMATCH'):b.verify(self.text(),out)
    def test_corrupted_result_hash_and_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'result';b.export(self.text(),out)
            path=out/'result.tsv';lines=path.read_text().splitlines();fields=lines[2].split('\t');fields[6]='999';lines[2]='\t'.join(fields);bad='\n'.join(lines)+'\n';path.write_text(bad)
            with self.assertRaisesRegex(ValueError,'RECEIPT_MISMATCH'):b.verify(self.text(),out)
            receipt=json.loads((out/'receipt.json').read_text());receipt['result_sha256']=hashlib.sha256(bad.encode()).hexdigest();(out/'receipt.json').write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,'RESULT_ELS_MISMATCH'):b.verify(self.text(),out)
    def test_case_capacity_and_no_selected(self):
        for r in self.lines:
            if r[0]=='GEOM':r[5]='NÃO'
        with self.assertRaisesRegex(ValueError,'NO_GEOMETRIES'):b.parse(self.text())
        for r in self.lines:
            if r[0]=='GEOM':r[5]='SIM'
        c=next(r for r in self.lines if r[0]=='COMB')
        for k in range(11):
            row=c.copy();row[1]=f'EXTRA_{k}';self.lines.append(row)
        with self.assertRaisesRegex(ValueError,'MAX_200'):b.parse(self.text())
    def test_zero_factor_valid_blank_rejected(self):
        c=next(r for r in self.lines if r[0]=='COMB');c[5]='0';b.parse(self.text());c[5]=''
        with self.assertRaisesRegex(ValueError,'INVALID_NUMBER'):b.parse(self.text())
    def test_signed_combination_and_hp(self):
        self.param('hx_total_kn',10);next(r for r in self.lines if r[0]=='COMB')[6]='-1'
        rows,_=b.solve(self.text())
        self.param('hx_total_kn',-10);next(r for r in self.lines if r[0]=='COMB')[6]='1'
        other,_=b.solve(self.text())
        self.assertEqual(rows,other)
        next(r for r in self.lines if r[:2]==['SECTION','column'])[3]='HP'
        self.assertEqual(b.parse(self.text())['sections']['column'].family,'HP')

if __name__=='__main__':unittest.main(verbosity=2)
