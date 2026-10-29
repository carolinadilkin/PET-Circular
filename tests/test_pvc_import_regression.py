"""Regressão do teste A/B realizado em 29/10/2026.

Dados são sintéticos e NÃO constituem documentação de produto real.
"""
import json
import unittest
from pathlib import Path
from ui_helpers import fresh, import_case
from pet_circular.engine import assess
from ecodesign_assistant import offline_answer

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / 'examples' / 'teste_rotulo_pvc_input.json'

class TestPvcImportRegression(unittest.TestCase):
    def test_synthetic_input_imported_and_assessed(self):
        case = import_case(SCENARIO.read_bytes())
        self.assertEqual(case['product_id'], 'SYN-PET-PVC-LABEL-001')
        self.assertEqual(len(case['facts']), 6)
        self.assertEqual(next(c['presence'] for c in case['components'] if c['kind']=='rotulo'), 'SIM')
        report = assess(case)
        rules = {r['rule_id']: r for r in report['results']}
        self.assertEqual(report['scope'], 'DENTRO')
        self.assertEqual(rules['PET-01']['status'],'COMPATIVEL')
        self.assertEqual(rules['PET-05']['status'],'NAO_COMPATIVEL')
        self.assertIn('PET-05',report['summary']['incompatibilities_confirmed'])
        self.assertNotIn('densidade_rotulo',rules['PET-05']['missing'])
        self.assertEqual(report['global_recyclability_class'],'NAO_EMITIDA')

    def test_blank_product_does_not_masquerade_as_imported(self):
        blank = fresh()
        self.assertEqual(blank['product_id'],'novo-produto')
        report=assess(blank)
        rules={r['rule_id']:r for r in report['results']}
        self.assertEqual(report['scope'],'INDETERMINADO')
        self.assertEqual(rules['PET-05']['status'],'INCONCLUSIVO')
        self.assertIn('presenca_rotulo',rules['PET-05']['missing'])

    def test_local_answer_preserves_specific_alternatives_on_incompatibility(self):
        report=assess(import_case(SCENARIO.read_bytes()))
        original=json.loads(json.dumps(report))
        answer=offline_answer('Por que PET-05 está não compatível e quais alternativas?',report)
        self.assertIn('Recomendação ativada',answer['answer'])
        self.assertIn('Orientação da matriz',answer['answer'])
        self.assertIn('PE/PP/OPP',answer['answer'])
        self.assertIn('subcritério incompatível',answer['answer'])
        self.assertIn('DOC-PVC-001',answer['answer'])
        self.assertEqual(original,report)

if __name__=='__main__':unittest.main()
