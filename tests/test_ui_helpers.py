"""Testes das funções independentes do framework Streamlit."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import storage
from pet_circular.engine import assess
from ui_helpers import (example,fresh,fields_catalog,upsert_fact,remove_fact,
                        set_components,upsert_document,remove_document,import_case,
                        fingerprint,rows,rule_catalog,missing)

class TestInterfaceIntegration(unittest.TestCase):
    def test_catalog_all_field_keys_snakecase(self):
        d=fields_catalog()
        self.assertGreaterEqual(len(d),70)
        self.assertIn('eupia_declaracao',d)
        self.assertIn('evidencias_nir',d)
        for k in d:
            self.assertEqual(k,k.lower())

    def test_patrico_does_not_get_global_class(self):
        result=assess(example())
        self.assertEqual(len(result['results']),15)
        self.assertEqual(result['global_recyclability_class'],'NAO_EMITIDA')
        self.assertEqual({x['rule_id']:x['status'] for x in result['results']}['PET-01'],'COMPATIVEL')
        self.assertEqual(len(rows(result,rule_catalog())),15)
        self.assertTrue(missing(result))

    def test_declaration_does_not_confirm_scope(self):
        p=fresh()
        p=upsert_fact(p,'material_corpo','PET',status='DECLARADO')
        p=upsert_fact(p,'transparencia_corpo','transparente')
        p=upsert_fact(p,'cor_corpo','incolor')
        result=assess(p)
        self.assertEqual({x['rule_id']:x['status'] for x in result['results']}['PET-01'],'INCONCLUSIVO')

    def test_human_confirmation_allows_scope(self):
        p=fresh()
        for k,v in [('material_corpo','PET'),('transparencia_corpo','transparente'),('cor_corpo','incolor')]:
            p=upsert_fact(p,k,v,status='CONFIRMADO',reviewer='Engenheira responsável')
        result=assess(p)
        self.assertEqual({x['rule_id']:x['status'] for x in result['results']}['PET-01'],'COMPATIVEL')
        self.assertEqual(result['global_recyclability_class'],'NAO_EMITIDA')

    def test_confirmed_without_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'CONFIRMADO'):
            upsert_fact(fresh(),'material_corpo','PET',status='CONFIRMADO')

    def test_numeric_comma_and_invalid_numeric(self):
        p=upsert_fact(fresh(),'capacidade_ml','500,5',status='DECLARADO',unit='mL')
        self.assertEqual(p['facts'][0]['value'],500.5)
        with self.assertRaises(ValueError):
            upsert_fact(p,'capacidade_ml','500 mL')
        with self.assertRaises(ValueError):
            upsert_fact(p,'numero_ensaios','9,5')

    def test_component_missing_is_not_absence(self):
        p=fresh()
        self.assertEqual({c['kind']:c['presence'] for c in p['components']}['tampa'],'DESCONHECIDA')
        p=set_components(p,{'tampa':'NAO','corpo':'SIM'})
        self.assertEqual({c['kind']:c['presence'] for c in p['components']}['tampa'],'NAO')

    def test_evidence_reference_and_delete_protection(self):
        p=upsert_document(fresh(),{'id':'DOC1','filename':'ficha.pdf','source_type':'upload'})
        p=upsert_fact(p,'material_corpo','PET',status='CONFIRMADO',evidence_ids=['DOC1'])
        with self.assertRaisesRegex(ValueError,'referenciado'):
            remove_document(p,'DOC1')
        p=remove_fact(p,'material_corpo')
        p=remove_document(p,'DOC1')
        self.assertEqual(p['documents'],[])

    def test_import_json_contract_and_version(self):
        p=example()
        copy_json=json.dumps(p).encode('utf-8')
        self.assertEqual(import_case(copy_json)['product_id'],p['product_id'])
        p['matrix_version']='0.2.0'
        with self.assertRaisesRegex(ValueError,'Incompatibilidade'):
            import_case(json.dumps(p).encode('utf-8'))
        with self.assertRaises(ValueError):
            import_case(b'{"hello":"world"}')

    def test_data_edits_change_fingerprint(self):
        p=fresh()
        q=upsert_fact(p,'material_corpo','PET')
        self.assertNotEqual(fingerprint(p),fingerprint(q))

    def test_sqlite_snapshots_are_historical(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'test.sqlite3'
            p=fresh(); sid1=storage.save(p,None,db)
            q=upsert_fact(p,'material_corpo','PET')
            sid2=storage.save(q,assess(q),db)
            self.assertEqual(sid1+1,sid2)
            self.assertEqual(len(storage.latest(db)),1)
            first,_=storage.load(sid1,db)
            last,res=storage.load(sid2,db)
            self.assertEqual(first['facts'],[])
            self.assertEqual(len(last['facts']),1)
            self.assertEqual(res['global_recyclability_class'],'NAO_EMITIDA')

if __name__=='__main__':unittest.main()
