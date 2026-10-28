"""Página Streamlit: upload, proposta de extração e validação humana."""
from __future__ import annotations
import hashlib
import json
import os
from copy import deepcopy

import streamlit as st

from document_ai import DocumentText, llm_candidates, local_candidates, read_pdf_bytes, review_apply
from ui_helpers import fields_catalog, upsert_document
from pet_circular.engine import validate


def render_document_ai(case, commit):
    st.subheader('Leitura inteligente de documentos')
    st.write('Envie uma ficha técnica em PDF. O sistema propõe campos com **trecho literal e página**; '
             'nenhum valor será confirmado nem enviado ao motor antes de tua revisão explícita.')
    st.info('Modo **local:** extrai campos rotulados por padrões, sem IA e sem transmitir texto. '
            'Modo **IA:** usa a API OpenAI com tua autorização e credencial própria. '
            'A API pode ter custos independentes do ChatGPT.')
    pending=st.session_state.get('doc_ai_review')
    if pending and pending.get('product_id') != case['product_id']:
        del st.session_state['doc_ai_review'];pending=None
    if not pending:
        epoch=st.session_state.form_epoch
        uploaded=st.file_uploader('Ficha técnica (PDF com texto pesquisável, até 12 MB e 35 páginas)',
                                  type=['pdf'],key=f'ai_pdf_upload_{epoch}')
        n=1
        existing={d['id'] for d in case['documents']}
        while f'DOC{n:02d}' in existing:n+=1
        a,b=st.columns(2)
        with a:
            doc_id=st.text_input('ID da nova evidência',value=f'DOC{n:02d}',key=f'ai_doc_id_{epoch}')
            version=st.text_input('Versão/data do documento (opcional)',key=f'ai_doc_version_{epoch}')
        with b:
            mode=st.radio('Método de extração',['Local — padrões explícitos','IA — OpenAI API'],key='ai_method')
            if mode.startswith('IA'):
                model=st.text_input('Modelo configurado na API',value='gpt-4.1-mini',key='ai_model')
                key=st.text_input('Chave OpenAI API (não salva)',type='password',key='ai_api_key',
                                  help='Também pode ser definida pela variável OPENAI_API_KEY no computador.')
                consent=st.checkbox('Autorizo enviar o texto extraído deste PDF à API OpenAI para análise.',key='ai_consent')
                st.caption('Somente o texto extraído é enviado, não o arquivo PDF. Não utilize documentos sigilosos sem autorização.')
        if st.button('Ler PDF e propor dados',type='primary',disabled=uploaded is None,key='extract_pdf'):
            try:
                if not doc_id.strip():raise ValueError('Informe o ID da evidência.')
                if uploaded is None:raise ValueError('Selecione um PDF.')
                doc=read_pdf_bytes(uploaded.getvalue(),uploaded.name)
                prior=next((x for x in case['documents'] if x['id']==doc_id.strip()),None)
                if prior and prior.get('sha256') != doc.digest:
                    raise ValueError('O ID já pertence a outro documento. Escolha um identificador novo.')
                if mode.startswith('IA'):
                    if not consent:raise ValueError('A transmissão à API exige autorização explícita.')
                    token=key.strip() or os.getenv('OPENAI_API_KEY','')
                    if not token:raise ValueError('Configure a chave da API ou utilize o modo local.')
                    with st.spinner('Consultando a API para extrair candidatos...'):
                        candidates,rejected=llm_candidates(doc,token,model.strip())
                    method='IA_API'
                else:
                    candidates=local_candidates(doc)
                    rejected=[]
                    method='LOCAL'
                metadata={'id':doc_id.strip(),'filename':uploaded.name,'source_type':'upload',
                          'sha256':doc.digest,'version':version.strip(),
                          'locator':f'páginas 1–{doc.total_pages}',
                          'notes':'PDF carregado para extração. Arquivo original não persistido.'}
                new_case=upsert_document(case,metadata)
                validate(new_case)
                for candidate in candidates:
                    candidate['doc_id']=doc_id.strip()
                st.session_state['doc_ai_review']={
                    'product_id':case['product_id'],'design_version':case['design_version'],
                    'doc_id':doc_id.strip(),'filename':uploaded.name,'digest':doc.digest,
                    'method':method,'candidates':candidates,'rejected':rejected,
                    'truncated':doc.truncated,'pages':doc.total_pages}
                commit(new_case,'Documento identificado e candidatos prontos para revisão.',clear_extraction=False)
            except Exception as exc:
                # Falha externa ou em leitura não altera produto nem confirma dados.
                st.error(f'Não foi possível realizar a extração: {exc}')
        return

    st.success(f"Documento registrado: **{pending['filename']}** · ID **{pending['doc_id']}** · páginas: {pending['pages']}")
    st.caption('Origem: '+('IA via API OpenAI' if pending['method']=='IA_API' else 'Parser local sem IA'))
    if pending['truncated']:
        st.warning('O texto ultrapassou o limite de leitura e foi truncado. Inspecione o documento integralmente antes de confirmar qualquer dado.')
    if pending['rejected']:
        st.warning(f"{len(pending['rejected'])} proposta(s) da IA foram descartadas por falta de citação verificável ou por formato inválido.")
        with st.expander('Detalhes dos descartes'):
            for reason in pending['rejected']:st.write(reason)
    candidates=pending['candidates']
    if not candidates:
        st.warning('Nenhum valor técnico seguro foi encontrado. O documento continua registrado, mas nenhum dado foi acrescentado. '
                   'Preencha os campos manualmente em Dados técnicos ou use um PDF com informações rotuladas.')
        if st.button('Concluir e analisar outro PDF',key='clear_ai_no_candidates'):
            st.session_state.pop('doc_ai_review',None);st.rerun()
        return
    st.write(f'**{len(candidates)} candidatos pendentes de revisão humana.**')
    existing={f['key']:f for f in case['facts']}
    field_catalog=fields_catalog()
    review_key=f"{st.session_state.form_epoch}_{pending['digest'][:12]}"
    with st.form(f'ai_review_form_{review_key}'):
        reviewer=st.text_input('Responsável pela revisão técnica (obrigatório para confirmar)',placeholder='Nome ou identificação',key=f'reviewer_{review_key}')
        agree=st.checkbox('Li as evidências de cada item selecionado e confirmo os valores para este produto.',value=False,key=f'agree_{review_key}')
        decisions=[]
        for i,c in enumerate(candidates):
            with st.container(border=True):
                label=field_catalog.get(c['key'],{}).get('regras','')
                st.markdown(f"**{c['key']}** · página {c['page']} · regras: {label}")
                st.code(c['quote'],language=None)
                l,r=st.columns([1,2])
                with l:
                    accept=st.checkbox('Aprovar este dado',value=False,key=f'accept_{review_key}_{i}')
                    prior=existing.get(c['key'])
                    overwrite=False
                    if prior and prior['evidence_status']=='CONFIRMADO':
                        st.warning('Já existe valor confirmado para este campo.')
                        overwrite=st.checkbox('Substituir o valor confirmado',value=False,key=f'overwrite_{review_key}_{i}')
                with r:
                    value=st.text_input('Valor proposto (corrigir se necessário)',value=str(c['value']),key=f'value_{review_key}_{i}')
                    st.caption(f"Unidade sugerida: {c['unit'] or '—'} · modo {c['method']}")
                decisions.append({'accept':accept,'overwrite':overwrite,'value':value})
        submitted=st.form_submit_button('Confirmar selecionados e atualizar o produto',type='primary')
    if submitted:
        try:
            if not agree:raise ValueError('Confirmação humana explícita é obrigatória.')
            if not any(d['accept'] for d in decisions):raise ValueError('Selecione ao menos um candidato para aprovar.')
            if case['design_version']!=pending['design_version']:
                raise ValueError('A versão do design mudou; reenvie o documento.')
            new_case, applied, skipped=review_apply(case,pending['doc_id'],candidates,decisions,reviewer)
            if not applied:
                raise ValueError('Nenhum dado pôde ser importado. '+'; '.join(skipped))
            commit(new_case,f"{len(applied)} campo(s) confirmado(s): {', '.join(applied)}. " + ('; '.join(skipped) if skipped else ''))
        except ValueError as exc:
            st.error(str(exc))
    c1,c2=st.columns(2)
    with c1:
        st.download_button('Exportar propostas (.json)',data=json.dumps({
            'document_sha256':pending['digest'],'candidates':candidates},ensure_ascii=False,indent=2).encode('utf-8'),
            file_name='pet_circular_propostas_extracao.json',mime='application/json')
    with c2:
        if st.button('Descartar propostas e analisar outro PDF'):
            st.session_state.pop('doc_ai_review',None)
            st.rerun()
