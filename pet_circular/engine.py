"""Motor demonstrativo PET Circular v0.3.3.

As 15 rotinas preservam avaliações individuais, sem emitir classificação global.
Regras com métodos pendentes não produzem aprovação presumida. Os textos
normativos e os IDs de origem são preservados em rule_catalog.json.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # erro claro no comando principal
    Draft202012Validator = None

VERSION = '0.1.0'
RULE_ORDER = ('PET-14','PET-01','PET-02','PET-03','PET-04','PET-07','PET-09',
              'PET-11','PET-12','PET-13','PET-16','PET-17','PET-18','PET-05','PET-19')
ALLOWED = {'COMPATIVEL','LIMITADA','NAO_COMPATIVEL','INCONCLUSIVO',
           'NAO_APLICAVEL','FORA_ESCOPO','NAO_ACIONADA'}
BAD = {'NAO_COMPATIVEL'}
EVIDENCE_OK = {'CONFIRMADO'}


def norm(value: Any) -> str:
    if value is None: return ''
    raw = unicodedata.normalize('NFKD',str(value).strip().lower())
    return ''.join(c for c in raw if not unicodedata.combining(c)).replace(' ', '_').replace('-', '_')


def decimal_value(x: Any) -> Decimal | None:
    if isinstance(x, bool) or x is None: return None
    try:
        d=Decimal(str(x).replace(',','.'))
        return d if d.is_finite() else None
    except (InvalidOperation,ValueError): return None


def yes(x: Any) -> bool | None:
    if isinstance(x,bool):return x
    v=norm(x)
    if v in {'sim','yes','true','1','confirmado','presente'}:return True
    if v in {'nao','no','false','0','ausente'}:return False
    return None


@dataclass
class Outcome:
    rule_id: str
    status: str = 'INCONCLUSIVO'
    reason: str = ''
    missing: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    trial: str = 'NAO_REQUERIDO'
    details: dict[str,Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.status not in ALLOWED: raise ValueError(f'Estado de regra desconhecido: {self.status}')
        self.missing=sorted(set(self.missing))
        self.evidence_ids=sorted(set(self.evidence_ids))


class Context:
    def __init__(self, product:dict[str,Any]):
        self.product=product
        self.facts=defaultdict(list)
        self.components=defaultdict(list)
        self.data_issues=[]
        self.results={}
        doc_ids={x['id'] for x in product['documents']}
        for x in product['facts']:
            self.facts[x['key']].append(x)
            if x['evidence_status']=='CONFIRMADO' and x['value'] is not None:
                if not x.get('evidence_ids') and not x.get('human_confirmed_by'):
                    self.data_issues.append(f"{x['key']}: CONFIRMADO sem documento ou confirmação humana")
                for e in x.get('evidence_ids',[]):
                    if e not in doc_ids:
                        self.data_issues.append(f"{x['key']}: evidência inexistente {e}")
        for comp in product['components']:
            self.components[comp['kind']].append(comp)
        for name,items in self.facts.items():
            vals={json.dumps(v['value'],ensure_ascii=False,sort_keys=True) for v in items if v['value'] is not None and v['evidence_status'] not in {'AUSENTE'}}
            if len(vals)>1 or any(x['evidence_status']=='CONFLITANTE' for x in items):
                self.data_issues.append(f'{name}: valores contraditórios')
        for name,items in self.components.items():
            if len({c['presence'] for c in items})>1:
                self.data_issues.append(f'{name}: presença contraditória')

    def presence(self,kind:str)->str:
        cs=self.components.get(kind)
        if not cs:return 'DESCONHECIDA'
        vals={c['presence'] for c in cs}
        return vals.pop() if len(vals)==1 else 'DESCONHECIDA'

    def lookup(self,key:str)->tuple[Any|None,list[str],bool]:
        """Somente valores CONFIRMADO fundamentados são utilizáveis como decisão conclusiva.

        Retorna valor, referências de evidência e indicador de valor provisório.
        """
        xs=self.facts.get(norm(key),[])
        if not xs: return None,[],False
        if any(s.startswith(key+':') for s in self.data_issues):return None,[],False
        conf=[f for f in xs if f['evidence_status'] in EVIDENCE_OK and f['value'] is not None]
        if conf:
            x=conf[0]
            return x['value'], x['evidence_ids'], False
        provisional=any(f['value'] is not None and f['evidence_status'] in {'DECLARADO','PROPOSTO','EXTRAIDO_PENDENTE'} for f in xs)
        return None,[],provisional

    def read(self,*keys:str)->tuple[dict[str,Any],list[str],list[str],bool]:
        values={}; missing=[]; ev=[]; preliminary=False
        for k in keys:
            v,e,p=self.lookup(k)
            if v is None:missing.append(k)
            else:values[k]=v
            ev.extend(e); preliminary|=p
        return values,missing,ev,preliminary

    def absent(self,kind:str)->bool:
        return self.presence(kind)=='NAO'

    def result(self,rule_id:str,status='INCONCLUSIVO',reason='',missing=(),evidence=(),warnings=(),recommendations=(),trial='NAO_REQUERIDO',details=None)->Outcome:
        return Outcome(rule_id,status,reason,list(missing),list(evidence),list(warnings),list(recommendations),trial,dict(details or {}))


def component_gate(c:Context,rule:str,kind:str)->Outcome|None:
    presence=c.presence(kind)
    if presence=='NAO':return c.result(rule,'NAO_APLICAVEL',f'{kind} comprovadamente ausente')
    if presence=='DESCONHECIDA':return c.result(rule,missing=[f'presenca_{kind}'],reason=f'Presença de {kind} não confirmada')
    return None


def r14(c:Context)->Outcome:
    issues=list(c.data_issues)
    missing=[]; provisional=[]
    for key,items in c.facts.items():
        if any(f['evidence_status'] in {'AUSENTE','EXTRAIDO_PENDENTE','PROPOSTO','DECLARADO'} for f in items):
            provisional.append(key)
    for kind in ['corpo','tampa','rotulo','sleeve','barreira']:
        if c.presence(kind)=='DESCONHECIDA':missing.append(f'presenca_{kind}')
    if issues:return c.result('PET-14',reason='Conflitos/erros de proveniência requerem revisão humana',missing=missing,warnings=issues,details={'provisorios':sorted(set(provisional))})
    if missing or provisional:return c.result('PET-14',reason='Dados incompletos ou ainda não confirmados',missing=missing,warnings=[f'Dados provisórios: {", ".join(sorted(set(provisional)))}'] if provisional else [],details={'provisorios':sorted(set(provisional))})
    return c.result('PET-14','NAO_ACIONADA','Nenhum conflito de dados explícito detectado; completude por regra será verificada em cada critério')


def r01(c:Context)->Outcome:
    d,m,e,p=c.read('material_corpo','transparencia_corpo','cor_corpo')
    checks={'material_corpo': {'pet'},'transparencia_corpo': {'transparente'},'cor_corpo':{'incolor','azul_claro','azul_claro_transparente'}}
    negatives=[k for k,v in d.items() if norm(v) not in checks[k]]
    if negatives:return c.result('PET-01','FORA_ESCOPO','Fora do recorte PET transparente incolor/azul-claro: '+', '.join(negatives),missing=m,evidence=e,recommendations=['Consultar diretriz apropriada; fora do escopo não significa não reciclável'])
    if m:return c.result('PET-01',reason='Não foi possível confirmar todos os dados de escopo',missing=m,evidence=e)
    return c.result('PET-01','COMPATIVEL','PET transparente incolor/azul-claro confirmado; apenas material/cor do corpo',evidence=e)


def r02(c:Context)->Outcome:
    d,m,e,p=c.read('polimeros_corpo_secundarios')
    if m:return c.result('PET-02',reason='Composição de polímeros adicionais não confirmada',missing=m)
    raw=d['polimeros_corpo_secundarios']
    if isinstance(raw,str): parts=re.split(r'[,;|+]',raw)
    elif isinstance(raw,(list,tuple)): parts=raw
    else:parts=[raw]
    vals={norm(x) for x in parts if norm(x) not in {'','nenhum','sem_adicao','nao','none'}}
    banned={'pla','pvc','ps','petg','pc','pbt'}
    bad=sorted(vals & banned)
    if bad:
        structure,_,_,_=c.read('tipo_estrutura_corpo')
        return c.result('PET-02','NAO_COMPATIVEL',f'Polímero(s) intencional(is) incompatível(is): {", ".join(bad)}',evidence=e,recommendations=['Revisar a composição do corpo e eliminar/substituir o polímero incompatível'],details={'polimeros':bad,'estrutura':structure.get('tipo_estrutura_corpo')})
    if vals:
        return c.result('PET-02',reason=f'Materiais adicionais sem enquadramento nesta regra: {sorted(vals)}',evidence=e,missing=['avaliacao_especifica_polimeros'],warnings=['Não generalizar compatibilidade a outros polímeros'])
    return c.result('PET-02','NAO_ACIONADA','Ausência confirmada de polímeros adicionais listados',evidence=e)


def r03(c:Context)->Outcome:
    d,m,e,p=c.read('aditivos_corpo')
    if m:return c.result('PET-03',reason='Composição dos aditivos do corpo não documentada',missing=m)
    val=norm(d['aditivos_corpo'])
    if val.startswith(('sem_negro','sem_carbono','sem_carbon_black')) or ('negro' not in val and 'carbon_black' not in val and 'carbono' not in val):
        return c.result('PET-03','NAO_ACIONADA','Sem negro de fumo declarado na composição',evidence=e)
    d2,m2,e2,p2=c.read('funcao_aditivo')
    if m2:return c.result('PET-03',reason='Negro de fumo informado, mas função do aditivo desconhecida',missing=m2,evidence=e)
    func=norm(d2['funcao_aditivo'])
    if func in {'reheat','reaquecimento','aditivo_de_reaquecimento'}:
        return c.result('PET-03','NAO_COMPATIVEL','Negro de fumo confirmado como aditivo de reaquecimento',evidence=e+e2,recommendations=['Avaliar eliminação ou substituição do aditivo de reaquecimento'])
    return c.result('PET-03',reason='Negro de fumo com outra função; enquadramento não determinado por esta regra',evidence=e+e2,missing=['avaliacao_especifica_aditivo'])


def r04(c:Context)->Outcome:
    dec={x:c.presence(x) for x in ('rotulo','sleeve')}
    if all(v=='NAO' for v in dec.values()):return c.result('PET-04','NAO_APLICAVEL','Não há rótulo ou sleeve')
    if all(v!='SIM' for v in dec.values()):return c.result('PET-04',reason='Decoração não confirmada',missing=['presenca_rotulo_ou_sleeve'])
    d,m,e,p=c.read('cobertura_nao_pet_pct')
    pct=decimal_value(d.get('cobertura_nao_pet_pct'))
    if pct is not None and not (0<=pct<=100):return c.result('PET-04',reason='Percentual de cobertura fora de 0 a 100',missing=['cobertura_nao_pet_pct_valida'],evidence=e)
    volume_val,_,ve,_=c.read('volume_ml')
    if 'volume_ml' not in volume_val:
        alternate,_,ve2,_=c.read('capacidade_ml')
        volume_val={'volume_ml':alternate.get('capacidade_ml')};ve+=ve2
    vol=decimal_value(volume_val.get('volume_ml'))
    if pct is None or vol is None or vol<=0:
        missed=(['cobertura_nao_pet_pct'] if pct is None else [])+(['volume_ml'] if vol is None or vol<=0 else [])
        return c.result('PET-04',reason='Dados para cálculo de cobertura faltantes',missing=missed,evidence=e+ve)
    threshold=Decimal('50') if vol<=500 else Decimal('70')
    over=pct>threshold
    method,missing_method,em,_=c.read('metodo_cobertura')
    sep,_,se,_=c.read('criterio_sep01')
    requires_trial=yes(sep.get('criterio_sep01')) is True
    mat,_,me,_=c.read('polimero_decoracao','tipo_decoracao')
    if norm(mat.get('tipo_decoracao')) in {'rotulo','label'} and norm(mat.get('polimero_decoracao')) not in {'','pet'} and pct>50:
        requires_trial=True
    trial='REQUERIDO' if requires_trial else ('ALERTA' if over else 'NAO_REQUERIDO')
    warnings=[]
    if over:warnings.append(f'Cobertura {pct}% excede indicação preventiva de {threshold}%')
    if not method:warnings.append('Método de cobertura não documentado; parâmetro operacional ainda não homologado')
    return c.result('PET-04', 'INCONCLUSIVO',
        'Cobertura indicativa avaliada; método normativo e identificabilidade ainda não homologados',missing=missing_method + ['validacao_metodo_normativo_cobertura'],
        evidence=e+ve+em+se+me,warnings=warnings,trial=trial,
        recommendations=['Reduzir cobertura não-PET e verificar condições específicas do SEP-01'] if over or requires_trial else [],
        details={'cobertura_pct':float(pct),'limite_indicativo_pct':int(threshold),'acima_indicacao':over,'gatilho_sep01':requires_trial})


def r07(c:Context)->Outcome:
    g=component_gate(c,'PET-07','tampa')
    if g:return g
    d,m,e,p=c.read('material_tampa')
    if m:return c.result('PET-07',reason='Polímero da tampa não confirmado',missing=m)
    material=norm(d['material_tampa']); missing=[];notes=[];bad=[]
    if material in {'pe','pp'}:
        dx,mx,ex,_=c.read('densidade_tampa'); e+=ex;missing+=mx
        density=decimal_value(dx.get('densidade_tampa'))
        if density is not None and density>1:bad.append('Densidade PE/PP >1 g/cm³')
        elif density is not None and density<=0:missing.append('densidade_tampa_valida')
    elif material=='pet':
        dx,mx,ex,_=c.read('transparencia_tampa_pet','cor_tampa_pet','aditivos_tampa');e+=ex;missing+=mx
        if 'transparencia_tampa_pet' in dx and norm(dx['transparencia_tampa_pet'])!='transparente':bad.append('PET opaco na tampa')
        if 'cor_tampa_pet' in dx and norm(dx['cor_tampa_pet'])!='incolor':bad.append('PET colorido na tampa')
        if 'aditivos_tampa' in dx and norm(dx['aditivos_tampa']) not in {'nenhum','sem_aditivos','aprovados','aprovado'}:missing.append('comprovacao_aditivos_tampa')
    else:
        return c.result('PET-07',reason='Material da tampa sem classificação nesta implementação',missing=['avaliacao_especifica_material_tampa'],evidence=e)
    fx,mx,ex,_=c.read('fixacao_tampa');e+=ex;missing+=mx
    if 'fixacao_tampa' in fx and norm(fx['fixacao_tampa']) in {'soldada','nao_desprendivel','permanente_incompativel'}:
        bad.append('Fixação soldada/não desprendível')
    if bad:return c.result('PET-07','NAO_COMPATIVEL','; '.join(bad),missing=missing,evidence=e,recommendations=['Reformular material ou sistema de fixação'])
    if missing:return c.result('PET-07',reason='Dados de material/fixação incompletos',missing=missing,evidence=e)
    if c.presence('liner')=='DESCONHECIDA' or c.presence('valvula')=='DESCONHECIDA':
        return c.result('PET-07',reason='Material/fixação verificados; sistema completo possui acessórios não confirmados',evidence=e,missing=['presenca_liner','presenca_valvula'],details={'material_tampa_verificado':True})
    return c.result('PET-07','COMPATIVEL','Critérios examinados do material e fixação da tampa atendidos; acessórios ausentes ou tratados fora desta regra',evidence=e)


def r09(c:Context)->Outcome:
    g=component_gate(c,'PET-09','adesivo')
    if g:
        if g.status=='INCONCLUSIVO' and c.presence('rotulo')=='NAO':return c.result('PET-09','NAO_APLICAVEL','Rótulo comprovadamente ausente; adesivo de rótulo não aplicável')
        return g
    d,m,e,p=c.read('comportamento_adesivo')
    if m:return c.result('PET-09',reason='Comportamento do adesivo não confirmado',missing=m)
    behavior=norm(d['comportamento_adesivo'])
    if behavior in {'soluvel','nao_liberavel','nao_desprendivel'}:
        return c.result('PET-09','NAO_COMPATIVEL',f'Adesivo {behavior} incompatível na aplicação',evidence=e,recommendations=['Substituir por adesivo liberável durante lavagem'])
    if behavior not in {'liberavel','releasable','desprendivel'}:
        return c.result('PET-09',reason='Comportamento não enquadrado pela regra',missing=['classificacao_adesivo'],evidence=e)
    d2,m2,e2,_=c.read('faixa_temperatura','meio_lavagem','evidencia_desprendimento')
    if m2:return c.result('PET-09',reason='Liberação declarada, mas condições/evidência insuficientes',missing=m2,evidence=e)
    faixa=norm(d2['faixa_temperatura'])
    if not any(x in faixa for x in ('70','90')):
        return c.result('PET-09',reason='Temperatura de avaliação não demonstra faixa 70–90 °C',evidence=e+e2,missing=['validacao_faixa_70_90c'])
    return c.result('PET-09','COMPATIVEL','Liberação confirmada em lavagem aplicável a 70–90 °C',evidence=e+e2)


def r11(c:Context)->Outcome:
    g=component_gate(c,'PET-11','barreira')
    if g:return g
    d,m,e,_=c.read('barreira_tipo')
    if m:return c.result('PET-11',reason='Tecnologia de barreira não documentada',missing=m)
    tipo=norm(d['barreira_tipo'])
    if tipo not in {'siox','siox_plasma'}:
        return c.result('PET-11','NAO_APLICAVEL','Barreira não SiOx; encaminhar à PET-12 ou análise específica',evidence=e)
    d2,m2,e2,_=c.read('deposicao_barreira','ficha_barreira')
    if m2:return c.result('PET-11',reason='SiOx informado sem comprovação completa da deposição',missing=m2,evidence=e)
    if norm(d2['deposicao_barreira']) not in {'plasma','deposicao_por_plasma','pecvd'}:
        return c.result('PET-11',reason='Tecnologia distinta de SiOx por plasma; avaliação específica',missing=['avaliacao_deposicao_siox'],evidence=e+e2)
    extras,_,ev3,_=c.read('outras_camadas')
    if extras and norm(extras['outras_camadas']) not in {'nao','nenhuma','ausentes','false'}:
        return c.result('PET-11','COMPATIVEL','Revestimento SiOx por plasma compatível isoladamente; outras camadas não aprovadas por esta regra',evidence=e+e2+ev3,warnings=['Avaliar outras camadas separadamente'])
    return c.result('PET-11','COMPATIVEL','Revestimento SiOx por plasma compatível como critério isolado',evidence=e+e2)


def r12(c:Context)->Outcome:
    g=component_gate(c,'PET-12','barreira')
    if g:return g
    d,m,e,_=c.read('barreira_tipo')
    if m:return c.result('PET-12',reason='Material de barreira não documentado',missing=m)
    t=norm(d['barreira_tipo'])
    if t=='evoh':return c.result('PET-12','NAO_COMPATIVEL','EVOH confirmado em camada de barreira',evidence=e,recommendations=['Eliminar EVOH quando possível; avaliar alternativas com compatibilidade comprovada'])
    if t in {'siox','siox_plasma'}:return c.result('PET-12','NAO_APLICAVEL','SiOx avaliado na PET-11',evidence=e)
    if t not in {'pa_mxd6','pamxd6'}:
        return c.result('PET-12',reason='Barreira não contemplada nesta regra',missing=['avaliacao_especifica_barreira'],evidence=e)
    d2,m2,e2,_=c.read('arquitetura_camadas');e+=e2
    if m2:return c.result('PET-12',reason='Estrutura de PA-MXD6 desconhecida',missing=m2,evidence=e)
    structure=norm(d2['arquitetura_camadas'])
    if structure in {'blenda_monocamada','monocamada_blenda','blenda'}:
        return c.result('PET-12','NAO_COMPATIVEL','Blenda monocamada de PA-MXD6',evidence=e)
    if structure!='multicamada':return c.result('PET-12',reason='Estrutura de PA-MXD6 não reconhecida',missing=['avaliacao_estrutura_pa_mxd6'],evidence=e)
    dx,mx,ex,_=c.read('percentual_pa_mxd6_massa','tie_layer');e+=ex
    if 'tie_layer' in dx and yes(dx['tie_layer']) is True:
        return c.result('PET-12','NAO_COMPATIVEL','PA-MXD6 multicamada com tie layers',evidence=e,missing=mx)
    pct=decimal_value(dx.get('percentual_pa_mxd6_massa'))
    if pct is not None and pct>5:
        return c.result('PET-12','NAO_COMPATIVEL',f'PA-MXD6 {pct}% (>5%)',evidence=e,missing=mx)
    if mx or pct is None or pct<0 or yes(dx.get('tie_layer')) is None:
        return c.result('PET-12',reason='Percentual/tie layers de PA-MXD6 insuficientes',missing=mx or ['percentual_pa_mxd6_massa_valido','tie_layer'],evidence=e)
    return c.result('PET-12','LIMITADA','PA-MXD6 multicamada ≤5% sem tie layers: compatibilidade limitada',evidence=e,details={'teor_pct':float(pct)})


def r13(c:Context)->Outcome:
    d,m,e,_=c.read('marcacao_tecnologia')
    if m:return c.result('PET-13',reason='Tecnologia de marcação não informada',missing=m)
    tech=norm(d['marcacao_tecnologia'])
    if tech in {'nenhuma','ausente','sem_marcacao'}:return c.result('PET-13','NAO_APLICAVEL','Sem marcação direta')
    d2,m2,e2,_=c.read('marcacao_finalidade','marcacao_local');e+=e2
    if m2:return c.result('PET-13',reason='Finalidade/local da marcação desconhecidos',missing=m2,evidence=e)
    local=norm(d2['marcacao_local']);purpose=norm(d2['marcacao_finalidade'])
    if local not in {'corpo','corpo_pet'}:return c.result('PET-13','NAO_APLICAVEL','Marcação não aplicada diretamente ao corpo',evidence=e)
    if tech in {'laser','marcacao_laser'} and purpose in {'producao','data_producao','validade','data_validade'}:
        return c.result('PET-13','COMPATIVEL','Laser para data de produção/validade',evidence=e)
    if tech in {'tinta','impressao_com_tinta','impressao_direta'}:
        if purpose in {'producao','data_producao','validade','data_validade'}:
            return c.result('PET-13','LIMITADA','Impressão direta com tinta para data: compatibilidade limitada',evidence=e)
        if purpose=='decoracao':return c.result('PET-13','NAO_COMPATIVEL','Impressão decorativa diretamente no corpo PET',evidence=e,recommendations=['Preferir rótulo removível compatível'])
    return c.result('PET-13',reason='Tecnologia ou finalidade não abrangida diretamente',missing=['avaliacao_especifica_marcacao'],evidence=e)


def r16(c:Context)->Outcome:
    volume,_,ev,_=c.read('volume_l')
    if 'volume_l' in volume: vol=decimal_value(volume['volume_l'])
    else:
        alt,_,ex,_=c.read('capacidade_ml','volume_ml');ev+=ex
        n=alt.get('capacidade_ml',alt.get('volume_ml'));vol=decimal_value(n);vol=vol/1000 if vol is not None else None
    compact,cm,ce,_=c.read('dimensoes_apos_compactacao','protocolo_compactacao');ev+=ce
    dim=decimal_value(compact.get('dimensoes_apos_compactacao'))
    if vol is not None and vol>5:
        return c.result('PET-16','NAO_COMPATIVEL',f'Capacidade nominal de {vol} L excede 5 L',evidence=ev,recommendations=['Avaliar redimensionamento ou outro fluxo de coleta'],details={'capacidade_l':float(vol)})
    if vol is not None and vol<=0:return c.result('PET-16',reason='Capacidade deve ser positiva',missing=['volume_l_valido'])
    if dim is not None and dim<=4 and 'protocolo_compactacao' in compact:
        # O método de 4 cm ainda carece de homologação. Não declarar incompatibilidade conclusiva.
        return c.result('PET-16',reason='Dimensão ≤4 cm indicada, porém aplicação operacional do limite ainda requer validação',evidence=ev,missing=['validacao_operacional_4cm'],warnings=['Possível incompatibilidade dimensional; não homologada'],details={'dimensao_cm':float(dim)})
    if dim is not None and dim<0:return c.result('PET-16',reason='Dimensão compactada inválida',missing=['dimensoes_apos_compactacao_validas'])
    if vol is None or dim is None or 'protocolo_compactacao' not in compact:
        return c.result('PET-16',reason='Capacidade avaliada quando disponível; compactação pendente',missing=([ 'volume_l' ] if vol is None else [])+([ 'dimensoes_apos_compactacao','protocolo_compactacao' ] if dim is None or 'protocolo_compactacao' not in compact else []),evidence=ev,details={'capacidade_l':float(vol) if vol is not None else None,'gatilho_5l':False if vol is not None else None})
    return c.result('PET-16',reason='Capacidade ≤5 L; interpretação do limite compactado ainda não homologada',evidence=ev,missing=['validacao_operacional_4cm'],details={'capacidade_l':float(vol) if vol is not None else None})


def r17(c:Context)->Outcome:
    d,m,e,_=c.read('produto_tipo')
    if m:return c.result('PET-17',reason='Tipo de produto e aplicabilidade do ensaio não confirmados',missing=m)
    if norm(d['produto_tipo']) in {'seco','granulado','solido'}:
        return c.result('PET-17','NAO_APLICAVEL','EtEi não aplicável automaticamente a esta categoria; requer avaliação por método pertinente',evidence=e)
    dx,mx,ex,_=c.read('peso_embalagem_vazia_g','massa_conteudo_nominal_g','media_pos_esvaziar_g','numero_ensaios','metodo_ete');e+=ex
    if mx:return c.result('PET-17',reason='Easy-to-Empty sem dados experimentais suficientes',missing=mx,evidence=e,trial='PENDENTE')
    w=decimal_value(dx['peso_embalagem_vazia_g']);pf=decimal_value(dx['massa_conteudo_nominal_g']);pe=decimal_value(dx['media_pos_esvaziar_g']);n=decimal_value(dx['numero_ensaios'])
    if None in {w,pf,pe,n} or pf<=0 or pe<w or n<10 or n!=int(n):
        return c.result('PET-17',reason='Dados de esvaziamento inválidos ou menos de 10 ensaios',missing=['validacao_ensaios_ete'],evidence=e,trial='PENDENTE')
    idx=100*(pe-w)/pf
    if idx<0:return c.result('PET-17',reason='Índice negativo não permitido',missing=['validacao_ensaios_ete'],evidence=e)
    info={'indice_pct':round(float(idx),4),'n_ensaios':int(n),'penalizacao_classes':0}
    if idx<=5:return c.result('PET-17','NAO_ACIONADA','Easy-to-Empty ≤5%: sem penalização',evidence=e,details=info)
    if idx<=10: info['penalizacao_classes']=1
    elif idx<=15:info['penalizacao_classes']=2
    else:return c.result('PET-17','NAO_COMPATIVEL','Easy-to-Empty >15%: desqualificação na metodologia de referência',evidence=e,details=info)
    return c.result('PET-17',reason=f'Easy-to-Empty {idx:.2f}%: penalização de {info["penalizacao_classes"]} classe(s); classificação global não calculada',evidence=e,trial='REQUERIDO',details=info,recommendations=['Avaliar redesenho para facilitar esvaziamento'])


def r18(c:Context)->Outcome:
    g=component_gate(c,'PET-18','tinta')
    if g:
        if g.status=='INCONCLUSIVO' and c.presence('rotulo')=='NAO' and c.presence('sleeve')=='NAO':
            return c.result('PET-18','NAO_APLICAVEL','Sem rótulo/sleeve para impressão')
        return g
    d,m,e,_=c.read('tinta_bleeding','tinta_washable','tinta_metalica','tinta_ligantes','EUPIA_declaracao')
    bad=[]
    for k,label in [('tinta_bleeding','bleeding'),('tinta_washable','tinta washable'),('tinta_metalica','tinta metálica')]:
        if k in d and yes(d[k]) is True:bad.append(label)
    if 'tinta_ligantes' in d and norm(d['tinta_ligantes']) not in {'sem_clorados','nao_clorado','sem_pvc','livre_de_clorados'} and any(word in norm(d['tinta_ligantes']) for word in ('clorad','pvc')):bad.append('ligante clorado')
    if 'EUPIA_declaracao' in d and yes(d['EUPIA_declaracao']) is False:bad.append('não conformidade EuPIA')
    if bad:return c.result('PET-18','NAO_COMPATIVEL','Tinta: '+', '.join(bad),missing=m,evidence=e,recommendations=['Substituir/reformular a tinta incompatível'])
    retain,rm,er,_=c.read('tinta_formulacao','protocolo_tintas');e+=er;m+=rm
    if m:return c.result('PET-18',reason='Tinta sem comprovação integral de composição e desempenho',missing=m,evidence=e)
    if yes(d.get('EUPIA_declaracao')) is not True or any(yes(d.get(k)) is not False for k in ['tinta_bleeding','tinta_washable','tinta_metalica']):
        return c.result('PET-18',reason='Evidência inconclusiva das características da tinta',missing=['comprovacao_tinta'],evidence=e)
    if norm(d.get('tinta_ligantes')) in {'desconhecido','nao_informado',''}:
        return c.result('PET-18',reason='Ligante de tinta sem identificação suficiente',missing=['tinta_ligantes'],evidence=e)
    return c.result('PET-18','COMPATIVEL','Composição/retentividade e EuPIA documentadas; apenas critério da tinta',evidence=e,warnings=['Removibilidade do sleeve/rótulo verificada separadamente'])


def r05(c:Context)->Outcome:
    g=component_gate(c,'PET-05','rotulo')
    if g:return g
    d,m,e,_=c.read('polimero_rotulo','densidade_rotulo','fixacao_rotulo','desprendimento');bad=[]
    poly=norm(d.get('polimero_rotulo'));density=decimal_value(d.get('densidade_rotulo'))
    if poly in {'pvc','petg','pla','ps','pet','pc','pbt'} and (density is None or density>1):bad.append('Polímero do rótulo classificado como incompatível no contexto informado')
    if density is not None and density>1:bad.append('Rótulo com densidade >1 g/cm³')
    if norm(d.get('fixacao_rotulo')) in {'soldada','permanente','nao_desprendivel'} or ('desprendimento' in d and yes(d['desprendimento']) is False):bad.append('Fixação sem desprendimento')
    e2=[]
    for rule in ['PET-04','PET-09','PET-18']:
        o=c.results.get(rule)
        if o and o.status=='NAO_COMPATIVEL':
            bad.append(f'Incompatibilidade associada verificada em {rule}')
    if bad:return c.result('PET-05','NAO_COMPATIVEL','; '.join(bad),missing=m,evidence=e,recommendations=['Revisar material, fixação e/ou decoração conforme incompatibilidade'])
    if m:return c.result('PET-05',reason='Material, densidade ou desprendimento do rótulo incompleto',missing=m,evidence=e)
    if poly not in {'pe','pp','opp'} or density is None or density<0:
        return c.result('PET-05',reason='Configuração não homologada automaticamente por este motor',missing=['avaliacao_especifica_rotulo'],evidence=e)
    if yes(d['desprendimento']) is not True:
        return c.result('PET-05',reason='Removibilidade não confirmada',missing=['desprendimento'],evidence=e)
    if density>1:return c.result('PET-05','NAO_COMPATIVEL','Densidade elevada',evidence=e)
    linked={r:c.results[r].status for r in ['PET-04','PET-09','PET-18'] if r in c.results}
    if any(s=='INCONCLUSIVO' for s in linked.values()):
        return c.result('PET-05',reason='Material/fixação favoráveis; decoração completa ainda tem critérios pendentes',evidence=e,details={'material_favoravel':True,'integracao':linked})
    return c.result('PET-05','COMPATIVEL','Rótulo de poliolefina flutuante com desprendimento confirmado, no âmbito deste critério',evidence=e,details={'integracao':linked})


def r19(c:Context)->Outcome:
    g=component_gate(c,'PET-19','sleeve')
    if g:return g
    d,m,e,_=c.read('sleeve_tipo','sleeve_polimero','sleeve_densidade');
    density=decimal_value(d.get('sleeve_densidade'))
    if 'sleeve_densidade' in d and density is None:return c.result('PET-19',reason='Densidade inválida',missing=['sleeve_densidade_valida'],evidence=e)
    poly=norm(d.get('sleeve_polimero'));tipo=norm(d.get('sleeve_tipo'))
    if density is not None and density<=0:return c.result('PET-19',reason='Densidade inválida',missing=['sleeve_densidade_valida'],evidence=e)
    if density is not None and density>1:return c.result('PET-19','NAO_COMPATIVEL','Densidade do sleeve >1 g/cm³',evidence=e)
    if poly=='petg_espumado':return c.result('PET-19','NAO_COMPATIVEL','PETG espumado classificado como incompatível',evidence=e)
    nir,_,en,_=c.read('evidencias_NIR');e+=en
    if 'evidencias_NIR' in nir and norm(nir['evidencias_NIR']) in {'bloqueia','nao_identifica','falhou','reprovado'}:
        return c.result('PET-19','NAO_COMPATIVEL','Sleeve impede identificação por NIR',evidence=e)
    if m:return c.result('PET-19',reason='Configuração/material do sleeve não confirmados',missing=m,evidence=e)
    if poly in {'eps','pet_espumado','ldpet'}:
        if density is not None and density<=Decimal('0.95'):
            return c.result('PET-19','LIMITADA','Sleeve espumado/LDPET com densidade ≤0,95 g/cm³; critério limitado',evidence=e)
        return c.result('PET-19',reason='Material espumado fora das condições limitadas documentadas',missing=['avaliacao_especifica_sleeve'],evidence=e)
    if poly not in {'pe','pp','opp'}:return c.result('PET-19',reason='Outro polímero do sleeve exige avaliação específica',missing=['avaliacao_especifica_sleeve'],evidence=e)
    if density is None:return c.result('PET-19',reason='Densidade não disponível',missing=['sleeve_densidade'],evidence=e)
    if tipo=='integral':
        ir,mm,ei,_=c.read('sleeve_ir');e+=ei
        if mm:return c.result('PET-19',reason='Sleeve integral sem comprovação de translucidez IR',missing=mm,evidence=e,trial='PENDENTE')
        if yes(ir['sleeve_ir']) is True:
            return c.result('PET-19','LIMITADA','Sleeve integral de poliolefina IR-translúcido: classe limitada do critério',evidence=e,trial='PENDENTE' if 'evidencias_NIR' not in nir else 'NAO_REQUERIDO',warnings=['Translucidez declarada não substitui ensaio de identificabilidade quando necessário'])
        return c.result('PET-19',reason='Sleeve integral não demonstrou translucidez ao IR; avaliar NIR',missing=['prova_identificabilidade_NIR'],evidence=e,trial='PENDENTE')
    if tipo=='parcial':
        linked={r:c.results[r].status for r in ('PET-04','PET-18') if r in c.results}
        if any(x=='INCONCLUSIVO' for x in linked.values()):
            return c.result('PET-19',reason='Material do sleeve favorável, mas tinta/cobertura pendente',evidence=e,details={'integracao':linked})
        return c.result('PET-19','COMPATIVEL','Sleeve parcial PE/PP/OPP com densidade ≤1 g/cm³ no critério de material',evidence=e,details={'integracao':linked})
    return c.result('PET-19',reason='Configuração especial depende da diretriz específica/EPBP',missing=['avaliacao_configuracao_sleeve'],evidence=e)


RULE_HANDLERS:dict[str,Callable[[Context],Outcome]]={
 'PET-14':r14,'PET-01':r01,'PET-02':r02,'PET-03':r03,'PET-04':r04,
 'PET-05':r05,'PET-07':r07,'PET-09':r09,'PET-11':r11,'PET-12':r12,
 'PET-13':r13,'PET-16':r16,'PET-17':r17,'PET-18':r18,'PET-19':r19,
}


def load_catalog()->dict[str,Any]:
    return json.loads(files('pet_circular').joinpath('rule_catalog.json').read_text(encoding='utf-8'))


def validate(product:dict[str,Any])->None:
    if Draft202012Validator is None:
        raise RuntimeError('Dependência jsonschema ausente. Execute: pip install -r requirements.txt')
    schema=json.loads(files('pet_circular').joinpath('input.schema.json').read_text(encoding='utf-8'))
    errors=list(Draft202012Validator(schema).iter_errors(product))
    if errors:
        errors.sort(key=lambda err: '.'.join(map(str,err.absolute_path)))
        raise ValueError('Erro de contrato: '+ '; '.join(f'{".".join(map(str,e.absolute_path)) or "raiz"}: {e.message}' for e in errors[:8]))


def assess(product:dict[str,Any])->dict[str,Any]:
    validate(product)
    ctx=Context(product)
    catalog=load_catalog()
    rules={r['ID ativo']:r for r in catalog['rules']}
    if set(RULE_ORDER)!=set(rules) or set(RULE_ORDER)!=set(RULE_HANDLERS):raise RuntimeError('Catálogo e handlers discordam')
    items=[]
    for rid in RULE_ORDER:
        if rid not in {'PET-14','PET-01'} and ctx.results['PET-01'].status=='FORA_ESCOPO':
            obj=ctx.result(rid,'NAO_APLICAVEL','Fora do recorte do MVP (não implica não reciclável)')
        else:obj=RULE_HANDLERS[rid](ctx)
        obj.sources=[x.strip() for x in (rules[rid]['ID de fonte'] or '').split(';') if x.strip()]
        ctx.results[rid]=obj
        items.append(asdict(obj))
    outside=ctx.results['PET-01'].status=='FORA_ESCOPO'
    incompatible=[i['rule_id'] for i in items if i['status']=='NAO_COMPATIVEL']
    unresolved=[i['rule_id'] for i in items if i['status']=='INCONCLUSIVO']
    trials=[i['rule_id'] for i in items if i['trial'] in {'REQUERIDO','PENDENTE'}]
    return {
      'engine_version':VERSION,'matrix_version':catalog['matrix_version'],
      'product_id':product['product_id'],'product_name':product['product_name'],
      'design_version':product.get('design_version','sem_versao'),
      'phase':product['phase'], 'scope': 'FORA' if outside else ('DENTRO' if ctx.results['PET-01'].status=='COMPATIVEL' else 'INDETERMINADO'),
      'global_recyclability_class':'NAO_EMITIDA', 'official_certification':False,
      'summary':{'incompatibilities_confirmed':incompatible,'rules_inconclusive':unresolved,'trials_pending':trials,
                 'data_issues':ctx.data_issues,'notes':['Avaliação demonstrativa por regras individuais; não constitui certificação RecyClass.',
                   'Sem classe global mesmo quando todos os critérios individuais parecem favoráveis.',
                   'Regras com método ou ensaio pendente não recebem aprovação presumida.']},
      'results':items,
    }
