"""Interface de perguntas e respostas sobre o resultado corrente."""
from __future__ import annotations

import os

import streamlit as st
from ecodesign_assistant import llm_answer, offline_answer
from pet_circular.engine import assess
from ui_helpers import fingerprint


def render_assistant(case: dict, assessment: dict | None = None) -> None:
    st.subheader('Assistente de ecodesign')
    st.caption('Explica regras e resultados da matriz v0.3.3, sem substituir o motor técnico.')
    if assessment is None:
        st.info('A avaliação será calculada a partir dos dados atuais do produto para fundamentar a conversa.')
        assessment = assess(case)
    current_hash = fingerprint(case)
    if st.session_state.get('assistant_case_hash') != current_hash:
        st.session_state.assistant_messages = []
        st.session_state.assistant_case_hash = current_hash
    if assessment.get('summary', {}).get('incompatibilities_confirmed'):
        st.error('Incompatibilidades registradas: ' + ', '.join(assessment['summary']['incompatibilities_confirmed']))
    st.warning('Classe global não emitida. Respostas da IA não alteram fatos, regras nem classificações.')
    mode = st.radio('Modo de explicação', ['Local — rastreável, sem API', 'IA — OpenAI API'], horizontal=True)
    api_key = None
    model = 'gpt-4.1-mini'
    consent = False
    if mode.startswith('IA'):
        api_key = st.text_input('Chave da API (ou variável OPENAI_API_KEY)',type='password',value='',help='Chave usada somente para esta chamada. Não é armazenada no banco SQLite.') or os.environ.get('OPENAI_API_KEY','')
        model = st.text_input('Modelo',value='gpt-4.1-mini')
        consent = st.checkbox('Autorizo enviar a pergunta, o resumo do produto e os critérios relacionados à API externa.')
        st.caption('A API não recebe o PDF original. Há possível cobrança por uso. Evite conteúdo confidencial sem autorização.')
    for msg in st.session_state.assistant_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('sources'):
                with st.expander('Referências vinculadas às regras'):
                    for src in msg['sources']:
                        st.markdown(f"- [{src['id']} — {src['title']}]({src['url']}) ({src['version']})")
    prompt = st.chat_input('Ex.: Por que o sleeve pode ser incompatível? O que falta confirmar?')
    if prompt:
        st.session_state.assistant_messages.append({'role':'user','content':prompt})
        with st.chat_message('user'):
            st.markdown(prompt)
        with st.chat_message('assistant'):
            try:
                if mode.startswith('IA'):
                    if not consent: raise ValueError('Marque o consentimento antes de enviar informações à API.')
                    result = llm_answer(prompt,assessment,api_key or '',model)
                else:result = offline_answer(prompt,assessment)
                st.markdown(result['answer'])
                if result.get('disclaimer'):st.caption(result['disclaimer'])
                if result['sources']:
                    with st.expander('Referências vinculadas às regras'):
                        for src in result['sources']:
                            st.markdown(f"- [{src['id']} — {src['title']}]({src['url']}) ({src['version']})")
                st.session_state.assistant_messages.append({'role':'assistant','content':result['answer'],'sources':result['sources']})
            except Exception as exc:
                st.error(f'Não foi possível responder: {type(exc).__name__}: {exc}')
