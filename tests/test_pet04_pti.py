"""Regressões do PTI-PET04-001; casos sintéticos assumidos como aceitos no projeto."""
import unittest
from test_engine import base, fact, component, check


class TestPTIPET04(unittest.TestCase):
    def m2(self, vol=500, covered=50, total=100):
        p=base();component(p,'rotulo');component(p,'sleeve','NAO')
        fact(p,'capacidade_ml',vol)
        fact(p,'metodo_cobertura','M2')
        fact(p,'area_referencia_lateral_cm2',total)
        fact(p,'area_coberta_lateral_cm2',covered)
        fact(p,'polimero_rotulo','PP')
        return p

    def test_m1_uses_larger_projection(self):
        p=self.m2();fact(p,'metodo_cobertura','M1')
        for k,v in {'area_referencia_frente_cm2':100,'area_coberta_frente_cm2':30,
                    'area_referencia_verso_cm2':100,'area_coberta_verso_cm2':60}.items():fact(p,k,v)
        r=check(p,'PET-04')
        self.assertEqual(r['details']['cobertura_pct'],60)
        self.assertEqual(r['details']['faixa_indicativa'],'ACIMA')
        self.assertEqual(r['status'],'INCONCLUSIVO')

    def test_m2_at_exact_limit_not_above(self):
        r=check(self.m2(),'PET-04')
        self.assertEqual(r['details']['cobertura_pct'],50)
        self.assertFalse(r['details']['acima_indicacao'])
        self.assertFalse(r['details']['gatilho_sep01'])

    def test_over_70_is_not_required_to_trigger_sep01_label(self):
        p=self.m2(vol=750,covered=60)
        r=check(p,'PET-04')
        self.assertFalse(r['details']['acima_indicacao'])
        self.assertEqual(r['trial'],'REQUERIDO')
        self.assertIn('rotulo_outro_polimero_acima_50',r['details']['gatilhos_sep01'])

    def test_sleeve_integral_triggers_even_without_geometry(self):
        p=base();component(p,'sleeve');component(p,'rotulo','NAO');fact(p,'sleeve_tipo','integral')
        r=check(p,'PET-04')
        self.assertEqual(r['trial'],'REQUERIDO')
        self.assertIn('sleeve_integral',r['details']['gatilhos_sep01'])
        self.assertEqual(r['status'],'INCONCLUSIVO')

    def test_metalization_triggers_even_below_threshold(self):
        p=self.m2(covered=15);fact(p,'tipo_rotulo','metalizado')
        r=check(p,'PET-04')
        self.assertFalse(r['details']['acima_indicacao'])
        self.assertEqual(r['trial'],'REQUERIDO')
        self.assertIn('metalizacao',r['details']['gatilhos_sep01'])

    def test_coverage_uncertainty_straddles_threshold(self):
        p=self.m2(covered=52);fact(p,'incerteza_cobertura_pct',3)
        r=check(p,'PET-04')
        self.assertEqual(r['details']['faixa_indicativa'],'LIMITROFE')
        self.assertIsNone(r['details']['acima_indicacao'])

    def test_divergent_manual_percentage_requests_review(self):
        p=self.m2(covered=50);fact(p,'cobertura_nao_pet_pct',80)
        r=check(p,'PET-04')
        self.assertIsNone(r['details']['acima_indicacao'])
        self.assertIn('conciliacao_percentuais_cobertura',r['missing'])

    def test_invalid_geometric_areas_not_accepted(self):
        p=self.m2(covered=110)
        r=check(p,'PET-04')
        self.assertEqual(r['status'],'INCONCLUSIVO')
        self.assertIn('areas_geometricas_validas',r['missing'])

    def test_unknown_polymer_above_50_not_marked_as_trial_exempt(self):
        p=self.m2(covered=51)
        p['facts']=[f for f in p['facts'] if f['key']!='polimero_rotulo']
        r=check(p,'PET-04')
        self.assertEqual(r['trial'],'PENDENTE')
        self.assertIn('polimero_rotulo',r['missing'])

    def test_no_label_or_sleeve_is_not_applicable(self):
        p=base();component(p,'rotulo','NAO');component(p,'sleeve','NAO')
        self.assertEqual(check(p,'PET-04')['status'],'NAO_APLICAVEL')

    def test_direct_printing_is_not_mistaken_for_absence(self):
        p=base();component(p,'rotulo','NAO');component(p,'sleeve','NAO')
        fact(p,'tipo_decoracao','impressao_direta')
        self.assertEqual(check(p,'PET-04')['status'],'INCONCLUSIVO')
