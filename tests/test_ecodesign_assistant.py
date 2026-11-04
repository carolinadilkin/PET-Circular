"""Testes offline do assistente explicativo: não avaliam precisão de LLM remoto."""
import unittest
from ecodesign_assistant import select_rules, offline_answer, llm_answer, make_context
from ui_helpers import example
from pet_circular.engine import assess

class FakeResponses:
    def __init__(self): self.called=None
    def create(self,**kw):
        self.called=kw
        return type('Response',(),{'output_text':'A PET-19 depende da estrutura; faltam informações. Classe global não emitida.'})()
class FakeClient:
    def __init__(self):self.responses=FakeResponses()

class AssistantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=assess(example())

    def test_explicit_id(self):
        self.assertEqual(select_rules('Explique a PET-19',self.report),['PET-19'])

    def test_alias(self):
        self.assertEqual(select_rules('Há um problema no sleeve?',self.report),['PET-19'])

    def test_unknown_query_uses_report(self):
        ids=select_rules('O que falta?',self.report)
        self.assertTrue(ids)
        self.assertTrue(all(r in {x['rule_id'] for x in self.report['results']} for r in ids))

    def test_no_global_certification(self):
        a=offline_answer('PET-01',self.report)
        self.assertIn('não foi emitida',a['answer'])
        self.assertIn('PET-01',a['answer'])
        self.assertEqual(self.report['global_recyclability_class'],'NAO_EMITIDA')

    def test_missing_evidence(self):
        a=offline_answer('PET-19',self.report)
        self.assertIn('sleeve',a['answer'].lower())
        self.assertIn('presenca_sleeve',a['answer'])

    def test_limit_length(self):
        with self.assertRaisesRegex(ValueError,'máximo'):
            offline_answer('x'*2001,self.report)

    def test_hypothesis_is_not_confirmation(self):
        a=offline_answer('Se eu trocar o sleeve?',self.report)
        self.assertIn('hipotético',a['answer'])

    def test_source_links_from_registry(self):
        a=offline_answer('PET-19',self.report)
        self.assertTrue(any(x['id']=='REF-04' for x in a['sources']))
        self.assertTrue(all(x['url'].startswith('https://') for x in a['sources']))

    def test_model_needs_key(self):
        with self.assertRaisesRegex(ValueError,'Chave'):
            llm_answer('PET-19',self.report,'')

    def test_mock_remote_does_not_edit_report(self):
        import copy
        old=copy.deepcopy(self.report)
        fake=FakeClient()
        answer=llm_answer('PET-19',self.report,'fake-key','gpt-4.1-mini',fake)
        self.assertEqual(self.report,old)
        self.assertEqual(answer['mode'],'IA_API')
        self.assertFalse(fake.responses.called['store'])
        self.assertEqual(fake.responses.called['max_output_tokens'],850)
        self.assertNotIn('ficha_sintetica_teste.pdf',str(fake.responses.called))

if __name__=='__main__': unittest.main()
