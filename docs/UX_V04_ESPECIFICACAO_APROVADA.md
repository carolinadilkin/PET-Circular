# PET Circular v0.4 — Especificação de experiência e interface

**Status:** proposta de design revisada; **não implementada no aplicativo**.  
**Data:** 03/11/2026 · **Referência:** aplicativo v0.3.1 (branch `feature/assistant-ecodesign-v0.3`), matriz científica v0.3.3 e relatórios sintéticos integrados A/B.  
**Objetivo de produto:** permitir que alguém sem conhecimento prévio da interface consiga avaliar uma embalagem PET, compreender limitações e comparar alternativas de ecodesign sem depender de um roteiro externo.

## 1. Parecer de UX

Aprovar **com alterações**. A proposta anterior acerta em trocar oito páginas técnicas por tarefas, mas um wizard linear rígido não atende bem casos com informações incompletas e ciclos de engenharia. O design aprovado deve adotar um **fluxo assistido flexível**, com sequência recomendada, possibilidade de pular etapas e retorno direto ao campo de origem a partir de pendências.

### Evidências de problema no aplicativo existente

- O `app.py` separa `Produto`, `Componentes`, `Dados técnicos`, `Evidências`, `IA · Documentos`, `Avaliação` e `Assistente` em páginas distintas. O usuário deve reconstruir a ordem correta.
- `Importar envelope JSON` ocorre na barra lateral, sem prévia comparativa dos dados que substituirão o produto ativo. No teste anterior, houve confusão entre selecionar arquivo, concluir importação e avaliar o produto certo.
- Um PDF em `Evidências` apenas registra metadados, enquanto o PDF em `IA · Documentos` efetua extração. Duas ações visualmente semelhantes têm consequências diferentes.
- `Componentes` utiliza onze opções técnicas com `SIM/NAO/DESCONHECIDA`, e a conclusão das regras depende da presença confirmada, mas a relação causal não está visível ao iniciante.
- O assistente local lê apenas a avaliação ativa, não compara históricos. A usuária percebeu essa limitação ao perguntar sobre Design A e B.
- A tela de resultados oferece visão detalhada de 15 regras, mas pouco suporte para priorização e continuidade.

## 2. Usuários e tarefas prioritárias (hipóteses a validar)

| Perfil | Trabalho principal | Necessidade | Modo sugerido |
|---|---|---|---|
| Designer/engenheiro de embalagem | Identificar mudanças antes de congelar o design | Caminho curto, próximos passos claros | Guiado |
| Responsável técnico ou de qualidade | Confirmar fatos, revisar fontes, detectar divergências | Visibilidade de evidência e autoria | Guiado + detalhes |
| Pesquisador/auditor | Auditar regra, matriz, métodos e limitações | Acesso a critérios e dados brutos | Avançado |

Não inferir que todos os usuários são especialistas em polímeros, mas tampouco substituir conteúdo científico por avaliações vagas de “bom/ruim”.

## 3. Arquitetura de informação aprovada

### Navegação principal (máximo quatro destinos)

1. **Início** — três ações: `Avaliar embalagem`, `Comparar designs`, `Continuar projeto`.
2. **Projetos** — lista e status dos projetos locais, suas versões e snapshots (com aviso sobre escopo do armazenamento).
3. **Avaliação** — espaço de trabalho com produto ativo, dados, evidências, avaliação e explicações.
4. **Comparação** — seleção de duas avaliações já executadas e apresentação por transição de status.

**Configurações e detalhes técnicos** ficam em um menu secundário, não nas ações de maior destaque. Modos local/API são apresentados no momento do upload ou da conversa, com informação de consentimento clara.

### Jornada de avaliação — checklist flexível

**0. Escolher a origem**: nova embalagem / exemplo demonstrativo / importar projeto JSON (não confundir com relatório JSON de resultado).  
**1. Definir a embalagem**: nome e versão; material/transparência/cor do corpo; inventário de componentes com `Presente / Ausente / Ainda não sei`.  
**2. Adicionar dados**: escolher `Enviar ficha técnica PDF` ou `Preencher manualmente`; se PDF, escolher `Extração local` como padrão. Mostrar limitações de PDF pesquisável, tamanho e páginas antes da seleção.  
**3. Revisar evidências**: tabela com `Campo | Valor proposto | Origem/página | Estado | Ação`; confirmar individualmente, rejeitar e editar mediante suporte documental. A presença do componente permanece declaração independente e explícita.  
**4. Ver avaliação**: botão `Avaliar com os dados disponíveis`, inclusive quando lacunas persistirem. Motor decide estados por critério; IA não decide estados.  
**5. Agir sobre resultados**: mostrar recomendações e lacunas acionáveis, permitir `Editar dado` e `Reavaliar`.  

Em cada etapa, exibir estado `Não iniciado / Em andamento / Revisado`; **não** usar percentual de “reciclabilidade” ou de “qualidade científica” baseado em quantidade de campos preenchidos. Um projeto com dados ausentes pode ser avaliado parcialmente sem ser marcado como tecnicamente completo.

## 4. Regras de interação não negociáveis

1. **Identidade persistente do caso:** nome, código, versão e tipo de dados (exemplo/real) sempre visíveis. Após importação, exibir comparação `produto atual → produto importado` e exigir `Substituir produto ativo`. Exibir número de fatos, componentes com presença conhecida, documentos e data.
2. **Proteção contra perda de trabalho:** salvar rascunho explícito; alterações não salvas e troca de projeto exigem aviso. `Criar novo`, `Abrir versão`, `Importar` não podem silenciosamente sobrescrever.
3. **Revisão de IA sem aprovação implícita:** mostrar trecho literal, página, nome/hash do documento, regra/necessidade e revisor. Ação `Confirmar dado` só após aprovação explícita. Proposta e confirmação não podem compartilhar mesmo estilo visual.
4. **Estados distintos:** `Presente / Ausente / Não informado` para componentes; `Proposto / Declarado / Confirmado / Conflitante` para fatos; `Compatível / Não compatível / Limitada / Inconclusivo / Não aplicável / Não acionada` para regras. Não colapsar estes níveis em um único selo de risco.
5. **Resultados explicáveis:** para cada regra mostrar `O que encontramos` → `Por que importa` → `O que fazer` → `Como comprovar` → `Fonte e ressalva`; a IA deve funcionar como complemento opcional.
6. **Sem promessas de classificação global:** banner curto e constante `Avaliação por critérios; sem classe global ou certificação` e detalhes ampliáveis. Não usar porcentagem de compatibilidade, nota verde global ou símbolo de certificação.
7. **Comparação responsável:** comparação determinística entre *relatórios de avaliação*, nunca por inferência livre do assistente. Garantir matriz/engine versionadas e alertar quando diferirem; A/B podem ter IDs diferentes, mas devem ser relacionados explicitamente ao mesmo projeto. Mostrar evidência e campos que mudaram quando disponível; relatórios somente com resultados não comprovam quais dados causaram a mudança.
8. **Controle de dados:** explicitar que o SQLite é local à máquina/servidor, o PDF original não é arquivado e a API externa exige consentimento específico; não prometer salvamento automático confiável até ser implementado/testado.
9. **Acessibilidade:** contraste WCAG 2.2 AA, foco visível, teclado e rótulos, estado textual além da cor, mensagens de erro específicas, leitura de status por tecnologias assistivas, responsividade. Testar compatibilidade efetiva do Streamlit, não presumir.
10. **Escopo PET transparente:** contextualizar antes de começar. Para fora do recorte, apresentar `Fora do escopo desta avaliação`, não `Não reciclável`.

## 5. Apresentação dos resultados

### Hierarquia

1. Cabeçalho: produto, versão, data e estado da avaliação (ex.: `Atual`/`Dados modificados — reavaliar`).
2. Resumo: quantidade de regras `Não compatível`, `Inconclusivo`, `Compatível`; em linha separada `Não aplicável`, `Não acionada`, `Limitada`. Somatório dos estados deve ser 15.
3. Lista priorizada: problemas concretos antes das pendências; dentro das pendências, mostrar quais dados precisam ser solicitados e a quem/onde, quando disponível.
4. Separar `Ensaios pendentes`, `Medições pendentes` e `Métodos ainda não homologados`. Um resultado `trial = NAO_REQUERIDO` não implica ausência de medições ou de limitações.
5. `Ver todas as 15 regras` e `Ver evidências/fontes` em detalhes expansíveis.
6. Assistente contextual com perguntas sugeridas; respostas devem citar somente fatos confirmados e IDs de fonte do resultado apresentado.

### Exemplo real da simulação integrada (dados sintéticos)

- A: PET-05, PET-09 e PET-18 **não compatíveis**; PET-04, PET-16 e PET-17 inconclusivas.
- B: PET-09 e PET-18 **compatíveis**; PET-05 mudou de **não compatível para inconclusiva**; PET-04, PET-16 e PET-17 permanecem inconclusivas.
- Comparador: `2 critérios passaram de não compatíveis a compatíveis`, `1 critério deixou de apontar incompatibilidade, mas continua inconclusivo`, `3 pendências persistem`. **Não** declarar “3 incompatibilidades resolvidas” ou “embalagem reciclável”.

## 6. Especificação das telas

| Tela | Componentes-chave | Ação primária | Erros/estados de atenção |
|---|---|---|---|
| Início | 3 cartões de tarefa, aviso de escopo, acesso a exemplo | Avaliar embalagem | Projeto não salvo / demo vs real |
| Definir embalagem | Nome, versão, seleção de componentes contextual | Salvar e continuar | Ausência desconhecida não equivale a ausente |
| Adicionar dados | PDF local (padrão), manual, importar JSON, requisitos | Ler PDF / registrar | PDF escaneado, grande, com senha, importação incompatível |
| Revisar | Tabela de candidatos, página/citação, confirmação por item | Confirmar selecionados | Documento divergente; edição sem evidência |
| Resultados | Resumo, problemas, pendências, explicações, fontes, assistente | Corrigir ou comparar | Resultado desatualizado após alteração |
| Comparar | Selecionar A/B, compatibilidade de matriz, diff por regra | Comparar | Dois resultados iguais, matriz diferente, sem resultado |
| Projetos | Lista de projetos e versões locais, exportação | Continuar | Rascunho perdido, ausência do PDF original |
| Avançado | Campos canônicos, IDs, JSON, matriz, logs | Inspecionar/exportar | Não modificar estado confirmado sem revisão |

## 7. Conteúdo e microcopy

| Texto atual | Preferir | Onde manter o termo técnico |
|---|---|---|
| Importar envelope JSON | Importar dados de um projeto (.json) | Detalhes avançados: `envelope de entrada` |
| Fatos técnicos | Informações técnicas | Exportação e auditoria |
| Componentes conhecidos: 2 | Presença definida em 2 de 11 componentes | Inventário, contagem técnica |
| Executar avaliação das 15 regras | Avaliar com os dados disponíveis | Cabeçalho de análise pode indicar 15 regras |
| Sem classe global | Resultado por critérios. Não é certificação de reciclabilidade | Detalhes metodológicos |
| Evidência confirmada | Dado confirmado após revisão humana | Metadados da evidência |
| Falta validacao_metodo_normativo_cobertura | Método de medição de cobertura ainda não validado | Detalhe: `validacao_metodo_normativo_cobertura` |
| Importação concluída | Produto **SYN-…** carregado: 30 informações técnicas, 11 componentes com presença definida | Confirmação de importação |

## 8. Comparador — algoritmo de transições para a UX

Para cada `rule_id`, identificar `status_A` e `status_B` e classificar a transição:

- `NAO_COMPATIVEL → COMPATIVEL`: `Critério com incompatibilidade não detectada na proposta B e avaliação compatível neste cenário` (com evidências do B, se disponíveis).
- `NAO_COMPATIVEL → INCONCLUSIVO`: `Incompatibilidade não indicada no B, mas critério ainda não comprovado`.
- `INCONCLUSIVO → COMPATIVEL`: `Pendência sanada nos dados avaliados`, com auditoria de evidências.
- `COMPATIVEL → NAO_COMPATIVEL`: `Nova incompatibilidade identificada`.
- `INCONCLUSIVO → INCONCLUSIVO`: `Pendente nos dois designs`; verificar se a causa mudou (comparar `missing`).
- Outras mudanças: exibir `Transição de estado` sem interpretar como melhoria automática, especialmente `NAO_APLICAVEL`, `NAO_ACIONADA`, `LIMITADA` e `FORA_ESCOPO`.

Não somar status como um índice global de reciclabilidade. Destacar se `matrix_version`, `engine_version` ou escopo diferirem. Preservar original imutável e armazenar histórico de comparação separadamente.

## 9. Design visual e responsividade

- Cores semafóricas apenas para estados de critérios, acompanhadas de texto e ícones; neutros no restante.
- Tipografia sem serifa, escala 14–32 px, largura de leitura limitada para explicações; tabelas com rolagem horizontal e equivalentes em cartões no celular.
- Desktop: barra superior com nome/versão ativa; tarefa central e coluna contextual opcional. Mobile: uma coluna e ações principais visíveis, sem painéis laterais persistentes.
- Formulários agrupados em 2–5 decisões por seção, com ajuda contextual curta e exemplos de unidades. Esconder chaves canônicas salvo nos detalhes avançados.
- Padrão visual: superfícies brancas, fundo neutro, verde-petróleo como identidade; vermelho e âmbar apenas para estados relevantes, respeitando contraste.

## 10. Plano de teste de usabilidade e métricas

**Pessoas:** 3–5 participantes por rodada exploratória, incluindo ao menos um não especialista em reciclagem e um especialista técnico. Não tratar esse tamanho como evidência estatística de desempenho. Fazer também teste de teclado, zoom e leitor de tela.

**Tarefas sem instruções externas:**

1. Criar projeto e importar uma ficha técnica PDF sintética.
2. Identificar por conta própria quais dados foram extraídos e confirmá-los conscientemente.
3. Dizer se um rótulo PVC foi classificado como incompatível e localizar a fonte da regra.
4. Comparar os designs A/B e explicar por que PET-05 continua inconclusiva no B.
5. Salvar, sair e retomar o projeto sem perder alterações (apenas depois da implementação desse recurso).

**Metas iniciais para validação** (*hipóteses*, não resultados medidos): ≥80% de conclusão independente por tarefa em uma rodada exploratória; 0 confirmações inadvertidas de dados extraídos; 0 interpretações equivocadas de `INCONCLUSIVO` como `COMPATIVEL`; importação compreendida antes de continuar; observação de tempo, erros, abandonos e comentários qualitativos. As metas devem ser calibradas com pesquisa posterior.

## 11. Planejamento de implementação (não executado)

- **Sprint 1 — Fundamentos:** modelo de estados do projeto, rotas por tarefa, resumo do caso ativo, proteção contra perda/overwrite e importação com prévia.
- **Sprint 2 — Captura guiada:** unificar upload/manual, revisão com proveniência e listas de componentes.
- **Sprint 3 — Resultados:** cards, lista de problemas, distinção testes/medições, edição com retorno e assistente contextual.
- **Sprint 4 — Comparação:** diff por regra + metadados/versões e UX de transições, testes A/B.
- **Sprint 5 — Qualidade:** teclado, contraste, foco/erros, teste com usuários e regressões de 15 regras. Ajustar arquitetura Streamlit conforme restrições observadas; não substituir motor científico.

### Critérios de aceitação de engenharia

- Nenhuma alteração não confirmada passa a `CONFIRMADO` por consequência de upload, importação ou sugestão.
- Resultado anterior é invalidado após alterações nos dados; não exibir status antigo como atual.
- Projeto ativo não muda sem ação explícita e resumo de importação/abertura.
- Exportação distingue entrada, relatório e comparação e identifica as versões do motor/matriz.
- Comparador A/B produz 2 resolvidas por critério, 1 pendente após incompatibilidade, 3 pendências persistentes na simulação.
- Acessibilidade e fluxo responsivo testados manualmente; manter testes unitários, smoke e CI.

## 12. Referências externas de design

- Nielsen Norman Group, *Progressive Disclosure*: https://www.nngroup.com/articles/progressive-disclosure/
- Nielsen Norman Group, *10 Usability Heuristics*: https://www.nngroup.com/articles/ten-usability-heuristics/
- GOV.UK, *Task list*: https://design-system.service.gov.uk/components/task-list/
- GOV.UK, *Check answers*: https://design-system.service.gov.uk/patterns/check-answers/
- GOV.UK, *Recover from validation errors*: https://design-system.service.gov.uk/patterns/validation/
- W3C, WCAG 2.2, *Error Identification*, *Status Messages*, *Contrast Minimum*: https://www.w3.org/WAI/WCAG22/Understanding/

## 13. O que o protótipo demonstra (e não demonstra)

`PROTOTIPO_NAVEGAVEL_v04.html` é uma **demonstração estática interativa de design**. Incorpora os resultados sintéticos A/B já produzidos para ilustrar o comportamento visual de comparação e dos estados; os dados e números não vêm de uma nova avaliação do motor. O protótipo **não processa PDFs ou JSON, não armazena dados, não utiliza API e não substitui a aplicação Streamlit**.
