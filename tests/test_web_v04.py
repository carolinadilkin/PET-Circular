"""HTTP regression for PET Circular Web, no external API calls or real company files."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from server import app

ROOT = Path(__file__).resolve().parents[1]


class WebAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.meta = cls.client.get('/api/bootstrap').json()
        cls.headers = {'X-PET-Session': cls.meta['session_token']}
        cls.a = json.loads((ROOT/'examples/integrated/Design_A_Entrada.json').read_text())
        cls.b = json.loads((ROOT/'examples/integrated/Design_B_Entrada.json').read_text())

    def post(self, path, payload):
        return self.client.post(path, json=payload, headers=self.headers)

    def test_web_assets_reuse_approved_markup(self):
        index = self.client.get('/')
        self.assertEqual(index.status_code,200)
        self.assertIn('Embalagens melhores começam com decisões claras',index.text)
        self.assertIn('/static/styles.css', index.text)
        script=self.client.get('/static/app.js')
        self.assertEqual(script.status_code,200)
        self.assertIn('function renderComparison',script.text)
        self.assertNotIn('Somente simulação visual',index.text)

    def test_mutations_require_local_token(self):
        r=self.client.post('/api/assessment',json={'case':self.a})
        self.assertEqual(r.status_code,403)
        denied=self.client.post('/api/assessment',json={'case':self.a},headers={**self.headers,'Origin':'https://example.com'})
        self.assertEqual(denied.status_code,403)

    def test_motor_a_b_and_comparison(self):
        a=self.post('/api/assessment',{'case':self.a})
        b=self.post('/api/assessment',{'case':self.b})
        self.assertEqual(a.status_code,200,a.text)
        self.assertEqual(b.status_code,200,b.text)
        ra=a.json()['report'];rb=b.json()['report']
        self.assertEqual(set(ra['summary']['incompatibilities_confirmed']),{'PET-05','PET-09','PET-18'})
        self.assertEqual(rb['summary']['incompatibilities_confirmed'],[])
        self.assertEqual(rb['global_recyclability_class'],'NAO_EMITIDA')
        comp=self.post('/api/compare',{'before':ra,'after':rb})
        self.assertEqual(comp.status_code,200,comp.text)
        c=comp.json()['comparison'];self.assertEqual(c['counts'].get('criterio_favoravel'),2)
        self.assertEqual(c['counts'].get('ainda_pendente'),1)
        self.assertEqual(c['counts'].get('pendencia_persistente'),3)
        pet05=next(x for x in c['changes'] if x['rule_id']=='PET-05')
        self.assertEqual(pet05['status_b'],'INCONCLUSIVO')

    def test_profile_edit_downgrades_changed_confirmed_fact(self):
        data=self.post('/api/projects/update',{'case':self.a,'details':{'product_name':'Projeto editado'},'components':{'rotulo':'SIM'},'basic_facts':{'material_corpo':'PVC'}})
        self.assertEqual(data.status_code,200,data.text)
        case=data.json()['case']
        self.assertEqual(case['product_name'],'Projeto editado')
        mat=next(x for x in case['facts'] if x['key']=='material_corpo')
        self.assertEqual(mat['evidence_status'],'DECLARADO')
        self.assertEqual(self.post('/api/assessment',{'case':case}).status_code,200)

    def test_manual_confirmation_is_explicit(self):
        blank=self.meta['new_case']
        base={'case':blank,'key':'polimero_rotulo','value':'PVC','confirm':True}
        self.assertEqual(self.post('/api/projects/fact',base).status_code,422)
        result=self.post('/api/projects/fact',{**base,'reviewer':'Teste responsável','acknowledged':True})
        self.assertEqual(result.status_code,200,result.text)
        fact=result.json()['case']['facts'][0]
        self.assertEqual(fact['evidence_status'],'CONFIRMADO')
        self.assertEqual(fact['human_confirmed_by'],'Teste responsável')

    def test_pdf_extract_then_review_with_page_and_citation(self):
        pdf=(ROOT/'examples/integrated/Ficha_Sintetica_Design_A.pdf').read_bytes()
        c=self.client.post('/api/documents/extract',headers=self.headers,
            files={'file':('ficha.pdf',pdf,'application/pdf')},
            data={'product':json.dumps(self.meta['new_case']),'mode':'local'})
        self.assertEqual(c.status_code,200,c.text[:600]);response=c.json()
        self.assertGreaterEqual(len(response['candidates']),5)
        self.assertEqual(response['case']['facts'],[])
        decisions=[{'accept':True,'value':str(x['value'])} for x in response['candidates']]
        review=self.post('/api/documents/review',{'case':response['case'],
                      'extraction_token':response['extraction_token'], 'decisions':decisions, 'reviewer':'Revisora fictícia'})
        self.assertEqual(review.status_code,200,review.text[:600])
        facts=review.json()['case']['facts']
        self.assertGreaterEqual(len(facts),5)
        self.assertTrue(all(x['evidence_status']=='CONFIRMADO' for x in facts))
        self.assertTrue(all('página' in x['observation'] for x in facts))
        retry=self.post('/api/documents/review',{'case':response['case'],
                      'extraction_token':response['extraction_token'], 'decisions':decisions, 'reviewer':'R'})
        self.assertEqual(retry.status_code,422)

    def test_import_requires_correct_contract(self):
        imported=self.client.post('/api/projects/import',content=json.dumps(self.b).encode(),headers={**self.headers,'Content-Type':'application/json'})
        self.assertEqual(imported.status_code,200,imported.text[:300])
        self.assertEqual(imported.json()['case']['product_id'],self.b['product_id'])
        error=self.client.post('/api/projects/import',data=b'{"anything":1}',headers=self.headers)
        self.assertEqual(error.status_code,422)

    def test_assistant_offline_grounding(self):
        response=self.post('/api/assistant',{'case':self.a,'question':'Quais incompatibilidades foram identificadas?'})
        self.assertEqual(response.status_code,200,response.text[:400])
        answer=response.json()['response']
        self.assertEqual(answer['mode'],'LOCAL')
        self.assertIn('PET-',answer['answer'])
        self.assertIn('não foi emitida',answer['answer'])
        denied=self.post('/api/assistant',{'case':self.a,'question':'PET-05?', 'mode':'api'})
        self.assertEqual(denied.status_code,422)

    def test_snapshots_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{'PET_CIRCULAR_DB':str(Path(tmp)/'snapshot.sqlite3')}):
                saved=self.post('/api/snapshots',{'case':self.a,'include_report':True})
                self.assertEqual(saved.status_code,200,saved.text)
                sid=saved.json()['id']
                hist=self.client.get('/api/snapshots').json()['items']
                self.assertEqual(len(hist),1)
                loaded=self.client.get(f'/api/snapshots/{sid}').json()
                self.assertEqual(loaded['case']['product_id'],self.a['product_id'])
                self.assertEqual(len(loaded['report']['results']),15)

if __name__ == '__main__': unittest.main()
