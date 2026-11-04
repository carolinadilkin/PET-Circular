"""PET-16: limites dimensionais e controle de proveniência (dados sintéticos)."""
import unittest
from tests.test_engine import base, fact, check

class TestPET16(unittest.TestCase):
    def start(self):
        return base()

    def measure(self,p,dim,proto='ensaio interno: dimensão de controle após compressão',source='REL-016',approved='sim',unit='cm'):
        fact(p,'dimensoes_apos_compactacao',dim)
        p['facts'][-1]['unit']=unit
        if proto is not None:fact(p,'protocolo_compactacao',proto)
        if source is not None:fact(p,'fonte_medicao',source)
        if approved is not None:fact(p,'validacao_operacional_4cm',approved)
        return p

    def test_capacity_above_five_even_without_compaction(self):
        p=self.start();fact(p,'capacidade_ml',5001)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_COMPATIVEL');self.assertTrue(r['details']['gatilho_5l'])
    def test_capacity_boundary_five_is_not_veto(self):
        p=self.start();fact(p,'capacidade_ml',5000)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertFalse(r['details']['gatilho_5l'])
    def test_compacted_exact_four_with_evidence_is_veto(self):
        p=self.start();self.measure(p,4)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_COMPATIVEL');self.assertTrue(r['details']['gatilho_4cm'])
        self.assertIn('capacidade_nominal_confirmada_e_consistente',r['missing']) if not any(x['key']=='capacidade_ml' for x in p['facts']) else None
    def test_above_four_and_under_five_not_triggered(self):
        p=self.start();self.measure(p,4.001)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_ACIONADA');self.assertFalse(r['details']['gatilho_4cm'])
    def test_no_validation_means_inconclusive(self):
        p=self.start();self.measure(p,3.5,approved=None)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertIn('validacao_operacional_4cm',r['missing'])
    def test_validation_false_means_inconclusive(self):
        p=self.start();self.measure(p,3.5,approved=False)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO')
    def test_missing_source_means_inconclusive(self):
        p=self.start();self.measure(p,3.5,source=None)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertIn('fonte_medicao',r['missing'])
    def test_missing_protocol_means_inconclusive(self):
        p=self.start();self.measure(p,3.5,proto=None)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertIn('protocolo_compactacao',r['missing'])
    def test_unconfirmed_dimension_is_not_veto(self):
        p=self.start();self.measure(p,3.5)
        fact(p,'dimensoes_apos_compactacao',3.5,status='DECLARADO')
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO')
    def test_invalid_dimensions_cannot_trigger_veto(self):
        for dim in (0,-1,'N/A'):
            with self.subTest(dim=dim):
                p=self.start();self.measure(p,dim)
                r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO')
    def test_dimension_unit_mm_not_silently_cm(self):
        p=self.start();self.measure(p,3.5,unit='mm')
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO')
    def test_conflicting_volume_units(self):
        p=self.start();fact(p,'volume_l',5.1);fact(p,'capacidade_ml',5000)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertIsNone(r['details']['gatilho_5l'])
    def test_independent_dimension_veto_even_when_volume_conflicts(self):
        p=self.start();fact(p,'volume_l',5.1);fact(p,'capacidade_ml',5000);self.measure(p,3.5)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_COMPATIVEL');self.assertTrue(r['details']['gatilho_4cm'])
    def test_confirmed_volume_l_and_ml_agree(self):
        p=self.start();fact(p,'volume_l',5.001);fact(p,'capacidade_ml',5001)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_COMPATIVEL')
    def test_volume_less_than_five_with_missing_dim_is_not_compatible(self):
        p=self.start();fact(p,'capacidade_ml',500)
        r=check(p,'PET-16');self.assertEqual(r['status'],'INCONCLUSIVO');self.assertNotEqual(r['status'],'COMPATIVEL')
    def test_volume_above_five_and_dimension_also_trigger(self):
        p=self.start();fact(p,'capacidade_ml',6000);self.measure(p,3)
        r=check(p,'PET-16');self.assertEqual(r['status'],'NAO_COMPATIVEL')
    def test_no_global_certification(self):
        from pet_circular.engine import assess
        p=self.start();self.measure(p,3.5)
        r=assess(p);self.assertFalse(r['official_certification']);self.assertEqual(r['global_recyclability_class'],'NAO_EMITIDA')

if __name__=='__main__': unittest.main()
