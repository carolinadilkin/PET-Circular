"""Interface guiada PET Circular v0.4: jornada, projetos, resultados e comparação.

Módulo apenas de apresentação. Classificação via pet_circular.engine.assess;
revisão documental via ui_document_ai; comparação via comparison_v04.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

import storage
from comparison_v04 import compare_reports, parse_report
from document_ai import measurements_pending
from pet_circular.engine import assess, validate
from ui_assistant import render_assistant
from ui_document_ai import render_document_ai
from ui_helpers import (EVIDENCE, KIND_LABELS, KINDS, PRESENCE, STATUSES, fields_catalog,
                        fingerprint, fresh, import_case, rule_catalog, set_components,
                        source_catalog, upsert_fact)

BASE = Path(__file__).resolve().parent
RULES = rule_catalog()
SOURCES = source_catalog()
FIELDS = fields_catalog()
SCOPE_FIELDS = ('material_corpo', 'transparencia_corpo', 'cor_corpo', 'capacidade_ml')
STEPS = ('1. Embalagem', '2. Informações', '3. Revisar', '4. Resultados')
FIELD_LABELS = {
    'material_corpo': 'Material do corpo', 'transparencia_corpo': 'Transparência do corpo',
    'cor_corpo': 'Cor do corpo', 'capacidade_ml': 'Capacidade nominal (mL)',
    'presenca_rotulo': 'Presença do rótulo', 'presenca_sleeve': 'Presença de sleeve',
    'presenca_tampa': 'Presença de tampa', 'presenca_barreira': 'Presença de barreira',
    'cobertura_nao_pet_pct': 'Cobertura não PET (%)',
    'validacao_metodo_normativo_cobertura': 'Método de medição da cobertura ainda não validado',
    'dimensoes_apos_compactacao': 'Dimensões após compactação',
    'protocolo_compactacao': 'Protocolo para avaliação da compactação',
    'massa_conteudo_nominal_g': 'Massa nominal do produto (g)',
    'media_pos_esvaziar_g': 'Massa média após esvaziamento (g)',
    'metodo_ete': 'Método do ensaio Easy-to-Empty',
    'numero_ensaios': 'Número de ensaios realizados',
    'peso_embalagem_vazia_g': 'Massa da embalagem vazia (g)',
    'polimero_rotulo': 'Material do rótulo', 'densidade_rotulo': 'Densidade do rótulo',
    'desprendimento': 'Desprendimento do rótulo', 'fixacao_rotulo': 'Fixação do rótulo',
}


def pretty_field(key: str) -> str:
    return FIELD_LABELS.get(key, key.replace('_', ' ').capitalize())


def go(section: str, step: int | None = None):
    st.session_state.pending_nav_v04 = section
    if step is not None:
        st.session_state.guide_step_v04 = step
    st.rerun()


def stage(step: int):
    st.session_state.guide_step_v04 = max(0, min(step, len(STEPS) - 1))
    st.rerun()


def known_components(case: dict) -> int:
    return sum(c.get('presence') != 'DESCONHECIDA' for c in case.get('components', []))


def _status_label(value: str) -> str:
    return STATUSES.get(value, value.replace('_', ' ').capitalize())


def _fact(case, key):
    return next((x for x in reversed(case['facts']) if x['key'] == key), None)


def _raw_value(case, key, default=''):
    item = _fact(case, key)
    return str(item['value']) if item and item.get('value') is not None else default


def _project_context(case: dict, result: dict | None = None):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(f"**Produto ativo:** {case['product_name']}")
        st.caption(f"ID: `{case['product_id']}` · Versão: `{case.get('design_version','v1')}`")
    with c2:
        st.metric('Informações técnicas', len(case['facts']))
    with c3:
        st.metric('Presença definida', f"{known_components(case)}/11")
    st.caption('Resultado por critérios · Não constitui classe global de reciclabilidade ou certificação.')
    if result is None and st.session_state.get('assessment_stale_v04'):
        st.warning('Os dados foram alterados desde a última avaliação. Execute a avaliação novamente.')


def home(case: dict, result: dict | None):
    st.caption('PET CIRCULAR · GUIDED ECODESIGN STUDIO')
    st.title('O que você deseja fazer?')
    st.write('Avalie uma embalagem PET transparente, compreenda as limitações técnicas e compare alternativas de design.')
    st.info('Escopo inicial: garrafas PET transparentes incolores ou azul-claras. Fora do escopo não significa não reciclável.')
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown('### Avaliar uma embalagem')
            st.write('Cadastre um produto, envie uma ficha técnica ou preencha os dados manualmente.')
            if st.button('Iniciar avaliação', type='primary', use_container_width=True, key='home_start_v04'):
                go('Avaliação', 0)
        with st.container(border=True):
            st.markdown('### Continuar um projeto')
            st.write('Recupere uma versão salva ou importe os dados de um projeto existente.')
            if st.button('Ver meus projetos', use_container_width=True, key='home_projects_v04'):
                go('Projetos')
    with right:
        with st.container(border=True):
            st.markdown('### Comparar versões de design')
            st.write('Veja quais critérios melhoraram, pioraram ou continuam sem evidência suficiente.')
            if st.button('Abrir comparação A/B', use_container_width=True, key='home_compare_v04'):
                go('Comparação')
        with st.container(border=True):
            st.markdown('### Trabalho em andamento')
            st.write(f"**{case['product_name']}** · {len(case['facts'])} informações técnicas")
            st.caption('Não há salvamento automático. Salve um snapshot em Projetos para retomar o trabalho.')
            if result:
                counts = Counter(x['status'] for x in result['results'])
                st.write(f"Última avaliação atual: {counts['NAO_COMPATIVEL']} incompatibilidades; {counts['INCONCLUSIVO']} critérios inconclusivos.")
            if st.button('Continuar avaliação', use_container_width=True, key='home_continue_v04'):
                go('Avaliação', 3 if result else 0)
    st.caption('O assistente é opcional. As classificações são produzidas pelo motor técnico, nunca pela conversa.')


def guided(case: dict, commit, result: dict | None):
    st.title('Avaliar embalagem')
    _project_context(case, result)
    step_index = int(st.session_state.get('guide_step_v04', 0))
    selection = st.radio('Etapas — você pode voltar ou continuar com informações faltantes',
                         STEPS, index=step_index, horizontal=True, key=f'guide_choice_v04_{step_index}')
    current_step = STEPS.index(selection)
    st.session_state.guide_step_v04 = current_step
    st.divider()
    if current_step == 0:
        _packaging(case, commit)
    elif current_step == 1:
        _information(case, commit)
    elif current_step == 2:
        _review(case, commit)
    else:
        results(case, commit, result)
    st.divider()
    if current_step:
        left, right = st.columns(2)
        with left:
            if st.button('Voltar etapa', key='guide_prev_v04'):
                stage(current_step - 1)
        with right:
            if current_step < len(STEPS) - 1:
                if st.button('Continuar para a próxima etapa', type='primary', key='guide_next_v04'):
                    stage(current_step + 1)
    elif st.button('Continuar para informações técnicas', type='primary', key='guide_next_v04'):
        stage(1)


def _packaging(case: dict, commit):
    st.subheader('1. Conhecer a embalagem')
    st.caption('Identifique o produto e indique a presença dos componentes. Pode deixar informações como “Ainda não sei”.')
    docs = [d['id'] for d in case['documents']]
    known_source = docs[0] if docs else None
    with st.form('guided_product_form_v04'):
        a, b = st.columns(2)
        with a:
            name = st.text_input('Nome da embalagem', value=case['product_name'])
            project_id = st.text_input('Identificador do projeto', value=case['project_id'])
            product_id = st.text_input('Código do produto', value=case['product_id'])
        with b:
            design = st.text_input('Versão do design', value=case.get('design_version', 'v1'))
            phase = st.selectbox('Fase do desenvolvimento', ['projeto_definido', 'ideacao'],
                                 index=0 if case['phase'] == 'projeto_definido' else 1,
                                 format_func=lambda x: 'Produto definido' if x == 'projeto_definido' else 'Ideação')
            capacity = st.text_input('Capacidade nominal (mL)', value=_raw_value(case, 'capacidade_ml'),
                                     help='Exemplo: 500. Use somente o número.')
        a, b, c = st.columns(3)
        options_material = ['Não informado', 'PET', 'outro']
        options_transparency = ['Não informado', 'transparente', 'opaco']
        options_color = ['Não informado', 'incolor', 'azul-claro', 'preta', 'outra']
        def option_index(opts, key):
            val = _raw_value(case, key)
            return opts.index(val) if val in opts else 0
        with a: material = st.selectbox('Material do corpo', options_material, index=option_index(options_material, 'material_corpo'))
        with b: transparency = st.selectbox('Transparência', options_transparency, index=option_index(options_transparency, 'transparencia_corpo'))
        with c: color = st.selectbox('Cor do corpo', options_color, index=option_index(options_color, 'cor_corpo'))
        st.markdown('**Presença dos componentes**')
        st.caption('Ausente significa que o componente não existe no design; “Ainda não sei” não significa ausente.')
        component_map = {x['kind']: x['presence'] for x in case['components']}
        new_comp = {}
        labels = {'DESCONHECIDA': 'Ainda não sei', 'SIM': 'Presente', 'NAO': 'Ausente'}
        columns = st.columns(2)
        primary = ('corpo', 'tampa', 'rotulo', 'adesivo', 'tinta')
        for idx, kind in enumerate(primary):
            with columns[idx % 2]:
                current = component_map.get(kind, 'DESCONHECIDA')
                new_comp[kind] = st.selectbox(KIND_LABELS[kind], PRESENCE, index=PRESENCE.index(current),
                                              key=f'guide_comp_{kind}', format_func=lambda x: labels[x])
        with st.expander('Outros componentes (sleeve, barreira, liner e acessórios)'):
            cols = st.columns(2)
            for idx, kind in enumerate(k for k in KINDS if k not in primary):
                with cols[idx % 2]:
                    current = component_map.get(kind, 'DESCONHECIDA')
                    new_comp[kind] = st.selectbox(KIND_LABELS[kind], PRESENCE, index=PRESENCE.index(current),
                                                  key=f'guide_comp_{kind}', format_func=lambda x: labels[x])
        description = st.text_area('Observações e requisitos funcionais (opcional)', value=case.get('free_description', ''), height=80)
        st.divider()
        source = st.selectbox('Documento relacionado aos dados do corpo (opcional)', ['Sem documento'] + docs,
                              index=0 if not known_source else 1)
        reviewer = st.text_input('Responsável pela confirmação (se aplicável)', placeholder='Nome ou identificação técnica')
        confirmed = st.checkbox('Revisei os dados básicos do corpo e confirmo sua origem ou minha responsabilidade técnica.')
        st.caption('Sem marcar a confirmação, os valores serão DECLARADOS e não serão tratados como evidência confirmada.')
        submitted = st.form_submit_button('Salvar informações da embalagem', type='primary')
    if submitted:
        try:
            if not all(x.strip() for x in (name, project_id, product_id, design)):
                raise ValueError('Informe nome, projeto, código do produto e versão do design.')
            if confirmed and not (reviewer.strip() or source != 'Sem documento'):
                raise ValueError('Para confirmar o corpo, identifique o revisor ou documento correspondente.')
            updated = {**case, 'product_name': name.strip(), 'project_id': project_id.strip(),
                       'product_id': product_id.strip(), 'design_version': design.strip(),
                       'phase': phase, 'free_description': description}
            updated = set_components(updated, new_comp)
            facts = (material, transparency, color, capacity)
            for key, value in zip(SCOPE_FIELDS, facts):
                blank = value in ('Não informado', '')
                updated = upsert_fact(updated, key, None if blank else value,
                                      status='AUSENTE' if blank else ('CONFIRMADO' if confirmed else 'DECLARADO'),
                                      applicability='DESCONHECIDA' if blank else 'SIM',
                                      evidence_ids=[source] if confirmed and source != 'Sem documento' and not blank else [],
                                      reviewer=reviewer if confirmed and not blank else '',
                                      unit='mL' if key == 'capacidade_ml' else '')
            commit(updated, 'Embalagem atualizada. Dados básicos registrados como ' + ('confirmados.' if confirmed else 'declarados.'))
        except (ValueError, KeyError) as exc:
            st.error(f'Não foi possível salvar: {exc}')
    st.caption('A presença e a ausência dos componentes são informadas pela pessoa usuária; o protótipo não exige automaticamente evidência documental para esse inventário.')


def _information(case: dict, commit):
    st.subheader('2. Adicionar informações técnicas')
    st.write('Você pode enviar uma ficha técnica ou registrar informações manualmente. Nenhum dado extraído é confirmado automaticamente.')
    a, b = st.tabs(['Enviar ficha técnica PDF', 'Preencher manualmente'])
    with a:
        render_document_ai(case, commit)
        st.caption('PDF pesquisável, até 12 MB e 35 páginas. PDFs digitalizados sem texto exigem OCR, ainda não implementado. O PDF original não é armazenado.')
    with b:
        st.markdown('#### Registrar um dado técnico')
        target_field = st.session_state.pop('v04_target_field', None)
        if target_field in FIELDS:
            st.session_state.v04_manual_field = target_field
            st.info(f'Você veio de um resultado pendente. Confira o campo: {pretty_field(target_field)}.')
        key = st.selectbox('O que você deseja informar?', sorted(FIELDS),
                           format_func=lambda x: f"{pretty_field(x)} · {FIELDS[x]['regras']}", key='v04_manual_field')
        old = _fact(case, key)
        with st.form(f'manual_v04_{key}'):
            raw = st.text_input('Valor', value=str(old['value']) if old and old.get('value') is not None else '',
                                help=f"Formato/valor esperado: {FIELDS[key].get('dominio', '')}")
            unit = st.text_input('Unidade (quando aplicável)', value=old.get('unit') or '' if old else '')
            choices = ['Sem documento'] + [d['id'] for d in case['documents']]
            source = st.selectbox('Fonte documental (opcional)', choices)
            reviewer = st.text_input('Responsável pela confirmação (se aplicável)')
            confirm = st.checkbox('Conferi pessoalmente este valor e sua base técnica.')
            st.caption('Sem confirmação explícita, o valor permanece declarado e não comprova compatibilidade.')
            submit = st.form_submit_button('Registrar informação', type='primary')
        if submit:
            try:
                if not raw.strip():raise ValueError('Informe o valor do campo. Para registrar ausência, utilize os estados técnicos em Avançado.')
                if confirm and not (reviewer.strip() or source != 'Sem documento'):
                    raise ValueError('Informe quem confirmou ou associe um documento existente.')
                updated = upsert_fact(case, key, raw, status='CONFIRMADO' if confirm else 'DECLARADO',
                                      evidence_ids=[source] if source != 'Sem documento' else [],
                                      reviewer=reviewer if confirm else '', unit=unit)
                commit(updated, f'Informação {pretty_field(key)} salva ' + ('e confirmada.' if confirm else 'como declarada.'))
            except ValueError as exc:st.error(f'Não foi possível registrar: {exc}')
    st.info('Para casos que exigem parâmetros especializados, abra “Avançado” no menu principal. Os campos continuam vinculados à mesma avaliação.')


def _review(case: dict, commit):
    st.subheader('3. Conferir as informações')
    st.write('Revise quais informações estão confirmadas, declaradas ou ainda ausentes. Somente valores confirmados podem fundamentar conclusões do motor.')
    counts = Counter(x['evidence_status'] for x in case['facts'])
    a, b, c = st.columns(3)
    a.metric('Confirmados', counts['CONFIRMADO'])
    b.metric('Declarados', counts['DECLARADO'])
    c.metric('Documentos', len(case['documents']))
    if case['facts']:
        rows = []
        for x in sorted(case['facts'], key=lambda x: x['key']):
            rows.append({'Informação': pretty_field(x['key']), 'Valor': str(x.get('value', '—')),
                         'Estado': x['evidence_status'], 'Origem': ', '.join(x.get('evidence_ids', [])) or 'Não vinculada',
                         'Revisor': x.get('human_confirmed_by', '') or '—'})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:st.info('Ainda não existem informações técnicas registradas. Volte para “Informações”.')
    pending = [f for f in case['facts'] if f['evidence_status'] == 'DECLARADO' and f.get('value') is not None]
    if pending:
        st.markdown('#### Confirmar uma informação declarada')
        selected = st.selectbox('Informação a revisar', [f['key'] for f in pending], format_func=pretty_field)
        fact = next(f for f in pending if f['key'] == selected)
        st.write(f"**Valor atual:** {fact['value']}")
        with st.form(f'confirm_v04_{selected}'):
            docs = ['Sem documento'] + [d['id'] for d in case['documents']]
            options = [x for x in fact.get('evidence_ids', []) if x in docs]
            source = st.selectbox('Documento que sustenta o dado', docs, index=docs.index(options[0]) if options else 0)
            reviewer = st.text_input('Identificação do responsável pela revisão')
            check = st.checkbox('Verifiquei o valor, seu significado e sua origem. Confirmo este dado para a avaliação.')
            submit = st.form_submit_button('Confirmar informação', type='primary')
        if submit:
            try:
                if not check:raise ValueError('A confirmação explícita é obrigatória.')
                if not reviewer.strip():raise ValueError('Identifique o responsável pela revisão.')
                updated = upsert_fact(case, selected, fact['value'], status='CONFIRMADO',
                                      evidence_ids=[source] if source != 'Sem documento' else [],
                                      reviewer=reviewer, unit=fact.get('unit') or '', observation=fact.get('observation',''))
                commit(updated, f'{pretty_field(selected)} confirmado após revisão humana.')
            except ValueError as exc:st.error(str(exc))
    st.markdown('#### Fontes registradas')
    if case['documents']:
        for d in case['documents']:
            with st.expander(f"{d['id']} · {d['filename']}"):
                st.write('**Origem:**', d.get('source_type', '—'))
                st.write('**Localização:**', d.get('locator','Não registrada'))
                st.write('**Hash SHA-256:**', d.get('sha256','Não registrado'))
                st.caption('O arquivo PDF original não é armazenado no histórico; guarde-o separadamente.')
    else:st.caption('Nenhum documento foi registrado. Um responsável técnico identificado pode confirmar informações declaradas; isso não equivale a uma evidência documental.')


def _rule_detail(r: dict, *, prefix: str = ''):
    rid = r['rule_id']
    title = RULES.get(rid, {}).get('Título v0.3', rid)
    st.markdown(f"**O que encontramos:** {r.get('reason', '') or 'Sem informação suficiente.'}")
    if r.get('missing'):
        st.markdown('**Dados a confirmar:** ' + '; '.join(pretty_field(x) for x in r['missing']) + '.')
        st.caption('Chaves técnicas: ' + ', '.join(r['missing']))
        editable = next((key for key in r['missing'] if key in FIELDS), None)
        if editable and st.button('Informar um dado pendente desta regra', key=f'edit_rule_v04_{rid}'):
            st.session_state.v04_target_field = editable
            stage(1)
    st.markdown('**O que fazer:**')
    for x in r.get('recommendations', []):st.write(x)
    st.write(RULES.get(rid, {}).get('Recomendação de ecodesign', 'Consultar a matriz.'))
    st.markdown('**Por que importa / limitações:**')
    st.write(RULES.get(rid, {}).get('Ressalva / limite', 'Verificar a origem e as condições da regra.'))
    if r.get('evidence_ids'):
        st.write('**Evidências relacionadas:** ' + ', '.join(r['evidence_ids']))
    if r.get('trial') != 'NAO_REQUERIDO':
        st.write('**Ensaio:** ' + r['trial'])
    for sid in r.get('sources', []):
        source = SOURCES.get(sid, {})
        url = source.get('URL oficial / DOI', '')
        if url.startswith('https://'):
            st.markdown(f"**Fonte:** [{sid} — {source.get('Documento',sid)}]({url}), {source.get('Versão / data','')}")
        else:st.caption('Fonte: ' + sid)


def results(case: dict, commit, current: dict | None):
    st.subheader('4. Entender os resultados')
    st.caption('A avaliação é por critérios individuais e pode ser executada com informações incompletas. Não emite classificação global ou certificação.')
    if case.get('matrix_version') != '0.3.3':
        st.error('Matriz incompatível com o motor ativo. Importe uma versão de dados válida para continuar.')
        return
    if st.button('Avaliar com os dados disponíveis', type='primary', key='run_assessment'):
        try:
            result = assess(case)
            st.session_state.assessment = result
            st.session_state.assessment_hash = fingerprint(case)
            st.session_state.assessment_stale_v04 = False
            st.success('Avaliação concluída com os dados disponíveis.')
            current = result
        except (ValueError, RuntimeError) as exc:st.error(f'Não foi possível avaliar: {exc}')
    if not current:
        st.info('Nenhum resultado atual. Avalie para identificar problemas e informações faltantes.')
        return
    if current.get('scope') == 'FORA':
        st.warning('Esta embalagem está fora do recorte de PET transparente incolor/azul-claro. Isso não significa que não seja reciclável.')
    elif current.get('scope') == 'INDETERMINADO':
        st.warning('Escopo ainda não confirmado: informe material, transparência e cor do corpo.')
    counts = Counter(r['status'] for r in current['results'])
    a, b, c, d = st.columns(4)
    a.metric('Não compatíveis', counts['NAO_COMPATIVEL'])
    b.metric('Inconclusivos', counts['INCONCLUSIVO'])
    c.metric('Compatíveis', counts['COMPATIVEL'])
    d.metric('Total de regras', len(current['results']))
    remaining = {s: counts[s] for s in ('LIMITADA', 'NAO_APLICAVEL', 'NAO_ACIONADA', 'FORA_ESCOPO') if counts[s]}
    if remaining:st.caption('Demais estados: ' + ' · '.join(f'{_status_label(k)}: {v}' for k,v in remaining.items()))
    st.info('Classe global: NÃO EMITIDA. Esses números não compõem um índice global de reciclabilidade.')
    incompatible = [r for r in current['results'] if r['status'] == 'NAO_COMPATIVEL']
    inconclusive = [r for r in current['results'] if r['status'] == 'INCONCLUSIVO']
    st.markdown('### Prioridades para revisão do design')
    if incompatible:
        for r in incompatible:
            with st.expander(f"Não compatível · {r['rule_id']} — {RULES[r['rule_id']]['Título v0.3']}", expanded=False):
                _rule_detail(r)
    else:st.success('Nenhuma incompatibilidade identificada nos critérios avaliados. Isso não comprova reciclabilidade integral.')
    st.markdown('### Informações e validações pendentes')
    if inconclusive:
        for r in inconclusive:
            with st.expander(f"Inconclusivo · {r['rule_id']} — {RULES[r['rule_id']]['Título v0.3']}"):
                _rule_detail(r)
    else:st.caption('Nenhuma regra inconclusiva neste relatório.')
    trials = [r['rule_id'] for r in current['results'] if r.get('trial') in ('PENDENTE', 'REQUERIDO')]
    measurements = measurements_pending(current)
    if trials:st.warning('Ensaios pendentes/requeridos: ' + ', '.join(trials))
    if measurements:
        with st.expander(f'Medições ou protocolos a confirmar ({len(measurements)})'):
            st.dataframe(pd.DataFrame(measurements), hide_index=True, use_container_width=True)
    st.caption('Ensaios, medições e métodos normativos pendentes são conceitos distintos. A ausência de ensaio requerido não elimina as outras pendências.')
    with st.expander('Ver todas as 15 regras e suas referências'):
        st.dataframe(pd.DataFrame([{'Regra': x['rule_id'],
                                    'Critério': RULES[x['rule_id']]['Título v0.3'],
                                    'Resultado': _status_label(x['status'])}
                                   for x in current['results']]),hide_index=True,use_container_width=True)
        rules_by_id = {x['rule_id']: x for x in current['results']}
        selected_id = st.selectbox('Detalhar uma regra',list(rules_by_id),
                                   format_func=lambda rid: f"{rid} — {RULES[rid]['Título v0.3']}",
                                   key='v04_detail_rule')
        _rule_detail(rules_by_id[selected_id])
    st.download_button('Exportar relatório de avaliação (.json)',
                       data=json.dumps(current, indent=2, ensure_ascii=False).encode('utf-8'),
                       file_name=f"pet_circular_{case['product_id']}_resultado.json", mime='application/json',
                       key='v04_download_report')
    st.divider()
    st.markdown('### Perguntar ao assistente sobre estes resultados')
    render_assistant(case, current)


def _report_selection():
    import_mode = st.radio('Como deseja selecionar as duas avaliações?',
                           ['Enviar relatórios de avaliação (.json)', 'Usar avaliações salvas', 'Experimentar dados demonstrativos'],
                           key='v04_comparison_source')
    if import_mode == 'Enviar relatórios de avaliação (.json)':
        a, b = st.columns(2)
        with a:
            left = st.file_uploader('Relatório anterior — Design A', type=['json'], key='compare_json_a_v04')
        with b:
            right = st.file_uploader('Relatório proposto — Design B', type=['json'], key='compare_json_b_v04')
        if not left or not right:return None, None
        return parse_report(left.getvalue()), parse_report(right.getvalue())
    if import_mode == 'Usar avaliações salvas':
        history = [(item, report) for item, report in storage.report_history()]
        if len(history) < 2:
            st.info('Ainda não há duas avaliações salvas com resultado. Salve cada avaliação em Projetos ou envie relatórios JSON.')
            return None, None
        labels = [f"#{it['id']} · {it['product_name']} · {it['design_version']} ({it['saved_at']})" for it,_ in history]
        a, b = st.columns(2)
        with a:i = st.selectbox('Avaliação anterior (A)', range(len(labels)), format_func=lambda x: labels[x], index=min(1,len(labels)-1))
        with b:j = st.selectbox('Avaliação proposta (B)', range(len(labels)), format_func=lambda x: labels[x], index=0)
        return history[i][1], history[j][1]
    a = json.loads((BASE / 'examples/integrated/Design_A_Resultado_Esperado.json').read_text(encoding='utf-8'))
    b = json.loads((BASE / 'examples/integrated/Design_B_Resultado_Esperado.json').read_text(encoding='utf-8'))
    st.info('Demonstração: resultados fictícios dos Designs A e B. Não representam avaliações de embalagens reais.')
    return a, b


def comparison():
    st.title('Comparar designs')
    st.write('Selecione duas avaliações já executadas. A comparação utiliza os relatórios gerados pelo motor, não inferências da IA.')
    try:
        a, b = _report_selection()
    except (ValueError, OSError) as exc:
        st.error(f'Não foi possível ler a avaliação: {exc}')
        return
    if a is None or b is None:return
    st.markdown(f"**A — Original:** {a.get('product_name','')} · `{a.get('design_version','')}`")
    st.markdown(f"**B — Proposto:** {b.get('product_name','')} · `{b.get('design_version','')}`")
    cross_id = a['product_id'] != b['product_id']
    related = True
    if cross_id:
        related = st.checkbox('Confirmo que os relatórios representam designs comparáveis do mesmo projeto.', key='v04_compare_relation')
    if a['matrix_version'] != b['matrix_version'] or a['engine_version'] != b['engine_version']:
        st.error('As avaliações usam versões diferentes da matriz ou do motor. Comparação interpretativa bloqueada para evitar conclusões incorretas.')
        st.caption(f"A: matriz {a['matrix_version']}, motor {a['engine_version']} · B: matriz {b['matrix_version']}, motor {b['engine_version']}")
        return
    try:
        report = compare_reports(a, b)
    except ValueError as exc:
        st.warning(str(exc));return
    if cross_id and not related:
        st.warning('Confirme a relação entre os designs para visualizar a análise comparativa.')
        return
    if report['warnings']:
        for warning in report['warnings']:st.caption('Atenção: ' + warning)
    counts = report['counts']
    a1, b1, c1 = st.columns(3)
    a1.metric('Passaram a compatíveis', counts.get('criterio_favoravel',0))
    b1.metric('Ainda inconclusivo após incompatibilidade', counts.get('ainda_pendente',0))
    c1.metric('Pendências persistentes', counts.get('pendencia_persistente',0))
    if counts.get('novo_problema'):
        st.error(f"{counts['novo_problema']} nova(s) incompatibilidade(s) identificada(s) no Design B.")
    st.info('A ausência de incompatibilidade no Design B não significa que a embalagem esteja aprovada ou reciclável.')
    key_groups = [
        ('Mudanças com compatibilidade no B', ('criterio_favoravel','pendencia_sanada')),
        ('Ainda dependem de comprovação', ('ainda_pendente','pendencia_persistente')),
        ('Novas incompatibilidades', ('novo_problema',)),
        ('Outras transições e critérios mantidos', ('sem_mudanca',)),
    ]
    for heading, kinds in key_groups:
        selected = [r for r in report['changes'] if r['category'] in kinds]
        if not selected:continue
        with st.expander(f'{heading} ({len(selected)})',expanded=heading!='Outras transições e critérios mantidos'):
            for entry in selected:
                with st.container(border=True):
                    rid = entry['rule_id']
                    st.markdown(f"**{rid} — {RULES[rid]['Título v0.3']}**")
                    st.write(f"A: **{_status_label(entry['status_a'])}** → B: **{_status_label(entry['status_b'])}**")
                    st.write(entry['description'])
                    if entry['missing_a'] or entry['missing_b']:
                        st.caption('Pendente em A: ' + (', '.join(pretty_field(x) for x in entry['missing_a']) or 'nenhum'))
                        st.caption('Pendente em B: ' + (', '.join(pretty_field(x) for x in entry['missing_b']) or 'nenhum'))
                    if entry['evidence_a'] or entry['evidence_b']:
                        st.caption('Evidências A: ' + (', '.join(entry['evidence_a']) or 'não identificadas') +
                                   ' · Evidências B: ' + (', '.join(entry['evidence_b']) or 'não identificadas'))
    st.caption(report['method_note'])
    st.download_button('Exportar comparação (.json)',
                       data=json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'),
                       file_name=f"pet_circular_comparacao_{a['product_id']}_vs_{b['product_id']}.json",
                       mime='application/json', key='v04_comparison_export')


def _case_preview(case: dict):
    st.markdown(f"**{case['product_name']}** · `{case['product_id']}` · versão `{case.get('design_version','v1')}`")
    st.caption(f"{len(case['facts'])} informações técnicas · {known_components(case)} de 11 componentes com presença definida · {len(case['documents'])} documentos")


def import_project(case: dict, replace_case, dirty: bool):
    st.markdown('### Importar dados de um projeto')
    st.caption('Aceita JSON de entrada do produto, não o relatório de avaliação. Confira a prévia antes de substituir o projeto ativo.')
    uploaded = st.file_uploader('Arquivo de dados do projeto (.json)', type=['json'], key='v04_project_import')
    if not uploaded:return
    try:
        new_case = import_case(uploaded.getvalue())
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        st.error(f'Arquivo incompatível: {exc}');return
    left, right = st.columns(2)
    with left:
        st.markdown('**Projeto atual**'); _case_preview(case)
    with right:
        st.markdown('**Projeto a importar**'); _case_preview(new_case)
    st.warning('A importação substituirá o projeto ativo na sessão. Os dados anteriores só poderão ser retomados se tiverem sido salvos/exportados.')
    approved = st.checkbox('Conferi a identificação e quero substituir o projeto ativo.', key='v04_import_confirm')
    if dirty:
        st.error('Existem alterações não salvas no projeto ativo. Salve em Projetos antes de prosseguir, se quiser preservá-las.')
    if st.button('Substituir produto ativo', type='primary', disabled=not approved,
                 key='v04_confirm_project_import'):
        replace_case(new_case, None, f"Importação concluída: {new_case['product_name']} · {len(new_case['facts'])} informações técnicas.", False)
        go('Avaliação', 0)


def projects(case: dict, current: dict | None, replace_case, dirty: bool):
    st.title('Projetos e versões')
    _project_context(case, current)
    st.caption('Snapshots ficam no SQLite do computador/servidor que executa o aplicativo. Não há sincronização na nuvem e os PDFs originais não são arquivados.')
    if dirty:
        st.warning('Existem alterações não salvas. Salve um snapshot antes de trocar de projeto ou fechar o aplicativo.')
    a, b = st.columns(2)
    with a:
        if st.button('Salvar snapshot deste projeto', type='primary', use_container_width=True, key='v04_save_snapshot'):
            try:
                sid = storage.save(case, current)
                st.session_state.saved_hash_v04 = fingerprint(case)
                st.success(f'Versão #{sid} salva neste computador/servidor.')
            except (OSError, ValueError) as exc:
                st.error(f'Não foi possível salvar: {exc}')
    with b:
        st.download_button('Exportar dados do projeto (.json)', data=json.dumps(case,ensure_ascii=False,indent=2).encode('utf-8'),
                           file_name=f"pet_circular_{case['product_id']}_entrada.json",mime='application/json',
                           use_container_width=True,key='v04_export_product')
    with st.expander('Criar uma embalagem nova'):
        st.write('O projeto atual será substituído na sessão. Confirme antes de continuar.')
        if st.button('Preparar novo projeto', key='v04_prepare_new'):
            st.session_state.new_project_confirmation_v04 = True
        if st.session_state.get('new_project_confirmation_v04'):
            if dirty:st.warning('Dados atuais não salvos: a ação não poderá ser desfeita sem exportação ou snapshot.')
            if st.button('Confirmar criação de projeto vazio', type='primary', key='v04_confirm_new'):
                replace_case(fresh(), None, 'Novo projeto criado. Os dados anteriores não foram modificados no histórico salvo.', False)
                go('Avaliação', 0)
    with st.expander('Importar um projeto existente'):
        import_project(case, replace_case, dirty)
    st.markdown('### Versões salvas')
    try:
        records = storage.history(limit=100)
    except (OSError, ValueError) as exc:
        st.error(f'Histórico indisponível: {exc}');return
    if not records:
        st.info('Nenhum snapshot salvo. Salve uma versão ou importe um JSON para começar.')
        return
    options = [f"#{r['id']} · {r['product_name']} · {r['design_version']} · {r['saved_at']}" for r in records]
    chosen = st.selectbox('Selecione uma versão salva', range(len(options)),format_func=lambda x: options[x])
    record = records[chosen]
    st.caption(f"Projeto: {record['project_id']} · Produto: {record['product_id']} · {'Com avaliação' if record['has_result'] else 'Sem avaliação'}")
    approve = st.checkbox('Confirmo que quero abrir esta versão e substituir o projeto ativo.',key='v04_open_confirm')
    if dirty:st.warning('A abertura substituirá alterações não salvas no projeto ativo.')
    if st.button('Abrir versão selecionada', disabled=not approve,key='v04_open_snapshot'):
        try:
            product, report = storage.load(record['id'])
            validate(product)
            replace_case(product, report, f"Versão #{record['id']} carregada.", True)
            go('Avaliação', 3 if report else 0)
        except (ValueError, OSError) as exc:st.error(f'Não foi possível carregar: {exc}')
