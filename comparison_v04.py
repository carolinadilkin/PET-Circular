"""Comparação determinística de relatórios de critérios PET Circular.

Sem índice global de reciclabilidade; não modifica o motor nem avaliações originais.
O arquivo de relatório não inclui todos os fatos de entrada, portanto a transição
não prova causalidade nem comprova a alteração física da embalagem.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from pet_circular.engine import ALLOWED, RULE_ORDER

MAX_JSON_BYTES = 2_000_000
TRANSITION_DESCRIPTIONS = {
    ('NAO_COMPATIVEL', 'COMPATIVEL'): (
        'criterio_favoravel', 'Incompatibilidade não identificada no Design B; critério compatível neste cenário'),
    ('NAO_COMPATIVEL', 'INCONCLUSIVO'): (
        'ainda_pendente', 'Incompatibilidade não identificada no B, mas critério ainda inconclusivo'),
    ('INCONCLUSIVO', 'COMPATIVEL'): (
        'pendencia_sanada', 'Critério passou a compatível com os dados disponíveis no B'),
    ('COMPATIVEL', 'NAO_COMPATIVEL'): (
        'novo_problema', 'Nova incompatibilidade identificada no Design B'),
    ('INCONCLUSIVO', 'INCONCLUSIVO'): (
        'pendencia_persistente', 'Critério inconclusivo nos dois designs'),
}


def validate_report(report: Any) -> dict:
    if not isinstance(report, dict):
        raise ValueError('Relatório inválido: era esperado um objeto JSON.')
    required = ('product_id', 'matrix_version', 'engine_version', 'scope', 'results')
    if any(not report.get(k) for k in required):
        raise ValueError('O arquivo não é um relatório de avaliação: faltam campos de identificação ou resultados.')
    results = report['results']
    if not isinstance(results, list) or len(results) != len(RULE_ORDER):
        raise ValueError(f'O relatório deve conter {len(RULE_ORDER)} critérios de avaliação.')
    ids = [item.get('rule_id') for item in results if isinstance(item, dict)]
    if len(ids) != len(results) or set(ids) != set(RULE_ORDER) or len(set(ids)) != len(ids):
        raise ValueError('Os IDs de regras estão incompletos, duplicados ou são incompatíveis.')
    for rule in results:
        if rule.get('status') not in ALLOWED:
            raise ValueError(f"Estado inválido para {rule['rule_id']}.")
        if not isinstance(rule.get('missing', []), list):
            raise ValueError(f"Pendências inválidas em {rule['rule_id']}.")
    return report


def parse_report(data: bytes) -> dict:
    if not data or len(data) > MAX_JSON_BYTES:
        raise ValueError('Selecione um relatório JSON de avaliação com tamanho máximo de 2 MB.')
    try:
        report = json.loads(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('Não foi possível interpretar o relatório JSON.') from exc
    return validate_report(report)


def compare_reports(before: dict, after: dict) -> dict:
    a = {r['rule_id']: r for r in validate_report(before)['results']}
    b = {r['rule_id']: r for r in validate_report(after)['results']}
    changes = []
    summary = Counter()
    for rule_id in RULE_ORDER:
        old, new = a[rule_id], b[rule_id]
        s1, s2 = old['status'], new['status']
        category, description = TRANSITION_DESCRIPTIONS.get(
            (s1, s2), ('sem_mudanca', 'Estado mantido' if s1 == s2 else 'Mudança de estado sem classificação automática de melhoria')
        )
        if s1 == s2 == 'INCONCLUSIVO' and set(old.get('missing', [])) != set(new.get('missing', [])):
            description += '; as informações pendentes mudaram'
        if s1 == s2 and s1 != 'INCONCLUSIVO':
            category = 'sem_mudanca'
        summary[category] += 1
        changes.append({
            'rule_id': rule_id, 'status_a': s1, 'status_b': s2,
            'category': category, 'description': description,
            'missing_a': list(old.get('missing', [])), 'missing_b': list(new.get('missing', [])),
            'evidence_a': list(old.get('evidence_ids', [])), 'evidence_b': list(new.get('evidence_ids', [])),
            'reason_a': old.get('reason', ''), 'reason_b': new.get('reason', ''),
        })
    warnings = []
    if before['matrix_version'] != after['matrix_version']:
        warnings.append('Versões de matriz diferentes: a comparação dos critérios pode não ser equivalente.')
    if before['engine_version'] != after['engine_version']:
        warnings.append('Versões do motor diferentes: diferenças de implementação podem afetar os resultados.')
    if before['scope'] != after['scope']:
        warnings.append('O escopo técnico mudou entre as duas avaliações.')
    if before['product_id'] != after['product_id']:
        warnings.append('Os relatórios têm IDs de produto diferentes. Confirme que são designs comparáveis do mesmo projeto.')
    if before.get('design_version') == after.get('design_version') and before['product_id'] == after['product_id']:
        warnings.append('Ambos os relatórios têm a mesma identidade e versão de design; confira a seleção.')
    if before == after:
        raise ValueError('Os relatórios selecionados são idênticos. Escolha dois resultados diferentes.')
    return {
        'design_a': {'product_id': before['product_id'], 'product_name': before.get('product_name', ''),
                     'design_version': before.get('design_version', ''), 'engine_version': before['engine_version'],
                     'matrix_version': before['matrix_version'], 'scope': before['scope']},
        'design_b': {'product_id': after['product_id'], 'product_name': after.get('product_name', ''),
                     'design_version': after.get('design_version', ''), 'engine_version': after['engine_version'],
                     'matrix_version': after['matrix_version'], 'scope': after['scope']},
        'counts': dict(summary), 'changes': changes, 'warnings': warnings,
        'global_classification': 'NAO_EMITIDA',
        'method_note': 'Comparação de resultados individuais de software, sem cálculo global; PDFs, ensaios e causalidade de mudanças não são comprovados pelos relatórios.',
    }
