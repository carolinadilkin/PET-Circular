"""Cenários A/B sintéticos: regras e documentos, não ensaios físicos."""
import json
import unittest
from pathlib import Path

from pet_circular.engine import assess
from document_ai import local_candidates,read_pdf_bytes
from ui_helpers import import_case

BASE=Path(__file__).resolve().parents[1]/'examples/integrated'

class TestIntegratedDesigns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs={n:import_case((BASE/f'Design_{n}_Entrada.json').read_bytes()) for n in ('A','B')}
        cls.actuals={n:assess(p) for n,p in cls.inputs.items()}
        cls.expected={n:json.loads((BASE/f'Design_{n}_Resultado_Esperado.json').read_text(encoding='utf-8')) for n in ('A','B')}
    def test_fixture_a_matches_expected(self):self.assertEqual(self.actuals['A'],self.expected['A'])
    def test_fixture_b_matches_expected(self):self.assertEqual(self.actuals['B'],self.expected['B'])
    def test_design_a_has_three_incompatibilities(self):
        self.assertEqual(set(self.actuals['A']['summary']['incompatibilities_confirmed']),{'PET-05','PET-09','PET-18'})
    def test_design_b_preserves_inconclusive_label_and_coverage(self):
        rules={r['rule_id']:r['status'] for r in self.actuals['B']['results']}
        self.assertEqual(rules['PET-05'],'INCONCLUSIVO')
        self.assertEqual(rules['PET-04'],'INCONCLUSIVO')
        self.assertEqual(rules['PET-09'],'COMPATIVEL')
        self.assertEqual(rules['PET-18'],'COMPATIVEL')
    def test_global_class_not_emitted_for_both(self):
        for n in ('A','B'):
            self.assertEqual(self.actuals[n]['global_recyclability_class'],'NAO_EMITIDA')
            self.assertFalse(self.actuals[n]['official_certification'])
    def test_local_pdf_extracts_core_facts(self):
        for n in ('A','B'):
            p=BASE/f'Ficha_Sintetica_Design_{n}.pdf'
            doc=read_pdf_bytes(p.read_bytes(),p.name)
            self.assertTrue(doc.pages)
            keys={x['key'] for x in local_candidates(doc)}
            for key in ('material_corpo','transparencia_corpo','cor_corpo','capacidade_ml','polimero_rotulo'):
                self.assertIn(key,keys)
