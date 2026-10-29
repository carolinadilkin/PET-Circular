"""Regressões de cenários fictícios A vs B. Não são validação laboratorial ou certificação."""
import json
import sys
import unittest
from pathlib import Path
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pet_circular.engine import assess, validate
from document_ai import read_pdf_bytes, local_candidates
from ecodesign_assistant import offline_answer

FIX = ROOT / 'examples' / 'integrated'


def load(name):
    return json.loads((FIX / name).read_text(encoding='utf-8'))


class IntegratedPackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=load('Design_A_Entrada.json')
        cls.b=load('Design_B_Entrada.json')
        cls.ra=assess(cls.a)
        cls.rb=assess(cls.b)
        cls.am={r['rule_id']:r for r in cls.ra['results']}
        cls.bm={r['rule_id']:r for r in cls.rb['results']}

    def test_envelopes_and_scope(self):
        for name, inp, out in [('A',self.a,self.ra),('B',self.b,self.rb)]:
            with self.subTest(name=name):
                validate(inp)
                self.assertEqual(out['scope'],'DENTRO')
                self.assertEqual(len(out['results']),15)
                self.assertEqual(len(inp['components']),11)
                self.assertEqual(sum(c['presence']=='SIM' for c in inp['components']),5)
                self.assertEqual(out['global_recyclability_class'],'NAO_EMITIDA')
                self.assertFalse(out['official_certification'])
                self.assertEqual(out['summary']['data_issues'],[])

    def test_design_a_three_incompatibilities(self):
        self.assertEqual(set(self.ra['summary']['incompatibilities_confirmed']),{'PET-05','PET-09','PET-18'})
        self.assertEqual(self.am['PET-01']['status'],'COMPATIVEL')
        self.assertEqual(self.am['PET-07']['status'],'COMPATIVEL')
        self.assertIn('densidade',self.am['PET-05']['reason'].lower())

    def test_redesign_b_improves_but_is_not_certified(self):
        self.assertEqual(self.rb['summary']['incompatibilities_confirmed'],[])
        for rid in ('PET-01','PET-07','PET-09','PET-18'):
            self.assertEqual(self.bm[rid]['status'],'COMPATIVEL')
        for rid in ('PET-04','PET-05','PET-16','PET-17'):
            self.assertEqual(self.bm[rid]['status'],'INCONCLUSIVO')
        self.assertIn('PET-17',self.rb['summary']['trials_pending'])
        self.assertTrue(self.bm['PET-05']['details'].get('material_favoravel'))

    def test_expected_reports_match_exact_engine_outputs(self):
        for k,p in [('A',self.ra),('B',self.rb)]:
            with self.subTest(design=k):
                self.assertEqual(p,load(f'Design_{k}_Resultado_Esperado.json'))

    def test_synthetic_pdf_hashes_and_extraction(self):
        for name,inp in [('A',self.a),('B',self.b)]:
            with self.subTest(design=name):
                blob=(FIX / f'Ficha_Sintetica_Design_{name}.pdf').read_bytes()
                self.assertEqual(sha256(blob).hexdigest(),inp['documents'][0]['sha256'])
                doc=read_pdf_bytes(blob,f'Ficha_Sintetica_Design_{name}.pdf')
                candidates={x['key']:x for x in local_candidates(doc)}
                for field in ('material_corpo','transparencia_corpo','cor_corpo','capacidade_ml','material_tampa','polimero_rotulo'):
                    self.assertIn(field,candidates)
                    self.assertGreaterEqual(candidates[field]['page'],1)
                label=next(x['value'] for x in inp['facts'] if x['key']=='polimero_rotulo')
                self.assertEqual(candidates['polimero_rotulo']['value'],label)

    def test_assistant_grounding_is_separate_from_engine(self):
        answer=offline_answer('Quais incompatibilidades foram identificadas e o que deve mudar?',self.ra)
        self.assertEqual(set(answer['rule_ids']),{'PET-05','PET-09','PET-18'})
        self.assertIn('classe global',answer['answer'])
        self.assertEqual(self.ra['global_recyclability_class'],'NAO_EMITIDA')
        b=offline_answer('Por que a PET-05 está inconclusiva?',self.rb)
        self.assertIn('PET-05',b['rule_ids'])
        self.assertIn('inconclusivo',b['answer'].lower())
        self.assertTrue(b['sources'])

if __name__=='__main__':
    unittest.main()
