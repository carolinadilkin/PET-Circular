"""Testes de comparação responsável e persistência de versões v0.4."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from comparison_v04 import compare_reports,parse_report,validate_report
from pet_circular.engine import assess
from ui_helpers import fingerprint,fresh,import_case,upsert_fact
import storage

ROOT=Path(__file__).resolve().parents[1]
A=json.loads((ROOT/'examples/integrated/Design_A_Resultado_Esperado.json').read_text(encoding='utf-8'))
B=json.loads((ROOT/'examples/integrated/Design_B_Resultado_Esperado.json').read_text(encoding='utf-8'))

class TestComparison(unittest.TestCase):
    def test_synthetic_counts_exact(self):
        comparison=compare_reports(A,B)
        self.assertEqual(comparison['counts']['criterio_favoravel'],2)
        self.assertEqual(comparison['counts']['ainda_pendente'],1)
        self.assertEqual(comparison['counts']['pendencia_persistente'],3)
        self.assertEqual(len(comparison['changes']),15)
        self.assertEqual(comparison['global_classification'],'NAO_EMITIDA')
    def test_pvc_label_is_not_marked_resolved(self):
        by_id={x['rule_id']:x for x in compare_reports(A,B)['changes']}
        self.assertEqual(by_id['PET-05']['category'],'ainda_pendente')
        self.assertEqual(by_id['PET-05']['status_b'],'INCONCLUSIVO')
    def test_two_compatibility_transitions(self):
        r=compare_reports(A,B)
        changed={x['rule_id'] for x in r['changes'] if x['category']=='criterio_favoravel'}
        self.assertEqual(changed,{'PET-09','PET-18'})
    def test_comparison_does_not_mutate_inputs(self):
        a,b=copy.deepcopy(A),copy.deepcopy(B)
        compare_reports(a,b)
        self.assertEqual((a,b),(A,B))
    def test_matrix_mismatch_flagged(self):
        other=copy.deepcopy(B);other['matrix_version']='0.0.0'
        self.assertTrue(any('matriz' in w for w in compare_reports(A,other)['warnings']))
    def test_scope_mismatch_flagged(self):
        other=copy.deepcopy(B);other['scope']='FORA'
        self.assertTrue(any('escopo' in w for w in compare_reports(A,other)['warnings']))
    def test_cannot_compare_identical_report(self):
        with self.assertRaisesRegex(ValueError,'idênticos'):compare_reports(A,copy.deepcopy(A))
    def test_reject_input_as_report(self):
        body=(ROOT/'examples/integrated/Design_A_Entrada.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'não é um relatório'):parse_report(body)
    def test_reject_missing_rule(self):
        other=copy.deepcopy(A);other['results'].pop()
        with self.assertRaisesRegex(ValueError,'15 critérios'):validate_report(other)
    def test_reject_duplicate_rule(self):
        other=copy.deepcopy(A);other['results'][0]['rule_id']=other['results'][1]['rule_id']
        with self.assertRaisesRegex(ValueError,'duplicados'):validate_report(other)
    def test_report_upload_roundtrip(self):
        body=json.dumps(B,ensure_ascii=False).encode('utf-8')
        self.assertEqual(parse_report(body),B)
    def test_reports_saved_in_historical_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'db.sqlite3'
            p=import_case((ROOT/'examples/integrated/Design_A_Entrada.json').read_bytes())
            a_id=storage.save(p,assess(p),path=path)
            q=import_case((ROOT/'examples/integrated/Design_B_Entrada.json').read_bytes())
            b_id=storage.save(q,assess(q),path=path)
            records=storage.history(path=path)
            self.assertEqual(len(records),2)
            self.assertEqual(records[0]['id'],b_id)
            self.assertEqual({t['id'] for t,r in storage.report_history(path=path)},{a_id,b_id})
            self.assertEqual(compare_reports(*reversed([storage.load(a_id,path)[1], storage.load(b_id,path)[1]]))['counts']['novo_problema'],2)
    def test_changes_invalidate_fingerprint(self):
        p=fresh()
        current=fingerprint(p)
        new=upsert_fact(p,'material_corpo','PET')
        self.assertNotEqual(current,fingerprint(new))
        self.assertEqual(p['facts'],[])

if __name__=='__main__':unittest.main()
