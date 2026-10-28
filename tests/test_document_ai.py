"""Testes offline de extração, validação de fontes, aprovação humana e travas."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from document_ai import (read_pdf_bytes,local_candidates,llm_candidates,
                         check_candidate, review_apply,measurements_pending)
from ui_helpers import fresh, upsert_document, upsert_fact, example
from pet_circular.engine import assess

PDF=Path(__file__).resolve().parents[1]/'examples/ficha_sintetica_teste.pdf'

class FakeResponses:
    def __init__(self,response):self.response=response;self.params=None
    def create(self,**kwargs):
        self.params=kwargs
        return type('Return',(),{'output_text':json.dumps(self.response,ensure_ascii=False)})()
class FakeClient:
    def __init__(self,response):self.responses=FakeResponses(response)

class PdfExtractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf=read_pdf_bytes(PDF.read_bytes(),PDF.name)
        cls.local=local_candidates(cls.pdf)
    def test_reads_pdf_with_page_numbers_and_hash(self):
        self.assertEqual(self.pdf.total_pages,2)
        self.assertEqual(len(self.pdf.digest),64)
        self.assertIn('Material do corpo: PET',self.pdf.pages[0][1])
    def test_blocks_invalid_pdf_and_scans(self):
        with self.assertRaisesRegex(ValueError,'assinatura'):
            read_pdf_bytes(b'abc','wrong.pdf')
        with self.assertRaisesRegex(ValueError,'12 MB'):
            read_pdf_bytes(b'%PDF-' + b'x'*(12*1024*1024),'big.pdf')
    def test_local_parser_is_conservative(self):
        d={x['key']:x for x in self.local}
        for k in ('material_corpo','transparencia_corpo','cor_corpo','capacidade_ml','material_tampa','polimero_rotulo'):
            self.assertIn(k,d)
        self.assertEqual(d['material_corpo']['value'],'PET')
        self.assertEqual(d['capacidade_ml']['value'],500)
        self.assertNotIn('polimeros_corpo_secundarios',d)
        self.assertEqual(d['material_corpo']['page'],1)
    def test_hallucinated_quote_page_and_key_rejected(self):
        base={'key':'material_corpo','value':'PET','page':1,'quote':'Material do corpo: PET'}
        self.assertEqual(check_candidate(base,self.pdf)['key'],'material_corpo')
        with self.assertRaisesRegex(ValueError,'não localizado'):
            check_candidate({**base,'quote':'Material do corpo: ABS'},self.pdf)
        with self.assertRaisesRegex(ValueError,'Página'):
            check_candidate({**base,'page':99},self.pdf)
        with self.assertRaisesRegex(ValueError,'Campo'):
            check_candidate({**base,'key':'classe_recyclass_global'},self.pdf)
        with self.assertRaisesRegex(ValueError,'não sustenta'):
            check_candidate({**base,'value':'PVC'},self.pdf)
    def test_wrong_component_citation_is_rejected(self):
        candidate={'key':'material_tampa','value':'PET','page':1,'quote':'Material do corpo: PET'}
        with self.assertRaisesRegex(ValueError,'não sustenta'):
            check_candidate(candidate,self.pdf)
    def test_remote_api_with_structured_output_and_local_verification(self):
        fake=FakeClient({'candidates':[
            {'key':'material_corpo','value':'PET','unit':'','page':1,'quote':'Material do corpo: PET','note':''},
            {'key':'material_tampa','value':'PET','unit':'','page':1,'quote':'CITAÇÃO INVENTADA','note':''},
        ]})
        found,rejected=llm_candidates(self.pdf,'test-key','fake',fake)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['method'],'IA_API')
        self.assertEqual(len(rejected),1)
        self.assertFalse(fake.responses.params['store'])
        self.assertEqual(fake.responses.params['text']['format']['type'],'json_schema')
        self.assertNotIn('%PDF-',str(fake.responses.params['input']))
    def test_import_requires_review(self):
        p=fresh()
        p=upsert_document(p,{'id':'DOC1','filename':PDF.name,'source_type':'upload','sha256':self.pdf.digest})
        self.assertEqual(len(p['facts']),0)
        decisions=[{'accept':x['key'] in ('material_corpo','transparencia_corpo','cor_corpo'),'value':str(x['value'])} for x in self.local]
        with self.assertRaisesRegex(ValueError,'responsável'):
            review_apply(p,'DOC1',self.local,decisions,'')
        q,added,skipped=review_apply(p,'DOC1',self.local,decisions,'Revisora')
        self.assertEqual(len(added),3)
        self.assertEqual(skipped,[])
        self.assertTrue(all(f['evidence_status']=='CONFIRMADO' for f in q['facts']))
        self.assertTrue(all(f['evidence_ids']==['DOC1'] for f in q['facts']))
        self.assertEqual(assess(q)['global_recyclability_class'],'NAO_EMITIDA')
        self.assertEqual(p['facts'],[])
    def test_prevent_silent_overwrite(self):
        p=fresh()
        p=upsert_document(p,{'id':'DOC1','filename':PDF.name,'source_type':'upload'})
        p=upsert_fact(p,'material_corpo','PVC',status='CONFIRMADO',reviewer='Engenheira')
        material=next(x for x in self.local if x['key']=='material_corpo')
        unchanged,added,skipped=review_apply(p,'DOC1',[material],[{'accept':True,'value':'PET'}],'Revisora')
        self.assertEqual(added,[])
        self.assertTrue(skipped)
        q,added,_=review_apply(p,'DOC1',[material],[{'accept':True,'overwrite':True,'value':'PET'}],'Revisora')
        self.assertEqual(added,['material_corpo'])
        self.assertEqual(q['facts'][0]['value'],'PET')
    def test_prevent_unsourced_edit(self):
        p=upsert_document(fresh(),{'id':'DOC1','filename':PDF.name,'source_type':'upload'})
        material=next(x for x in self.local if x['key']=='material_corpo')
        with self.assertRaisesRegex(ValueError,'não é sustentado'):
            review_apply(p,'DOC1',[material],[{'accept':True,'value':'PP'}],'Revisora')
    def test_prevent_duplicate_field_selection(self):
        p=upsert_document(fresh(),{'id':'DOC1','filename':PDF.name,'source_type':'upload'})
        a=next(x for x in self.local if x['key']=='material_corpo')
        with self.assertRaisesRegex(ValueError,'Duas propostas'):
            review_apply(p,'DOC1',[a,a],[{'accept':True},{'accept':True}],'Revisora')
    def test_measurements_separate_from_trials(self):
        result=assess(example())
        self.assertEqual(len(result['summary']['trials_pending']),0)
        pending=measurements_pending(result)
        self.assertTrue(any(x['Regra']=='PET-16' for x in pending))
        self.assertEqual(result['global_recyclability_class'],'NAO_EMITIDA')

if __name__=='__main__':unittest.main()
