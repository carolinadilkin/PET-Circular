"""Adaptação entre a interface Streamlit e o envelope JSON do motor PET Circular."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json
from typing import Any
from pet_circular.engine import validate

ROOT=Path(__file__).resolve().parent
KINDS=['corpo','tampa','rotulo','sleeve','adesivo','tinta','barreira','liner','valvula','lacre','outro']
KIND_LABELS=dict(zip(KINDS,['Corpo PET','Tampa','Rótulo','Sleeve','Adesivo','Tintas','Barreira','Vedante / liner','Válvula','Lacre','Outro']))
PRESENCE=['DESCONHECIDA','SIM','NAO']
EVIDENCE=['DECLARADO','CONFIRMADO','PROPOSTO','EXTRAIDO_PENDENTE','AUSENTE','CONFLITANTE']
APPLICABILITY=['SIM','NAO','DESCONHECIDA']
STATUSES={'COMPATIVEL':'Compatível','LIMITADA':'Limitada','NAO_COMPATIVEL':'Não compatível',
          'INCONCLUSIVO':'Inconclusivo','NAO_ACIONADA':'Não acionada','NAO_APLICAVEL':'Não aplicável','FORA_ESCOPO':'Fora do escopo'}
ALIASES={'evidencias_NIR':'evidencias_nir','EUPIA_declaracao':'eupia_declaracao'}
NUMBER_KEYS={'volume_ml','capacidade_ml','volume_l','cobertura_nao_pet_pct','densidade_rotulo','densidade_tampa',
             'percentual_pa_mxd6_massa','peso_embalagem_vazia_g','massa_conteudo_nominal_g','media_pos_esvaziar_g',
             'numero_ensaios','sleeve_densidade','sleeve_cobertura_pct','massa_corpo_g'}


def fields_catalog():
    fields=json.loads((ROOT/'pet_circular/fields_catalog.json').read_text(encoding='utf-8'))['fields']
    names=('chave','tipo','obrigatoriedade','dominio','regras','origem','observacao')
    return {ALIASES.get(row[0],row[0]):dict(zip(names,[ALIASES.get(row[0],row[0]),*row[1:]])) for row in fields}


def rule_catalog():
    return {r['ID ativo']:r for r in json.loads((ROOT/'pet_circular/rule_catalog.json').read_text(encoding='utf-8'))['rules']}


def source_catalog():
    return json.loads((ROOT/'pet_circular/source_registry.json').read_text(encoding='utf-8'))


def example():
    return json.loads((ROOT/'examples/patrico_input.json').read_text(encoding='utf-8'))


def fresh():
    return {'project_id':'pet-circular-local','product_id':'novo-produto','product_name':'Nova embalagem PET',
            'phase':'projeto_definido','matrix_version':'0.3.3','design_version':'v1','free_description':'',
            'facts':[],'components':[{'id':f'C{i:02d}','kind':k,'presence':'DESCONHECIDA'} for i,k in enumerate(KINDS,1)],
            'documents':[]}


def parse_value(raw,key):
    raw=raw.strip()
    if not raw:return None
    if key not in NUMBER_KEYS:return raw
    try:num=Decimal(raw.replace(',','.'))
    except InvalidOperation as err:raise ValueError(f'{key}: informe só o valor numérico, sem unidade (ex.: 20,3).') from err
    if not num.is_finite():raise ValueError(f'{key}: número inválido.')
    if key=='numero_ensaios':
        if num<0 or num!=int(num):raise ValueError('numero_ensaios exige inteiro não negativo.')
        return int(num)
    return float(num)


def upsert_fact(product,key,raw_value,*,status='DECLARADO',applicability='SIM',evidence_ids=None,reviewer='',unit='',observation=''):
    val=parse_value(raw_value,key) if isinstance(raw_value,str) else raw_value
    ids=list(evidence_ids or [])
    if status not in EVIDENCE or applicability not in APPLICABILITY:raise ValueError('Status ou aplicabilidade inválidos.')
    if any(e not in {d['id'] for d in product['documents']} for e in ids):raise ValueError('Documento de evidência não cadastrado.')
    if status=='CONFIRMADO' and val is not None and not (ids or reviewer.strip()):
        raise ValueError('Para CONFIRMADO, registre documento ou responsável pela confirmação humana.')
    new=deepcopy(product);new['facts']=[f for f in new['facts'] if f['key']!=key]
    if val is not None or status in {'AUSENTE','CONFLITANTE'}:
        fact={'key':key,'value':val,'unit':unit or None,'evidence_status':status,
              'applicability':applicability,'evidence_ids':ids}
        if reviewer.strip():fact['human_confirmed_by']=reviewer.strip()
        if observation.strip():fact['observation']=observation.strip()
        new['facts'].append(fact)
    validate(new)
    return new


def remove_fact(product,key):
    new=deepcopy(product);new['facts']=[f for f in new['facts'] if f['key']!=key];return new


def set_components(product,changes):
    new=deepcopy(product);by_kind={c['kind']:c for c in new['components']}
    for i,k in enumerate(KINDS,1):
        val=changes.get(k,by_kind.get(k,{}).get('presence','DESCONHECIDA'))
        if val not in PRESENCE:raise ValueError('Presença inválida: '+k)
        if k not in by_kind:by_kind[k]={'id':f'NEW{i:02d}','kind':k,'presence':val}
        else:by_kind[k]['presence']=val
    new['components']=list(by_kind.values());validate(new)
    return new


def upsert_document(product,data):
    if not data.get('id','').strip() or not data.get('filename','').strip():
        raise ValueError('Documento exige ID e nome do arquivo.')
    new=deepcopy(product);new['documents']=[d for d in new['documents'] if d['id']!=data['id']]+[data]
    validate(new);return new


def remove_document(product,doc_id):
    if any(doc_id in f.get('evidence_ids',[]) for f in product['facts']):
        raise ValueError('Documento referenciado por dados técnicos. Remova as referências primeiro.')
    new=deepcopy(product);new['documents']=[d for d in new['documents'] if d['id']!=doc_id];return new


def fingerprint(product):
    return hashlib.sha256(json.dumps(product,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()


def rows(result,rules):
    return [{'Regra':r['rule_id'],'Critério':rules[r['rule_id']]['Título v0.3'],
             'Situação':STATUSES.get(r['status'],r['status']),
             'Pendências':', '.join(r['missing']),'Ensaio':r['trial']} for r in result['results']]


def missing(result):
    return sorted({(k,r['rule_id']) for r in result['results'] for k in r.get('missing',[])})


def import_case(content,expected_version='0.3.3'):
    if len(content)>2_000_000:raise ValueError('Arquivo JSON excede 2 MB.')
    case=json.loads(content.decode('utf-8'));validate(case)
    if case['matrix_version']!=expected_version:
        raise ValueError(f"Incompatibilidade de matriz: documento {case['matrix_version']} vs motor {expected_version}.")
    return case
