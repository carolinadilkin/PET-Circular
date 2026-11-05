/* PET Circular v0.4 Web — presentation layer faithful to approved HTML prototype.
 * Engine, review and comparison are executed ONLY by local Python endpoints.
 * No external CDN, image, font or script is loaded.
 */
'use strict';
const state = {
  token: '', meta: null, case: null, report: null, dirty: false, saved: false, stale: false,
  view: 'inicio', step: 0, tab: 'pdf', manualKey: 'polimero_rotulo',
  extraction: null, importPreview: null, snapshots: [], comparison: null,
  compareA: 'demo:A', compareB: 'demo:B', uploads: {}, assistant: null,
  lastMessage: '', demo: false, busy: false
};
const statusNames = {
  NAO_COMPATIVEL:'Não compatível', COMPATIVEL:'Compatível', INCONCLUSIVO:'Inconclusivo',
  NAO_APLICAVEL:'Não aplicável', NAO_ACIONADA:'Não acionada', LIMITADA:'Limitada',
  FORA_ESCOPO:'Fora do escopo'
};
const statusClass = {
  NAO_COMPATIVEL:'bad', COMPATIVEL:'good', INCONCLUSIVO:'pending',
  LIMITADA:'pending', NAO_APLICAVEL:'neutral', NAO_ACIONADA:'neutral', FORA_ESCOPO:'neutral'
};
const fieldNames = {
  material_corpo:'Material do corpo', transparencia_corpo:'Transparência do corpo',cor_corpo:'Cor do corpo',
  capacidade_ml:'Capacidade nominal (mL)', material_tampa:'Material da tampa',polimero_rotulo:'Material do rótulo',
  densidade_rotulo:'Densidade do rótulo (g/cm³)',fixacao_rotulo:'Fixação do rótulo',
  desprendimento:'Desprendimento do rótulo',cobertura_nao_pet_pct:'Cobertura não-PET (%)',
  comportamento_adesivo:'Comportamento do adesivo',tinta_tipo:'Tipo de tinta',
  marcacao_tecnologia:'Tecnologia de marcação',dimensoes_apos_compactacao:'Dimensões após compactação',
  protocolo_compactacao:'Protocolo de compactação',validacao_metodo_normativo_cobertura:'Método de cobertura validado'
};
const stageNames = ['Embalagem', 'Dados técnicos', 'Revisão', 'Resultados'];
const $ = (s,root=document)=>root.querySelector(s);
const $$ = (s,root=document)=>[...root.querySelectorAll(s)];
function esc(s){ return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
const label = key => fieldNames[key] || key.replaceAll('_',' ').replace(/\\b\\w/g, s=>s.toUpperCase());
const coreKeys = new Set(['material_corpo','transparencia_corpo','cor_corpo','capacidade_ml']);
const fieldGroups = [
 ['Corpo e estrutura',['tipo_estrutura_corpo','polimeros_corpo_secundarios','evidencia_composicao','percentual_pa_mxd6_massa','aditivos_corpo']],
 ['Tampa e vedação',['material_tampa','densidade_tampa','aditivos_tampa','material_vedante']],
 ['Rótulo e sleeve',['polimero_rotulo','densidade_rotulo','fixacao_rotulo','desprendimento','cobertura_nao_pet_pct','sleeve_polimero','sleeve_densidade','sleeve_cobertura_pct']],
 ['Adesivos, tintas e impressão',['comportamento_adesivo','adesivo_tipo','tinta_tipo','marcacao_tecnologia']],
 ['Dimensões e ensaios',['dimensoes_apos_compactacao','protocolo_compactacao','numero_ensaios','peso_embalagem_vazia_g','massa_conteudo_nominal_g','media_pos_esvaziar_g']]
];
const friendly = {polimeros_corpo_secundarios:'Outros polímeros incorporados ao CORPO (não tampa/rótulo)',sleeve_polimero:'Material do sleeve',sleeve_densidade:'Densidade do sleeve (g/cm³)',adesivo_tipo:'Tipo de adesivo',aditivos_corpo:'Aditivos no corpo',aditivos_tampa:'Aditivos na tampa',tipo_estrutura_corpo:'Estrutura do corpo',material_vedante:'Material do vedante'};
function humanLabel(k){return friendly[k]||label(k);}
function groupedFields(fields){
 const used=new Set([...coreKeys]);let groups=fieldGroups.map(([name,keys])=>[name,keys.filter(k=>fields[k]&&!used.has(k))]);groups.forEach(g=>g[1].forEach(k=>used.add(k)));
 groups.push(['Outras informações técnicas',Object.keys(fields).filter(k=>!used.has(k)).sort()]);return groups.filter(g=>g[1].length);
}
function manualOptions(fields){return groupedFields(fields).map(([name,keys])=>'<optgroup label="'+esc(name)+'">'+keys.map(k=>'<option value="'+esc(k)+'" '+(state.manualKey===k?'selected':'')+'>'+esc(humanLabel(k))+'</option>').join('')+'</optgroup>').join('');}
const tag = (s)=>`<span class="tag ${statusClass[s]||'neutral'}">${esc(statusNames[s]||s)}</span>`;
const knownCount = c=>(c?.components||[]).filter(x=>x.presence!=='DESCONHECIDA').length;
const confirmedCount = c=>(c?.facts||[]).filter(x=>x.evidence_status==='CONFIRMADO').length;
const counts = r => Object.fromEntries(Object.keys(statusNames).map(s=>[s,(r?.results||[]).filter(x=>x.status===s).length]));
const oldFact = key => (state.case?.facts||[]).find(x=>x.key===key);
const factValue = key => oldFact(key)?.value ?? '';
function notify(msg,type='info') { const n=$('#toast'); n.textContent=msg;n.className='toast show'; if(type==='error')n.style.background='#86282e';else n.style.background='';clearTimeout(window._toastTimer);window._toastTimer=setTimeout(()=>n.classList.remove('show'),5200); }
async function api(path,body=null,opts={}){
  const init={method:body===null?'GET':'POST',headers:{'X-PET-Session':state.token}};
  if(body!==null){if(opts.form){init.body=body;}else if(opts.raw){init.headers['Content-Type']='application/json';init.body=body;}else{init.headers['Content-Type']='application/json';init.body=JSON.stringify(body);}}
  const r=await fetch(path,init);let val;try{val=await r.json()}catch{throw Error('O servidor não retornou uma resposta válida.');}
  if(!r.ok)throw Error(typeof val.detail==='string'?val.detail:'Falha ao processar a operação.');return val;
}
async function act(fn){if(state.busy)return;state.busy=true;try{await fn()}catch(err){console.error(err);notify(err.message||'Erro não identificado','error')}finally{state.busy=false}}
function newCase(caseValue,{demo=false,report=null,dirty=true,saved=false}={}){
  state.case=structuredClone(caseValue);state.report=report;state.dirty=dirty;state.saved=saved;state.stale=false;state.demo=demo;
  state.extraction=null;state.importPreview=null;state.assistant=null;state.comparison=null;
}
function editCase(caseValue){state.case=caseValue;state.report=null;state.dirty=true;state.saved=false;state.stale=true;state.demo=false;state.assistant=null;}
function changeGuard(){return !state.dirty || window.confirm('Existem alterações ainda não salvas como versão. Desejas trocar de projeto mesmo assim?');}
function show(view,step){
  state.view=view;if(step!==undefined)state.step=Number(step);
  $$('.page').forEach(el=>el.classList.toggle('active',el.id==='page-'+view));
  $$('.nav button').forEach(el=>{const on=el.dataset.view===view;el.classList.toggle('active',on);on?el.setAttribute('aria-current','page'):el.removeAttribute('aria-current')});
  renderCurrent();window.scrollTo({top:0,behavior:'instant'});$('#content')?.focus({preventScroll:true});
}
function renderCurrent(){
  if(state.view==='avaliacao')renderEvaluation();
  if(state.view==='comparacao')renderComparison();
  if(state.view==='projetos')renderProjects();
}
function setStep(step){state.step=Number(step);renderEvaluation();window.scrollTo({top:110,behavior:'instant'});}
function workspace(){let c=state.case;return `<div class="workspacebar"><div><small>Embalagem ativa · ${state.demo?'cenário sintético':'projeto local'}</small><strong>${esc(c.product_name)}</strong><small>ID: ${esc(c.product_id)} · Versão ${esc(c.design_version||'v1')} · ${c.facts.length} informações técnicas · presença definida em ${knownCount(c)}/11 componentes</small></div><div class="statusline">${state.stale?'<span class="tag is-stale">Alterações ainda não avaliadas</span>':''}${state.dirty?'<span class="tag neutral">Alterações não salvas</span>':state.saved?'<span class="tag good">Versão salva</span>':'<span class="tag neutral">Ainda não salvo</span>'}${state.demo?'<span class="tag blue">Dados fictícios</span>':''}<button type="button" class="btn ghost small" data-view="projetos">Trocar projeto</button></div></div>`;}
function steps(){return `<div class="steps" role="navigation" aria-label="Etapas da avaliação">${stageNames.map((n,i)=>`<button type="button" data-step="${i}" class="step ${i===state.step?'on':i<state.step?'done':''}" ${i===state.step?'aria-current="step"':''}><span class="n">${i+1}</span>${n}</button>`).join('')}</div>`;}
function input(name,val,type='text',attrs=''){return `<input name="${esc(name)}" type="${type}" value="${esc(val)}" ${attrs}/>`;}
function field(name,title,control,help=''){return `<div class="field"><label for="${name}">${esc(title)}</label>${control}${help?`<small>${esc(help)}</small>`:''}</div>`;}
function select(name,options,value){return `<select id="${name}" name="${name}">${options.map(x=>{let [v,l]=Array.isArray(x)?x:[x,x];return `<option value="${esc(v)}" ${String(value)===String(v)?'selected':''}>${esc(l)}</option>`}).join('')}</select>`;}
const componentOptions = [['DESCONHECIDA','Ainda não sei'],['SIM','Presente'],['NAO','Ausente']];
function renderProfile(){
  const c=state.case,byKind=Object.fromEntries(c.components.map(x=>[x.kind,x.presence]));
  let primary=['corpo','tampa','rotulo','adesivo','tinta','sleeve'];let extra=Object.keys(state.meta.component_labels).filter(x=>!primary.includes(x));
  let cmp=keys=>keys.map(k=>`<div class="checkrow"><label for="cmp-${esc(k)}">${esc(state.meta.component_labels[k])}</label>${select('cmp-'+k,componentOptions,byKind[k]||'DESCONHECIDA')}</div>`).join('');
  return `<div class="split"><section class="panel"><div class="headrow"><div><h2>1. Conhecer a embalagem</h2><p class="subtle">Começa com os dados básicos. Não é preciso conhecer todas as propriedades agora.</p></div><span class="tag blue">Etapa 1 de 4</span></div>
  <form id="profile-form"><div class="formgrid" style="margin-top:20px">
  ${field('product_name','Nome da embalagem',input('product_name',c.product_name,'text','id="product_name" required'))}
  ${field('design_version','Versão do design',input('design_version',c.design_version||'v1','text','id="design_version" required'))}
  ${field('project_id','Projeto / família',input('project_id',c.project_id,'text','id="project_id" required'), 'Use o mesmo ID de projeto para relacionar versões A e B.')}
  ${field('product_id','Identificador da embalagem',input('product_id',c.product_id,'text','id="product_id" required'))}
  ${field('material_corpo','Material do corpo',select('material_corpo',[['','Ainda não informado'],'PET','PLA','PVC','PP','PE','PETG','outro'],factValue('material_corpo')))}
  ${field('transparencia_corpo','Transparência',select('transparencia_corpo',[['','Ainda não informado'],'transparente','opaco'],factValue('transparencia_corpo')))}
  ${field('cor_corpo','Cor do corpo',select('cor_corpo',[['','Ainda não informado'],'incolor','azul-claro','preta','outra'],factValue('cor_corpo')))}
  ${field('capacidade_ml','Capacidade nominal (mL)',input('capacidade_ml',factValue('capacidade_ml'),'number','id="capacidade_ml" min="1" max="100000" step="any" placeholder="500"'))}
  </div><h3 style="margin-top:25px">Quais componentes estão presentes?</h3><p class="subtle">Ausente não é o mesmo que desconhecido.</p><div class="checklist">${cmp(primary)}</div>
  <details class="moredata"><summary>Outros componentes (vedantes, válvulas, barreiras etc.)</summary><div class="checklist" style="margin-top:14px">${cmp(extra)}</div></details>
  <div class="help warning">Os valores digitados são <b>declarações</b> até terem revisão ou evidência. Mesmo com informações faltantes, podes solicitar uma avaliação parcial.</div>
  <div class="buttons"><button class="btn" type="submit">Salvar e continuar →</button><button class="btn secondary" type="button" data-step="3">Ir para resultados</button></div></form></section>
  <aside class="sidebar-note"><h3>Antes de começar</h3><p>O PET Circular avalia garrafas PET transparentes incolores ou azul-claras, dentro dos critérios disponíveis na matriz.</p><p>O cadastro de componentes é independente dos materiais descritos no PDF. A presença deve ser informada por ti.</p><p>O motor não emite classe global nem certificação.</p></aside></div>`;
}
const manualFocus=['material_corpo','transparencia_corpo','cor_corpo','capacidade_ml','material_tampa','polimero_rotulo','densidade_rotulo','cobertura_nao_pet_pct','comportamento_adesivo','fixacao_rotulo','desprendimento','sleeve_polimero','sleeve_densidade'];
function renderData(){
  let tab=state.tab,ex=state.extraction;
  const t=names=>names.map(([v,l])=>`<button type="button" data-tab="${v}" class="${v===tab?'sel':''}" aria-pressed="${v===tab}">${esc(l)}</button>`).join('');
  const fields=state.meta.fields;const keys=groupedFields(fields).flatMap(g=>g[1]);const k=keys.includes(state.manualKey)?state.manualKey:keys[0];state.manualKey=k;
  let docs=state.case.documents.map(d=>[d.id,d.filename]);
  return `<div class="split"><section class="panel"><h2>2. Adicionar informações técnicas</h2><p class="subtle">Escolhe a forma mais simples. É possível combinar um PDF com preenchimento manual.</p>
  <div class="seg" role="group" aria-label="Método de entrada">${t([['pdf','Enviar PDF'],['manual','Preencher manualmente'],['json','Importar JSON']])}</div>
  ${tab==='pdf'?`<form id="extract-form"><div class="upload"><strong style="font-size:19px">Enviar uma ficha técnica</strong><p>PDF pesquisável · até 12 MB · até 35 páginas</p><input id="pdf-file" name="file" type="file" accept="application/pdf,.pdf" aria-label="Ficha técnica PDF" required/></div><div class="help"><b>Privacidade:</b> o modo local não envia dados para serviço externo. PDFs originais não são armazenados no histórico.</div>
  <details style="margin-top:17px"><summary>Opções de extração</summary><div class="field" style="margin-top:14px"><label for="pdf-mode">Método</label>${select('pdf-mode',[['local','Local — sem API'],['api','IA externa — requer autorização']], 'local')}</div><div id="external-doc-options" hidden><p class="subtle">O texto extraído do PDF será enviado à API externa se autorizado. Não utilize documentos sigilosos sem permissão.</p>${field('doc-key','Chave da API (não armazenada)',`<input id="doc-key" type="password" autocomplete="off"/>`)}<label class="togglecheck"><input id="doc-consent" type="checkbox"/> Autorizo o envio do texto deste documento à API externa.</label></div></details>
  <div class="buttons"><button class="btn" type="submit">Ler PDF e revisar dados →</button><button class="btn secondary" type="button" data-step="2">Ver informações registradas</button></div></form>`:''}
  ${tab==='manual'?`<form id="manual-form"><div class="formgrid">
   ${field('manual-key','Informação a registrar',`<select id="manual-key" name="manual-key">${manualOptions(fields)}</select>`,'Os dados básicos do corpo e capacidade já estão na etapa 1. Escolha um atributo adicional.')}
   ${field('manual-value','Valor',input('manual-value',oldFact(k)?.value??'','text','id="manual-value" placeholder="Um único valor verificável" required'), 'Para material e densidade, registre dois campos separados. Ex.: material da tampa = PP; densidade da tampa = 0,90 g/cm³.')}
   ${field('manual-unit','Unidade (quando aplicável)',input('manual-unit',oldFact(k)?.unit??'','text','id="manual-unit" placeholder="Ex.: g/cm³"'))}
   ${field('manual-document','Documento associado (opcional)',select('manual-document',[['','Sem documento'],...docs],''))}
   ${field('manual-reviewer','Responsável pela conferência',input('manual-reviewer','','text','id="manual-reviewer" placeholder="Nome / identificação"'))}
  </div><label class="togglecheck" style="margin-top:17px"><input id="manual-confirm" type="checkbox"/> Confirmar este dado após revisão humana (exige responsável)</label><label class="togglecheck" style="margin-top:10px"><input id="manual-ack" type="checkbox"/> Verifiquei o valor e a evidência ou origem informada</label>
  <div class="help"><b>Importante:</b> PET-02 considera somente polímeros adicionais incorporados ao CORPO. PP/PEAD na tampa ou BOPP no rótulo pertencem a outros critérios. Não digite alternativas como “PEAD ou PP” em um campo de material: registre o material conhecido ou mantenha pendente.<br/>Sem confirmação, o sistema registra o valor como <b>declarado</b> e não presume compatibilidade a partir dele. Campos confirmados exigem identificação do revisor.</div>
  <div class="buttons"><button class="btn" type="submit">Registrar informação</button><button type="button" class="btn secondary" data-step="2">Revisar informações →</button></div></form>`:''}
  ${tab==='json'?`${renderImportBox('evaluation')}`:''}
  ${ex?`<div class="help success"><strong>Documento processado:</strong> ${esc(ex.document.filename)} · ${ex.candidates.length} propostas para revisão. Nenhum valor foi confirmado automaticamente. <button class="inline-link" data-step="2" type="button">Ir à revisão</button></div>`:''}
  </section><aside class="sidebar-note"><h3>Evitar dúvidas</h3><ul><li>Um documento é a fonte; não confirma automaticamente os dados.</li><li>Confirmações registram trecho, página e responsável.</li><li>PDF digitalizado exige OCR, ainda não disponível.</li><li>Se não tens documento, começa pelo cadastro manual.</li></ul></aside></div>`;
}
function renderImportBox(where){
  const p=state.importPreview;
  return `<div class="project-picker"><div class="field"><label for="import-file-${where}">Selecionar dados de um projeto (.json)</label><input id="import-file-${where}" type="file" accept=".json,application/json" data-import-file="${where}"/></div><p class="subtle">Aceita somente JSON de projeto exportado pelo PET Circular (não relatórios de resultado, arquivos genéricos ou documentos convertidos para JSON). O aplicativo mostra a identidade antes de substituir.</p>
  ${p?`<div class="compare-mini" style="margin:12px 0"><span>Prévia do projeto selecionado</span><strong>${esc(p.product_name)}</strong><span>ID ${esc(p.product_id)} · ${esc(p.design_version)} · ${p.facts.length} informações técnicas · presença definida em ${knownCount(p)} de 11 componentes</span></div><button class="btn" data-action="confirm-import">Confirmar substituição do projeto ativo</button>`:''}</div>`;
}
function renderReview(){
  const ex=state.extraction,c=state.case;
  let rows=(ex?.candidates||[]).map((x,i)=>`<tr><td><input type="checkbox" name="accept-${i}" aria-label="Aceitar ${esc(x.key)}"/></td><td><b>${esc(label(x.key))}</b><div class="mini">${esc(x.key)}</div></td><td><input type="text" name="value-${i}" value="${esc(x.value)}" aria-label="Valor proposto para ${esc(label(x.key))}"/></td><td><span class="proof">Página ${esc(x.page)} · ${esc(ex.document.filename)}<br/>“${esc(x.quote)}”</span></td><td><span class="tag pending">Extraído — não confirmado</span>${oldFact(x.key)?`<div class="mini">Valor atual: ${esc(oldFact(x.key).value)} (${esc(oldFact(x.key).evidence_status)})</div><label class="togglecheck small"><input type="checkbox" name="overwrite-${i}"/> Substituir o valor confirmado existente, após conferir</label>`:'<span class="mini">Novo campo; não há valor anterior a substituir</span>'}</td></tr>`).join('');
  const factRows=c.facts.map(f=>`<tr><td>${esc(label(f.key))}<div class="mini">${esc(f.key)}</div></td><td>${esc(f.value)} ${esc(f.unit||'')}</td><td>${f.evidence_status==='CONFIRMADO'?'<span class="tag good">Confirmado</span>':'<span class="tag pending">'+esc(f.evidence_status.toLowerCase())+'</span>'}</td><td>${esc((f.evidence_ids||[]).join(', ')||'Sem documento')}</td></tr>`).join('');
  return `<section class="panel"><div class="headrow"><div><h2>3. Conferir as informações</h2><p class="subtle">Marque apenas valores comprovados pelo trecho do PDF. “Extraído” significa sugestão pendente, não dado confirmado. A opção de substituir só aparece quando já existe um valor.</p></div><span class="tag pending">${ex?ex.candidates.length+' sugestões pendentes':'Revisão manual'}</span></div>
  ${ex?`<div class="help">Fonte: <b>${esc(ex.document.filename)}</b> · ID ${esc(ex.document.id)} · SHA-256 ${esc(ex.document.sha256.slice(0,16))}... · ${ex.pages} página(s). Confira os trechos citados antes de aceitar.</div>
  ${rows?`<form id="review-form"><div class="review-table"><table><thead><tr><th>Selecionar</th><th>Informação</th><th>Valor proposto</th><th>Trecho de evidência</th><th>Estado</th></tr></thead><tbody>${rows}</tbody></table></div>
  <div class="field" style="max-width:450px;margin-top:20px"><label for="reviewer">Responsável pela revisão</label><input id="reviewer" name="reviewer" required placeholder="Nome ou identificação"/></div>
  <div class="buttons"><button class="btn" type="submit">Confirmar os dados selecionados</button><button type="button" class="btn ghost" data-action="discard-extraction">Descartar propostas</button></div></form>`:'<p class="is-empty">O PDF não apresentou campos reconhecidos no modo escolhido. Podes cadastrar informações manualmente.</p>'}`:
  `<div class="help">Não há propostas de PDF aguardando revisão. Podes conferir as informações já registradas ou adicionar mais dados.</div>`}
  <h3 style="margin-top:26px">Informações já registradas</h3>
  ${factRows?`<div class="review-table"><table><thead><tr><th>Campo</th><th>Valor</th><th>Estado</th><th>Evidência</th></tr></thead><tbody>${factRows}</tbody></table></div>`:'<div class="is-empty">Ainda não há informações técnicas cadastradas. Isso não impede uma avaliação parcial.</div>'}
  <div class="buttons"><button class="btn" data-step="3">Avaliar com os dados disponíveis →</button><button class="btn ghost" data-step="1">Adicionar dados</button></div></section>`;
}
function ruleCard(x){
  const m=state.meta.rules[x.rule_id]||{};
  return `<article class="rule"><div class="rtitle"><strong>${esc(x.rule_id)} — ${esc(m.title||'Critério técnico')}</strong>${tag(x.status)}</div><p>${esc(x.reason)}</p>
  ${x.missing?.length?`<p><b>Informações ou métodos pendentes:</b> ${esc(x.missing.map(label).join(', '))}</p>`:''}
  <details><summary>Por que importa, recomendações, evidências e fontes</summary>
  ${x.recommendations?.length?`<p><b>Recomendação ativada:</b> ${esc(x.recommendations.join('; '))}</p>`:''}
  ${m.recommendation?`<p><b>Orientação da matriz:</b> ${esc(m.recommendation)}</p>`:''}
  ${m.limitation?`<p><b>Limitação:</b> ${esc(m.limitation)}</p>`:''}
  <p class="source"><b>Evidências:</b> ${esc((x.evidence_ids||[]).join(', ')||'Não vinculadas')}<br><b>Fontes:</b> ${(x.sources||[]).map(code=>{let link=state.meta.sources[code]?.['URL oficial / DOI'];return link&&/^https:\/\//.test(link)?`<a href="${esc(link)}" rel="noopener noreferrer" target="_blank">${esc(code)}</a>`:esc(code)}).join(', ')}</p>
  </details></article>`;
}
function renderAssistant(){
  const ans=state.assistant;
  return `<section class="assistant"><h3>Ajuda para interpretar</h3><p class="subtle">Pergunte sobre os resultados atuais. A explicação não altera nenhum status.</p>
  <div class="qs" style="display:flex;flex-wrap:wrap;gap:7px;margin:10px 0"><button class="answer-trigger" data-question="Quais incompatibilidades foram identificadas e o que preciso corrigir?">O que devo corrigir?</button><button class="answer-trigger" data-question="Por que a PET-05 está inconclusiva ou não compatível neste produto?">Por que a PET-05?</button></div>
  <form id="assistant-form"><div class="field"><label for="assistant-question">Sua pergunta</label><textarea id="assistant-question" name="question" maxlength="2000" required placeholder="Ex.: Quais informações faltam para avaliar o rótulo?"></textarea></div>
  <details style="margin:12px 0"><summary>Modo de resposta</summary><div class="field"><label for="assistant-mode">Método</label>${select('assistant-mode',[['local','Local — rastreável, sem API'],['api','IA externa — requer autorização']], 'local')}</div><div id="external-assistant-options" hidden><p class="subtle">A pergunta e os resultados relevantes serão enviados a um provedor externo. Evite dados confidenciais sem autorização.</p><div class="field"><label for="assistant-key">Chave da API (não salva)</label><input type="password" id="assistant-key" autocomplete="off"/></div><label class="togglecheck"><input type="checkbox" id="assistant-consent"/> Autorizo o envio da pergunta e do contexto para a API externa.</label></div></details>
  <button class="btn small" type="submit">Consultar assistente</button></form>
  ${ans?`<div class="answer open" aria-live="polite"><b>${ans.mode==='LOCAL'?'Resposta local fundamentada':'Resposta assistida por IA externa'}</b><div>${md(ans.answer)}</div>${ans.sources?.length?`<p><b>Fontes:</b> ${ans.sources.map(s=>{let url=s.url||s['URL oficial / DOI'];return url&&/^https:\/\//.test(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(s.code||s.id||s.title||'Fonte')}</a>`:esc(s.code||s.id||'Fonte')}).join(', ')}</p>`:''}</div>`:''}
  </section>`;
}
function md(s){return esc(s).replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').split(/\n\s*\n/).map(x=>`<p>${x.replaceAll('\n','<br/>')}</p>`).join('');}
function renderResults(){const r=state.report;
  if(!r)return `<section class="panel"><h2>4. Entender os resultados</h2><p>Já podes avaliar uma embalagem com os dados disponíveis. Informações ausentes permanecem inconclusivas; nenhuma conclusão é presumida.</p><div class="help warning">A avaliação é individual por critério e não representa classe global ou certificação.</div><div class="buttons"><button class="btn" data-action="assess">Avaliar com os dados disponíveis</button><button class="btn secondary" data-step="1">Adicionar informações</button></div></section>`;
  let n=counts(r),priority=[...r.results.filter(x=>x.status==='NAO_COMPATIVEL'),...r.results.filter(x=>x.status==='INCONCLUSIVO')];
  return `<div class="results-toolbar"><div class="heading"><h2>4. Entender os resultados</h2><p>${esc(r.product_name)} · matriz ${esc(r.matrix_version)}, motor ${esc(r.engine_version)}</p></div><div class="buttons" style="margin:0"><button class="btn secondary small" data-action="assess">Reavaliar</button><button class="btn ghost small" data-action="export-report">Exportar relatório</button></div></div>
  <div class="stat-grid"><div class="stat problem"><strong>${n.NAO_COMPATIVEL}</strong><small>Não compatíveis</small></div><div class="stat pending"><strong>${n.INCONCLUSIVO}</strong><small>Inconclusivos</small></div><div class="stat good"><strong>${n.COMPATIVEL}</strong><small>Compatíveis</small></div><div class="stat"><strong>15</strong><small>Critérios examinados</small></div></div>
  <div class="help warning"><strong>Interpretação:</strong> resultado por critérios, sem classe global de reciclabilidade ou certificação. ${r.scope==='FORA'?'O produto está fora do recorte técnico, o que não significa que seja irreciclável.':''}</div>
  <div class="split" style="margin-top:20px"><section class="panel"><h3>O que precisa de atenção</h3><p class="subtle">Problemas concretos primeiro. Depois, dados e métodos pendentes.</p>
  ${priority.length?priority.map(ruleCard).join(''):'<p class="help success">Nenhuma incompatibilidade ou pendência encontrada nos critérios listados; isto não significa classificação global.</p>'}
  <details style="margin-top:20px"><summary><b>Ver todas as 15 regras</b></summary>${r.results.map(ruleCard).join('')}</details>
  <div class="buttons"><button class="btn" data-view="comparacao">Comparar com outra versão →</button><button class="btn ghost" data-step="0">Editar embalagem</button></div></section>
  <aside><div class="sidebar-note"><h3>Próximos passos</h3><p>${n.NAO_COMPATIVEL?`Há ${n.NAO_COMPATIVEL} critério(s) não compatível(eis). Revise as recomendações e registre mudanças como uma nova versão.`:'Nenhuma incompatibilidade confirmada neste conjunto de dados.'}</p><p>${n.INCONCLUSIVO?`Há ${n.INCONCLUSIVO} critério(s) inconclusivo(s). Solicite evidências e metodologias necessárias.`:'Verifique a documentação e os limites científicos antes de tirar conclusões.'}</p><div class="help"><b>Atenção:</b> ensaio, medição e validação metodológica são situações distintas.</div><div class="buttons"><button class="btn secondary small" data-action="save-snapshot">Salvar versão avaliada</button></div></div>${renderAssistant()}</aside></div>`;
}
function renderEvaluation(){
  if(!state.case)return;
  $('#page-avaliacao').innerHTML=`<div class="heading"><span class="eyebrow">Percurso guiado, não obrigatório</span><h1>Avaliar uma embalagem</h1><p>Podes voltar, alterar os dados e avaliar mesmo com informações faltantes.</p></div>${workspace()}${steps()}
  ${state.step===0?renderProfile():state.step===1?renderData():state.step===2?renderReview():renderResults()}`;
}
function optionSelect(id,selected){
  let opts=[['demo:A','Exemplo sintético — Design A'],['demo:B','Exemplo sintético — Design B']];
  if(state.report&&!state.stale)opts.push(['active','Avaliação ativa — '+state.case.product_name]);
  opts.push(...state.snapshots.filter(x=>x.has_result).map(x=>['snap:'+x.id,`Versão salva #${x.id} — ${x.product_name} (${x.design_version})`]));
  opts.push(...Object.keys(state.uploads).map(k=>['upload:'+k,'Relatório importado '+k]));
  return select(id,opts,selected);
}
const categoryNames={criterio_favoravel:'Critério favorável no B',ainda_pendente:'Não compatível → inconclusivo',pendencia_sanada:'Pendência sanada',novo_problema:'Nova incompatibilidade',pendencia_persistente:'Pendência persistente',sem_mudanca:'Sem mudança conclusiva'};
function renderComparison(){
 let c=state.comparison;
 let output=c?`<div class="comparison-grid" style="margin-top:20px"><div class="compare-mini"><span>VERSÃO ANTERIOR</span><strong>${esc(c.design_a.product_name)}</strong><span>${esc(c.design_a.design_version)}</span></div><div class="compare-mini"><span>VERSÃO PROPOSTA</span><strong>${esc(c.design_b.product_name)}</strong><span>${esc(c.design_b.design_version)}</span></div></div>
 <div class="stat-grid" style="grid-template-columns:repeat(3,1fr)"><div class="stat good"><strong>${c.counts.criterio_favoravel||0}</strong><small>Não compatíveis → compatíveis</small></div><div class="stat pending"><strong>${c.counts.ainda_pendente||0}</strong><small>Não compatíveis → inconclusivos</small></div><div class="stat pending"><strong>${c.counts.pendencia_persistente||0}</strong><small>Inconclusivos em ambos</small></div></div>
 ${c.warnings?.length?`<div class="help warning">${c.warnings.map(esc).join('<br/>')}</div>`:''}
 <section class="panel"><div class="headrow"><div><h2>Mudanças por critério</h2><p class="subtle">Sem porcentagem global nem aprovação presumida.</p></div><span class="tag blue">Motor determinístico</span></div>
 <div class="comp-row comphead"><span>Regra</span><span>Antes</span><span>Depois</span><span>Interpretação</span></div>
 ${c.changes.map(x=>`<div class="comp-row"><strong>${esc(x.rule_id)}</strong><span>${tag(x.status_a)}</span><span>${tag(x.status_b)}</span><div class="cat subtle"><b>${esc(categoryNames[x.category]||'Transição')}</b><br/>${esc(x.description)}${x.missing_b?.length?`<br/><b>Pendências B:</b> ${esc(x.missing_b.map(label).join(', '))}`:''}<details><summary>Ver evidências</summary><p>Antes: ${esc(x.evidence_a.join(', ')||'não vinculada')}<br/>Depois: ${esc(x.evidence_b.join(', ')||'não vinculada')}</p></details></div></div>`).join('')}
 <div class="help warning"><b>Nota:</b> ${esc(c.method_note)}</div></section>`:
 `<section class="panel"><h2>Uma comparação responsável</h2><p>Selecione duas avaliações. O aplicativo compara estados calculados pelo motor — não inventa uma classe global e não pressupõe que inconclusivo significa compatível.</p><div class="help">Para experimentar agora, mantenha os exemplos A e B e clique em <b>Comparar as versões</b>.</div></section>`;
 $('#page-comparacao').innerHTML=`<div class="heading"><span class="eyebrow">Comparação com rastreabilidade</span><h1>O que mudou entre os designs?</h1><p>Compare versões salvas, exemplos ou relatórios exportados. A transição de estado não comprova mudança física por si só.</p></div>
 <div class="panel" style="margin-top:24px"><div class="formgrid">
 ${field('compare-a','Versão anterior',optionSelect('compare-a',state.compareA))}
 ${field('compare-b','Versão proposta',optionSelect('compare-b',state.compareB))}
 </div><div class="buttons"><button class="btn" data-action="run-compare">Comparar as versões</button><button class="btn secondary" data-action="demo-compare">Usar demonstração A/B</button></div>
 <details style="margin-top:17px"><summary>Importar relatórios JSON exportados</summary><div class="formgrid" style="margin-top:15px">${field('report-a-file','Relatório anterior (.json)',`<input id="report-a-file" type="file" accept=".json,application/json" data-report-file="A"/>`)}${field('report-b-file','Relatório proposto (.json)',`<input id="report-b-file" type="file" accept=".json,application/json" data-report-file="B"/>`)}</div></details></div>${output}`;
}
function renderProjects(){
  let items=state.snapshots.map(s=>`<div class="project"><div><span class="tag neutral">Salvo em ${esc(s.saved_at.replace('T',' ').slice(0,16))}</span><h3>${esc(s.product_name)}</h3><p>ID ${esc(s.product_id)} · ${esc(s.design_version)} · ${s.has_result?'com avaliação':'rascunho'}</p></div><button class="btn secondary" data-snapshot="${s.id}">Abrir versão #${s.id}</button></div>`).join('');
  $('#page-projetos').innerHTML=`<div class="heading"><span class="eyebrow">Continuidade e versionamento</span><h1>Projetos e versões</h1><p>Salva versões localmente no computador que executa o servidor. Os PDFs originais não são arquivados.</p></div>
  <div class="panel" style="margin-top:25px"><h2>Produto ativo</h2>${workspace()}<div class="buttons"><button class="btn" data-action="save-snapshot">Salvar versão atual</button><button class="btn secondary" data-action="export-case">Exportar dados do projeto</button>${state.report?'<button class="btn ghost" data-action="export-report">Exportar relatório de avaliação</button>':''}</div></div>
  <div class="panel"><h2>Começar ou importar um projeto</h2><div class="buttons"><button class="btn" data-action="new-case">Criar uma embalagem</button><button class="btn secondary" data-demo="A">Abrir exemplo sintético A</button><button class="btn secondary" data-demo="B">Abrir exemplo sintético B</button></div>${renderImportBox('projects')}</div>
  <div class="panel"><div class="headrow"><div><h2>Histórico de versões locais</h2><p class="subtle">Cada salvamento cria uma nova versão. A anterior continua disponível.</p></div><button class="btn ghost small" data-action="refresh-projects">Atualizar lista</button></div>
  <div class="projectlist">${items||'<div class="is-empty">Nenhuma versão salva ainda. Salva o produto atual para poder retomá-lo.</div>'}</div></div>`;
}
function downloadFile(filename,obj){let blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);}
async function saveSnapshot(){const r=await api('/api/snapshots',{case:state.case,include_report:!!state.report&&!state.stale});state.dirty=false;state.saved=true;await refreshSnapshots();notify('Versão #'+r.id+' salva neste computador.');renderCurrent();}
async function refreshSnapshots(){state.snapshots=(await api('/api/snapshots')).items;}
async function loadDemo(which){if(!changeGuard())return;const r=await api('/api/examples/'+which);newCase(r.case,{demo:true,report:r.report,dirty:false});notify('Exemplo sintético '+which+' carregado. Não representa evidência física.');show('avaliacao',3);}
async function previewImport(file){if(!file)return; if(file.size>2_000_000)throw Error('Arquivo JSON acima de 2 MB.');let buf=await file.arrayBuffer();const r=await api('/api/projects/import',new TextDecoder().decode(buf),{raw:true});state.importPreview=r.case;renderCurrent();notify('Prévia pronta. Confirme antes de substituir o produto ativo.');}
async function pickReport(file,kind){if(!file)return;if(file.size>2_000_000)throw Error('Relatório maior que 2 MB.');const obj=JSON.parse(await file.text());state.uploads[kind]=obj;if(kind==='A')state.compareA='upload:A';else state.compareB='upload:B';renderComparison();notify('Relatório '+kind+' selecionado. Clique em Comparar.');}
async function reportFromSelection(selection){if(selection==='active'){if(!state.report||state.stale)throw Error('Avalie o projeto ativo antes de compará-lo.');return state.report;}
  if(selection.startsWith('demo:'))return (await api('/api/examples/'+selection.slice(-1))).report;
  if(selection.startsWith('snap:')){const r=await api('/api/snapshots/'+selection.slice(5));if(!r.report)throw Error('Esta versão salva não contém avaliação.');return r.report;}
  if(selection.startsWith('upload:'))return state.uploads[selection.slice(-1)];throw Error('Seleção inválida.');}
async function runCompare(){let [a,b]=await Promise.all([reportFromSelection(state.compareA),reportFromSelection(state.compareB)]);state.comparison=(await api('/api/compare',{before:a,after:b})).comparison;renderComparison();}
async function saveProfile(form){const fd=new FormData(form);let details={};for(let k of ['product_name','design_version','project_id','product_id'])details[k]=fd.get(k).toString().trim();
  let comps={};for(let k of Object.keys(state.meta.component_labels))comps[k]=fd.get('cmp-'+k)||state.case.components.find(x=>x.kind===k)?.presence||'DESCONHECIDA';
  // Inputs are presented as simple declarations, never silently confirmed.
  let basic={};for(let k of ['material_corpo','transparencia_corpo','cor_corpo','capacidade_ml'])basic[k]=fd.get(k)||'';
  let res=await api('/api/projects/update',{case:state.case,details,components:comps,basic_facts:basic});let changed=JSON.stringify(res.case)!==JSON.stringify(state.case);
  if(changed)editCase(res.case);notify(res.notice);setStep(1);
}
async function saveManual(form){const fd=new FormData(form);let key=fd.get('manual-key'),value=fd.get('manual-value'),confirm=$('#manual-confirm')?.checked,ack=$('#manual-ack')?.checked;
 let res=await api('/api/projects/fact',{case:state.case,key,value,unit:fd.get('manual-unit'),doc_id:fd.get('manual-document'),reviewer:fd.get('manual-reviewer'),confirm,acknowledged:ack});editCase(res.case);notify('Informação registrada como '+(confirm?'confirmada':'declarada')+'.');renderEvaluation();}
async function extract(form){const f=$('#pdf-file')?.files?.[0];if(!f)throw Error('Selecione um PDF.');if(f.size>12*1024*1024)throw Error('PDF maior que 12 MB.');let mode=$('#pdf-mode')?.value||'local';const data=new FormData();data.set('file',f);data.set('product',JSON.stringify(state.case));data.set('mode',mode);data.set('consent',$('#doc-consent')?.checked?'true':'false');if(mode==='api'){data.set('api_key',$('#doc-key')?.value||'');data.set('model','gpt-4.1-mini');}
  const r=await api('/api/documents/extract',data,{form:true});editCase(r.case);state.extraction=r;notify(`PDF lido: ${r.candidates.length} sugestões aguardam revisão humana.`);setStep(2);}
async function review(form){const ex=state.extraction;if(!ex)throw Error('Não há propostas para revisar.');const d=new FormData(form);let decisions=ex.candidates.map((c,i)=>({accept:d.get('accept-'+i)!==null,value:d.get('value-'+i),overwrite:d.get('overwrite-'+i)!==null}));if(!decisions.some(x=>x.accept))throw Error('Selecione ao menos uma proposta a confirmar.');let reviewer=String(d.get('reviewer')||'');
 const r=await api('/api/documents/review',{case:state.case,extraction_token:ex.extraction_token,decisions,reviewer});editCase(r.case);state.extraction=null;notify(`${r.accepted.length} informação(ões) confirmada(s). ${r.skipped.length?'Alguns campos foram ignorados por já estarem confirmados.':''}`);setStep(3);}
async function getAssessment(){const r=await api('/api/assessment',{case:state.case});state.report=r.report;state.stale=false;state.assistant=null;notify('Avaliação calculada pelo motor das 15 regras.');setStep(3);}
async function askAssistant(question,mode='local',key='',consent=false){if(!state.report||state.stale)throw Error('Execute a avaliação antes de consultar o assistente.');let r=await api('/api/assistant',{case:state.case,question,mode,api_key:key,consent,model:'gpt-4.1-mini'});state.assistant=r.response;renderEvaluation();}
async function openSnapshot(id){if(!changeGuard())return;const r=await api('/api/snapshots/'+id);newCase(r.case,{report:r.report,dirty:false,saved:true});notify('Versão #'+id+' aberta.');show('avaliacao',r.report?3:0);}
function exportCase(){downloadFile(`pet_circular_${state.case.product_id}_entrada.json`,state.case);}
function exportReport(){if(!state.report||state.stale)throw Error('Não há uma avaliação atual para exportar.');downloadFile(`pet_circular_${state.case.product_id}_resultado.json`,state.report);}
function handleAction(action){return act(async()=>{switch(action){
  case 'assess':return getAssessment();case 'save-snapshot':return saveSnapshot();case 'refresh-projects':await refreshSnapshots();return renderProjects();
  case 'new-case':if(changeGuard()){newCase(state.meta.new_case,{dirty:true});notify('Nova embalagem criada.');show('avaliacao',0);}return;
  case 'confirm-import':if(!state.importPreview)throw Error('Selecione um JSON antes de confirmar.');if(!changeGuard())return;newCase(state.importPreview,{dirty:true});notify('Produto '+state.case.product_id+' importado. Confirmação recebida.');show('avaliacao',0);return;
  case 'discard-extraction':state.extraction=null;notify('Propostas descartadas. O registro do documento permanece no projeto.');return setStep(1);
  case 'export-case':return exportCase();case 'export-report':return exportReport();
  case 'run-compare':return runCompare();case 'demo-compare':state.compareA='demo:A';state.compareB='demo:B';return runCompare();
  default:throw Error('Operação desconhecida.');}})}
document.addEventListener('click',e=>{
  let a=e.target.closest('[data-action]');if(a){e.preventDefault();return handleAction(a.dataset.action);}
  let d=e.target.closest('[data-demo]');if(d){e.preventDefault();return act(()=>loadDemo(d.dataset.demo));}
  let ss=e.target.closest('[data-snapshot]');if(ss){e.preventDefault();return act(()=>openSnapshot(ss.dataset.snapshot));}
  let q=e.target.closest('[data-question]');if(q){e.preventDefault();let text=q.dataset.question;const el=$('#assistant-question');if(el)el.value=text;return act(()=>askAssistant(text));}
  let n=e.target.closest('[data-view]');if(n){e.preventDefault();return show(n.dataset.view,n.dataset.step);}
  let st=e.target.closest('[data-step]');if(st){e.preventDefault();return setStep(st.dataset.step);}
  let tab=e.target.closest('[data-tab]');if(tab){e.preventDefault();state.tab=tab.dataset.tab;return renderEvaluation();}
});
document.addEventListener('change',e=>{
  const el=e.target;
  if(el.matches('[data-import-file]'))return act(()=>previewImport(el.files?.[0]));
  if(el.matches('[data-report-file]'))return act(()=>pickReport(el.files?.[0],el.dataset.reportFile));
  if(el.id==='manual-key'){state.manualKey=el.value;return renderEvaluation();}
  if(el.id==='pdf-mode'){const opt=$('#external-doc-options');if(opt)opt.hidden=el.value!=='api';}
  if(el.id==='assistant-mode'){const opt=$('#external-assistant-options');if(opt)opt.hidden=el.value!=='api';}
  if(el.id==='compare-a')state.compareA=el.value;
  if(el.id==='compare-b')state.compareB=el.value;
});
document.addEventListener('submit',e=>{e.preventDefault();let form=e.target;return act(async()=>{
  if(form.id==='profile-form')return saveProfile(form);
  if(form.id==='manual-form')return saveManual(form);
  if(form.id==='extract-form')return extract(form);
  if(form.id==='review-form')return review(form);
  if(form.id==='assistant-form')return askAssistant(form.elements.question.value,$('#assistant-mode')?.value,$('#assistant-key')?.value,$('#assistant-consent')?.checked);
});});
window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue='';}});
(async function boot(){try{const b=await api('/api/bootstrap');state.token=b.session_token;state.meta=b;newCase(b.new_case,{dirty:false});await refreshSnapshots();show('inicio');}catch(e){notify('Falha ao iniciar o servidor local: '+e.message,'error');}})();
