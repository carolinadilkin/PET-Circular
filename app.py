"""PET Circular — Streamlit com extração opcional, revisão humana e motor v0.1.

Rodar: streamlit run app.py
Sem classificação global nem certificação automática.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

import pandas as pd
import streamlit as st

import storage
from document_ai import measurements_pending
from ui_document_ai import render_document_ai
from ui_assistant import render_assistant
from pet_circular.engine import assess, validate
from ui_helpers import (
    APPLICABILITY, EVIDENCE, KIND_LABELS, KINDS, PRESENCE, STATUSES,
    example, fields_catalog, fingerprint, fresh, import_case, missing,
    parse_value, remove_document, remove_fact, rows, rule_catalog,
    set_components, source_catalog, upsert_document, upsert_fact
)

st.set_page_config(page_title='PET Circular | Ecodesign', page_icon='♻', layout='wide',
                   initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1300px}
[data-testid="stMetric"]{border:1px solid #dfe9e3;padding:14px;border-radius:12px;background:white}
[data-testid="stSidebar"]{border-right:1px solid #e2ebe6}
.small-caption{color:#587468;font-size:0.87rem}
.site-kicker{font-weight:700;letter-spacing:0.12em;text-transform:uppercase;font-size:0.75rem;color:#187763}
</style>''',unsafe_allow_html=True)

FIELDS=fields_catalog()
RULES=rule_catalog()
SOURCES=source_catalog()
MATRIX_VERSION='0.3.3'
PAGES=['Visão geral','Produto','Componentes','Dados técnicos','Evidências','IA · Documentos','Avaliação','Assistente de ecodesign']

if 'case' not in st.session_state:st.session_state.case=example()
if 'assessment' not in st.session_state:st.session_state.assessment=None
if 'assessment_hash' not in st.session_state:st.session_state.assessment_hash=None
if 'form_epoch' not in st.session_state:st.session_state.form_epoch=0
if 'last_message' not in st.session_state:st.session_state.last_message=None


def commit(case,notice='Informações atualizadas.',clear_extraction=True):
    validate(case)
    st.session_state.case=case
    if clear_extraction:st.session_state.pop('doc_ai_review',None)
    st.session_state.assessment=None
    st.session_state.assessment_hash=None
    st.session_state.form_epoch+=1
    st.session_state.last_message=notice
    st.rerun()


def reset(case,message):
    validate(case)
    st.session_state.pop('doc_ai_review',None)
    st.session_state.case=case
    st.session_state.assessment=None
    st.session_state.assessment_hash=None
    st.session_state.form_epoch+=1
    st.session_state.last_message=message
    st.rerun()


def error_message(exc):
    st.error(str(exc))


def current_result():
    result=st.session_state.assessment
    if result and st.session_state.assessment_hash==fingerprint(st.session_state.case):
        return result
    return None


def fact_by_key(key):
    for f in reversed(st.session_state.case['facts']):
        if f['key']==key:return f
    return None


# Barra lateral — navegação, importação, snapshots e exportação
with st.sidebar:
    st.markdown('<div class="site-kicker">PET CIRCULAR</div>',unsafe_allow_html=True)
    st.title('Ecodesign Studio')
    st.caption('Prova de conceito · matriz v0.3.3 · motor v0.1 · extração IA opcional')
    st.divider()
    page=st.radio('Navegação',PAGES, key='navigation')
    st.divider()
    st.markdown('**Casos de avaliação**')
    if st.button('Carregar piloto Patrico',use_container_width=True,key='load_patrico'):
        reset(example(),'Piloto documental Patrico restaurado.')
    if st.button('Criar produto novo',use_container_width=True,key='new_case'):
        reset(fresh(),'Novo produto criado.')
    with st.expander('Importar envelope JSON'):
        uploaded_json=st.file_uploader('Arquivo JSON',type=['json'],key='case_upload')
        if st.button('Importar',disabled=uploaded_json is None,key='import_case_button'):
            try:
                imported = import_case(uploaded_json.getvalue())
                reset(imported, (
                    f"Importação confirmada: {imported['product_name']} "
                    f"[ID: {imported['product_id']}] · "
                    f"{len(imported['facts'])} fatos, {len(imported['components'])} componentes."
                ))
            except (ValueError,UnicodeError,json.JSONDecodeError) as ex:error_message(ex)
    active = st.session_state.case
    st.caption(f"Caso ativo: `{active['product_id']}` · {len(active['facts'])} fatos · {len(active['components'])} componentes")
    if not active['facts']:
        st.warning('Nenhum fato técnico registrado neste produto. Verifique se a importação JSON foi concluída antes de avaliar.')
    st.download_button('Exportar dados do produto (.json)',
        data=json.dumps(st.session_state.case,indent=2,ensure_ascii=False).encode('utf-8'),
        file_name=f"pet_circular_{st.session_state.case['product_id']}_input.json",
        mime='application/json',use_container_width=True,key='download_input')
    st.divider()
    st.markdown('**Histórico local**')
    try:
        saved=storage.latest()
        if saved:
            choices={f"#{x['id']} · {x['product_name']} ({x['design_version']})":x['id'] for x in saved}
            saved_label=st.selectbox('Casos salvos',list(choices),key='saved_select')
            if st.button('Abrir snapshot',use_container_width=True,key='open_snapshot'):
                product,result=storage.load(choices[saved_label])
                st.session_state.case=product
                st.session_state.pop('doc_ai_review',None)
                st.session_state.assessment=result
                st.session_state.assessment_hash=fingerprint(product) if result else None
                st.session_state.form_epoch+=1
                st.session_state.last_message='Snapshot recuperado.'
                st.rerun()
        else:st.caption('Nenhum snapshot salvo.')
        if st.button('Salvar snapshot',use_container_width=True,key='save_snapshot'):
            snapshot_id=storage.save(st.session_state.case,current_result())
            st.success(f'Snapshot #{snapshot_id} salvo no SQLite local.')
    except (OSError,ValueError,Exception) as ex:
        # Problemas de disco não devem impedir a avaliação em memória.
        st.warning(f'Histórico local indisponível: {ex}')
    st.caption('Dados salvos apenas no computador/servidor que executa o app. PDFs carregados não são arquivados.')

case=st.session_state.case
if st.session_state.last_message:
    st.success(st.session_state.last_message)
    st.session_state.last_message=None

st.markdown('<div class="site-kicker">PROTÓTIPO FUNCIONAL • AVALIAÇÃO TÉCNICA ASSISTIDA</div>',unsafe_allow_html=True)
st.title('PET Circular')
st.caption(f"Produto ativo: **{case['product_name']}** · ID `{case['product_id']}` · **{len(case['facts'])}** fatos técnicos")
st.caption('Compatibilidade de design para garrafas PET transparentes incolores ou azul-claras.')
st.info('Este protótipo não emite classe global de reciclabilidade, laudo nem certificação RecyClass. Informações declaradas ou propostas não são tratadas como confirmadas.')

if page=='Visão geral':
    st.subheader('Visão geral do projeto')
    st.write(f"**{case['product_name']}** · Código `{case['product_id']}` · Versão de design `{case.get('design_version','—')}`")
    ready=current_result()
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Fatos registrados',len(case['facts']))
    c2.metric('Documentos registrados',len(case['documents']))
    c3.metric('Componentes conhecidos',sum(c['presence']!='DESCONHECIDA' for c in case['components']))
    c4.metric('Regras avaliadas',len(ready['results']) if ready else 0)
    st.markdown('#### Caminho de avaliação')
    st.markdown('**1. Produto** → **2. Componentes** → **3. Dados técnicos** → **4. Evidências / IA** → **5. Revisão humana** → **6. Avaliação**')
    st.write('O app solicita fatos, separa informações ainda declaradas das confirmadas, aplica o motor de 15 regras e apresenta justificativas, lacunas e recomendações.')
    a,b=st.columns(2)
    with a:
        st.markdown('**O que está implementado**')
        st.markdown('- Edição do envelope de produto e da presença de componentes.\n- Registro de fatos com unidade, estado e evidências.\n- Avaliação individual das 15 regras.\n- Exportação JSON e histórico SQLite local.\n- Extração local de PDFs e IA opcional com revisão humana obrigatória.')
    with b:
        st.markdown('**O que ainda não está implementado**')
        st.markdown('- OCR de PDFs escaneados e armazenamento seguro de originais.\n- Balanço gravimétrico integral no Python.\n- Homologação de cobertura PET-04 e compactação PET-16.\n- Classe global e certificação.')
    if ready:
        st.divider()
        st.markdown('#### Última avaliação')
        counts=Counter(r['status'] for r in ready['results'])
        st.write(f"**Incompatibilidades confirmadas:** {counts['NAO_COMPATIVEL']} · **Inconclusivas:** {counts['INCONCLUSIVO']} · **Compatíveis por critério:** {counts['COMPATIVEL']}")
        st.caption('Classe global: NÃO EMITIDA.')

elif page=='Produto':
    st.subheader('Cadastro e contexto do produto')
    st.caption('O identificador do produto e a versão de design permitem comparar avaliações ao longo do desenvolvimento.')
    with st.form('product_form'):
        a,b=st.columns(2)
        with a:
            name=st.text_input('Nome do produto',value=case['product_name'])
            product_id=st.text_input('Código do produto',value=case['product_id'])
            phase=st.selectbox('Fase do desenvolvimento',['projeto_definido','ideacao'],index=['projeto_definido','ideacao'].index(case['phase']),format_func=lambda x:'Produto existente' if x=='projeto_definido' else 'Ideação')
        with b:
            project_id=st.text_input('ID do projeto',value=case['project_id'])
            version=st.text_input('Versão do design',value=case.get('design_version','v1'))
            st.text_input('Versão da matriz (fixa)',value=MATRIX_VERSION,disabled=True)
        desc=st.text_area('Descrição / requisitos funcionais',value=case.get('free_description',''),height=115)
        save_product=st.form_submit_button('Salvar informações do produto',type='primary')
    if save_product:
        if not all(x.strip() for x in (name,product_id,project_id,version)):
            st.error('Preencha os identificadores obrigatórios.')
        else:
            new={**case,'product_name':name.strip(),'product_id':product_id.strip(),
                 'project_id':project_id.strip(),'phase':phase,'design_version':version.strip(),
                 'free_description':desc,'matrix_version':MATRIX_VERSION}
            try:commit(new,'Cadastro do produto salvo.')
            except ValueError as ex:error_message(ex)
    st.caption('A fase "Ideação" permite registrar propostas, mas não as transforma em fatos confirmados.')

elif page=='Componentes':
    st.subheader('Inventário de componentes')
    st.caption('Confirme explicitamente a ausência de componentes. "Desconhecida" não equivale a "Não".')
    st.warning('A versão atual do motor não exige evidência documental para presença/ausência dos componentes. Revise o inventário com o fabricante antes de considerar uma ausência como confirmada.')
    by_kind={c['kind']:c for c in case['components']}
    with st.form('component_form'):
        left,right=st.columns(2)
        changes={}
        for i,kind in enumerate(KINDS):
            with (left if i%2==0 else right):
                initial=by_kind.get(kind,{}).get('presence','DESCONHECIDA')
                changes[kind]=st.selectbox(KIND_LABELS[kind],PRESENCE,index=PRESENCE.index(initial),
                    format_func=lambda p:{'DESCONHECIDA':'Não informado','SIM':'Presente','NAO':'Ausente'}[p],
                    key=f'component_{kind}_{st.session_state.form_epoch}')
        submitted=st.form_submit_button('Salvar inventário',type='primary')
    if submitted:
        try:commit(set_components(case,changes),'Presença dos componentes atualizada.')
        except ValueError as ex:error_message(ex)
    st.caption('A avaliação de liners, válvulas e lacres ainda não cobre integralmente todas as classificações da diretriz.')

elif page=='Dados técnicos':
    st.subheader('Informações técnicas')
    st.caption('Dados somente declarados ou propostos não habilitam conclusões definitivas. Use confirmação humana ou evidência documental registrada.')
    st.markdown('#### Entrada rápida — escopo PET')
    scopes=['material_corpo','transparencia_corpo','cor_corpo','capacidade_ml']
    lookups={k:fact_by_key(k) for k in scopes}
    doc_choices=[d['id'] for d in case['documents']]
    defaults=sorted({eid for f in lookups.values() if f for eid in f.get('evidence_ids',[]) if eid in doc_choices})
    with st.form('scope_form'):
        a,b=st.columns(2)
        def index_for(keys,key):
            v=lookups[key]['value'] if lookups[key] else None
            return keys.index(v) if v in keys else 0
        with a:
            mat_options=['Não informado','PET','outro']
            material=st.selectbox('Polímero do corpo',mat_options,index=index_for(mat_options,'material_corpo'))
            transp_options=['Não informado','transparente','opaco']
            transparency=st.selectbox('Transparência',transp_options,index=index_for(transp_options,'transparencia_corpo'))
        with b:
            color_options=['Não informado','incolor','azul-claro','preta','outra']
            color=st.selectbox('Cor do corpo',color_options,index=index_for(color_options,'cor_corpo'))
            capacity=st.text_input('Capacidade nominal (mL)',value=str(lookups['capacidade_ml']['value']) if lookups['capacidade_ml'] and lookups['capacidade_ml']['value'] is not None else '')
        docs=st.multiselect('Documentos que fundamentam os quatro dados',doc_choices,default=defaults)
        reviewer=st.text_input('Responsável pela confirmação humana (opcional)',placeholder='Ex.: Eng. Responsável')
        checked=st.checkbox('Conferi pessoalmente os valores informados e confirmo sua correspondência à evidência ou ao conhecimento técnico identificado.',value=False)
        st.caption('A confirmação é explícita. Sem marcar a caixa, valores ficam DECLARADOS, mesmo com um documento vinculado. Salvar sem confirmar altera o estado anterior para DECLARADO.')
        quick_submitted=st.form_submit_button('Registrar dados de escopo',type='primary')
    if quick_submitted:
        try:
            if checked and not (docs or reviewer.strip()):
                raise ValueError('Para confirmar estes dados, indique uma evidência cadastrada ou o responsável pela revisão.')
            temp=case
            for key,val in zip(scopes,[material,transparency,color,capacity]):
                missing_value=val=='Não informado' or val==''
                actual=None if missing_value else val
                status='AUSENTE' if missing_value else ('CONFIRMADO' if checked else 'DECLARADO')
                temp=upsert_fact(temp,key,actual,status=status,
                      applicability='DESCONHECIDA' if missing_value else 'SIM',
                      evidence_ids=docs if not missing_value else [],reviewer=reviewer if not missing_value else '',
                      unit='mL' if key=='capacidade_ml' else '')
            commit(temp,'Dados básicos de escopo registrados.')
        except ValueError as ex:error_message(ex)
    st.divider()
    st.markdown('#### Cadastro detalhado — qualquer campo da matriz')
    key=st.selectbox('Selecionar chave técnica',sorted(FIELDS),key='chosen_field',format_func=lambda x:f'{x} · {FIELDS[x]["regras"]}')
    meta=FIELDS[key]
    st.caption(f"Domínio: {meta['dominio']} · Origem: {meta['origem']} · {meta['observacao']}")
    old=fact_by_key(key)
    with st.form(f'fact_form_{key}'):
        a,b=st.columns([3,1])
        with a:
            raw=st.text_input('Valor do campo',value=str(old['value']) if old and old['value'] is not None else '',
                placeholder='Valor técnico; use número sem unidade quando apropriado')
        with b:
            unit=st.text_input('Unidade',value=old.get('unit') or '' if old else '')
        c1,c2=st.columns(2)
        with c1:
            ev_status=st.selectbox('Estado da informação',EVIDENCE,index=EVIDENCE.index(old['evidence_status']) if old else 0)
            applicability=st.selectbox('Aplicabilidade',APPLICABILITY,
                index=APPLICABILITY.index(old['applicability']) if old else 0)
        with c2:
            selected_docs=st.multiselect('Documentos de evidência',doc_choices,
                default=[x for x in old.get('evidence_ids',[]) if x in doc_choices] if old else [])
            human=st.text_input('Confirmação por',value=old.get('human_confirmed_by','') if old else '',
                placeholder='Nome ou identificação do revisor')
        notes=st.text_area('Observação / limites da evidência',value=old.get('observation','') if old else '',height=75)
        save_fact=st.form_submit_button('Salvar campo técnico',type='primary')
    if save_fact:
        try:
            temp=upsert_fact(case,key,raw,status=ev_status,applicability=applicability,
                evidence_ids=selected_docs,reviewer=human,unit=unit,observation=notes)
            commit(temp,f'Campo {key} atualizado.')
        except ValueError as ex:error_message(ex)
    st.divider()
    st.markdown(f"#### Inventário de fatos registrados ({len(case['facts'])})")
    if case['facts']:
        shown=[{'Chave':f['key'],'Valor':str(f['value']) if f['value'] is not None else '—',
               'Estado':f['evidence_status'],'Evidências':', '.join(f.get('evidence_ids',[])),
               'Confirmação':f.get('human_confirmed_by','')} for f in case['facts']]
        st.dataframe(pd.DataFrame(shown),hide_index=True,use_container_width=True)
        delete_key=st.selectbox('Campo para excluir',sorted({f['key'] for f in case['facts']}),key='delete_field')
        if st.button('Excluir campo selecionado',key='remove_field'):
            commit(remove_fact(case,delete_key),f'Campo {delete_key} excluído.')
    else:st.info('Ainda não há fatos técnicos registrados.')

elif page=='Evidências':
    st.subheader('Documentos e rastreabilidade')
    st.caption('O cadastro de um documento não confirma automaticamente os dados extraídos dele. A revisão humana continua necessária.')
    st.markdown('#### Registrar documento')
    uploaded_pdf=st.file_uploader('Selecionar PDF (opcional; sem extração automática)',type=['pdf'],key='doc_file_upload')
    with st.form('document_form'):
        a,b=st.columns(2)
        with a:
            docid=st.text_input('ID único da evidência',value=f"DOC{len(case['documents'])+1:02d}")
            filename=st.text_input('Nome da ficha ou relatório',value=uploaded_pdf.name if uploaded_pdf else '')
            srctype=st.selectbox('Tipo de origem',['url_oficial','upload','declaracao'],index=1 if uploaded_pdf else 0)
        with b:
            url=st.text_input('URL oficial (se houver)')
            docversion=st.text_input('Versão/data do documento')
            locator=st.text_input('Localização no documento (página, tabela etc.)')
        docnotes=st.text_area('Observações',height=80)
        add_doc=st.form_submit_button('Registrar evidência',type='primary')
    if add_doc:
        try:
            record={'id':docid.strip(),'filename':filename.strip(),'source_type':srctype,
                    'version':docversion.strip(),'notes':docnotes.strip()}
            if url.strip():record['url']=url.strip()
            if locator.strip():record['locator']=locator.strip()
            if uploaded_pdf:
                record['sha256']=hashlib.sha256(uploaded_pdf.getvalue()).hexdigest()
            elif srctype=='upload':raise ValueError('Selecione um PDF para registrar origem como upload.')
            commit(upsert_document(case,record),'Documento registrado.')
        except ValueError as ex:error_message(ex)
    st.info('O arquivo PDF não é armazenado no SQLite nem copiado para o envelope JSON. Apenas metadados e hash SHA-256 são registrados. Guarde o arquivo original.')
    st.markdown('#### Evidências registradas')
    if case['documents']:
        st.dataframe(pd.DataFrame([{'ID':d['id'],'Nome':d['filename'],'Tipo':d['source_type'],
            'Versão':d.get('version',''),'Hash SHA-256':d.get('sha256','')[:16]} for d in case['documents']]),
            use_container_width=True,hide_index=True)
        remove_id=st.selectbox('Documento para remover',[d['id'] for d in case['documents']],key='delete_doc')
        if st.button('Remover documento',key='remove_doc'):
            try:commit(remove_document(case,remove_id),'Documento removido.')
            except ValueError as ex:error_message(ex)
    else:st.info('Nenhum documento cadastrado.')

elif page=='IA · Documentos':
    render_document_ai(case,commit)

elif page=='Assistente de ecodesign':
    render_assistant(case, current_result())

elif page=='Avaliação':
    st.subheader('Avaliação técnico-científica')
    st.write('Execute o motor determinístico sobre o envelope atual. O relatório mostra a classificação **por critério**, não a certificação global da embalagem.')
    st.caption('A presença ou ausência declarada dos componentes ainda não possui verificação documental automática. Confirme esses dados com o responsável técnico.')
    if case['matrix_version'] != MATRIX_VERSION:
        st.error(f"O produto usa a matriz {case['matrix_version']}, mas este motor exige {MATRIX_VERSION}.")
    if st.button('Executar avaliação das 15 regras',type='primary',key='run_assessment',
                 disabled=(case['matrix_version']!=MATRIX_VERSION)):
        try:
            result=assess(case)
            st.session_state.assessment=result
            st.session_state.assessment_hash=fingerprint(case)
            st.success('Avaliação concluída. Os resultados por regra estão disponíveis abaixo.')
        except (ValueError,RuntimeError) as ex:error_message(ex)
    result=current_result()
    if not result:
        st.info('Execute a avaliação para ver os resultados. Se os dados forem alterados, a avaliação anterior será invalidada.')
    else:
        counts=Counter(r['status'] for r in result['results'])
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric('Compatíveis',counts['COMPATIVEL'])
        c2.metric('Não compatíveis',counts['NAO_COMPATIVEL'])
        c3.metric('Inconclusivos',counts['INCONCLUSIVO'])
        c4.metric('Ensaios requeridos',len(result['summary']['trials_pending']))
        med=measurements_pending(result)
        c5.metric('Medições pendentes',len(med))
        if med:
            st.caption('Medições/protocolos citados como faltantes (não são ensaios formalmente requisitados):')
            st.dataframe(pd.DataFrame(med),hide_index=True,use_container_width=True)
        if result['scope']=='FORA':st.error('Fora do recorte inicial: não equivale a embalagem não reciclável.')
        elif result['scope']=='INDETERMINADO':st.warning('Escopo não confirmado. Informe material, transparência e cor do corpo.')
        else:st.success('Corpo do produto dentro do recorte PET transparente — demais critérios avaliados separadamente.')
        st.warning('**Classe global: NÃO EMITIDA.** O motor não calcula a classificação completa de reciclabilidade.')
        if result['summary']['incompatibilities_confirmed']:
            st.error('Incompatibilidades comprovadas: '+', '.join(result['summary']['incompatibilities_confirmed']))
        if result['summary']['data_issues']:
            for issue in result['summary']['data_issues']:st.error('Conflito / proveniência: '+issue)
        st.markdown('#### Panorama das regras')
        st.dataframe(pd.DataFrame(rows(result,RULES)),hide_index=True,use_container_width=True)
        st.markdown('#### Detalhamento e recomendações')
        for r in result['results']:
            name=RULES[r['rule_id']]['Título v0.3']
            with st.expander(f"{r['rule_id']} · {name} — {STATUSES.get(r['status'],r['status'])}"):
                st.write('**Conclusão:**',r['reason'] or 'Sem justificativa adicional.')
                if r['missing']:st.write('**Informações faltantes:**',', '.join(r['missing']))
                if r['evidence_ids']:st.write('**Evidências consideradas:**',', '.join(r['evidence_ids']))
                if r['warnings']:
                    for warning in r['warnings']:st.warning(warning)
                if r['recommendations']:
                    for rec in r['recommendations']:st.write('**Recomendação ativada:**',rec)
                else:
                    st.caption('Nenhuma recomendação específica ativada nesta execução.')
                st.caption('Diretriz geral da matriz: '+RULES[r['rule_id']]['Recomendação de ecodesign'])
                if r['trial']!='NAO_REQUERIDO':st.write('**Situação do ensaio:**',r['trial'])
                if r['details']:st.json(r['details'],expanded=False)
                for sid in r['sources']:
                    src=SOURCES.get(sid,{})
                    if src.get('URL oficial / DOI','').startswith('https://'):
                        st.markdown(f"Fonte [{sid}]({src['URL oficial / DOI']}) — {src.get('Versão / data','')}.")
                    else:st.caption('Fonte: '+sid)
        st.markdown('#### Solicitações para completar a avaliação')
        gaps=missing(result)
        if gaps:
            from collections import defaultdict
            users=defaultdict(list)
            for field,rid in gaps:users[field].append(rid)
            gaprows=[{'Campo a confirmar':k,'Regras afetadas':', '.join(v)} for k,v in sorted(users.items(),key=lambda kv:-len(kv[1]))]
            st.dataframe(pd.DataFrame(gaprows),hide_index=True,use_container_width=True)
        else:st.caption('Nenhuma lacuna explícita no relatório individual. Não implica certificação global.')
        report_bytes=json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8')
        st.download_button('Baixar relatório de avaliação (.json)',report_bytes,
                           file_name=f"pet_circular_{case['product_id']}_resultado.json",
                           mime='application/json',use_container_width=True,key='download_result')
        st.download_button('Baixar tabela de regras (.csv)',pd.DataFrame(rows(result,RULES)).to_csv(index=False).encode('utf-8-sig'),
                           file_name=f"pet_circular_{case['product_id']}_regras.csv",mime='text/csv',key='download_csv')

st.divider()
st.caption('PET Circular · PoC de pesquisa · extração sujeita a revisão humana · 15 critérios técnicos · Não utilizar como certificação oficial.')
