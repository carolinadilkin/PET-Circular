# PET Circular — Registro de implementação da interface v0.4

**Status:** prévia funcional para homologação de UX. **Base:** app v0.3.1 + 15 regras da matriz 0.3.3, motor 0.1.0. **Não é certificação RecyClass.**

## Funcionalidades implementadas

| Requisito de UX | Implementação | Observação |
|---|---|---|
| Navegação por tarefas | `Início / Avaliação / Comparação / Projetos / Avançado` | Avançado é um destino secundário para investigadores |
| Checklist flexível | 4 etapas com retorno e avanço mesmo com campos faltantes | A ausência de dados resulta em estados inconclusivos, não em aprovações |
| Entrada documental ou manual | PDF pesquisável + extração local/API opcional + cadastro técnico | Sem OCR; parser local só cobre campos explicitamente rotulados |
| Revisão humana | Candidatos com citação/página, estado e ação explícita | Apenas revisão humana confirmada pode fornecer fatos `CONFIRMADO` |
| Presença de componentes | Seletor Presente/Ausente/Ainda não sei | Sem inferência por arquivo ou por material |
| Resultados contextualizados | Incompatíveis antes dos inconclusivos; pendências, fontes, ressalvas | Motor original, sem score global |
| Assistente contextual | Incorporado na etapa Resultados | Explica uma avaliação atual; não compara históricos sozinho |
| Comparação A/B | Motor determinístico de mudanças de status + evidências associadas | Veta comparabilidade automática com versões diferentes de matriz/motor |
| Proteção da troca de projetos | Prévia da importação, confirmação antes de substituir; novos projetos e snapshots exigem confirmação | Não há gravação automática; alerta de trabalho não salvo |
| Histórico | Todas as versões salvas consultáveis no SQLite; relatórios salvos selecionáveis no comparador | Armazenamento local, sem nuvem |
| Acesso técnico | Telas anteriores disponíveis em Avançado | Sem atalhos diretos de substituição |

## Critérios de aceitação automatizados

- 15 regras originais inalteradas e testes existentes aprovados.
- A/B reproduz 2 `NAO_COMPATIVEL → COMPATIVEL`, 1 `NAO_COMPATIVEL → INCONCLUSIVO` e 3 `INCONCLUSIVO → INCONCLUSIVO`.
- A PET-05 do Design B permanece `INCONCLUSIVO`.
- Comparador rejeita arquivo de dados de entrada como se fosse relatório; recusa relatórios incompletos, IDs duplicados e selecionados idênticos.
- Dados técnicos novos não são automaticamente `CONFIRMADO`.
- Projeto atual só é substituído após confirmação explícita em Projetos.
- Mudanças invalidam o resultado ativo antes de nova avaliação.
- Snapshots preservam projetos e resultados sem sobrescrever registros anteriores.

## Teste manual antes do merge

1. Abrir app no Windows com Streamlit instalado, em janela de 1440 px e 390 px. Verificar rolagem, quebra de colunas e texto legível.
2. Criar projeto e selecionar componentes presentes/ausentes. Confirmar que omissões continuam `DESCONHECIDA`.
3. Enviar PDF sintético, aceitar apenas um dos dados e verificar que os demais não entram como `CONFIRMADO`.
4. Registrar manualmente sem confirmação, confirmar depois com revisor e verificar estado.
5. Executar avaliação, alterar dado e confirmar que resultado anterior é invalidado.
6. Importar JSON A/B com tela de prévia; cancelar importação e verificar que o projeto não muda.
7. Usar comparador demonstrativo, depois dois relatórios exportados; validar transições e exportação.
8. Salvar e reabrir um snapshot, comparar dois snapshots salvos, confirmar ausência de autosave.
9. Testar somente teclado, zoom 200%, leitor de tela e contraste em navegador. Corrigir eventuais limitações de componentes Streamlit.
10. Fazer rodada exploratória com 3–5 pessoas sem roteiro externo; registrar pontos de hesitação, erros e interpretações de `INCONCLUSIVO`.

**Limites conhecidos:** nenhuma conta multiusuário ou sincronização; uploads originais não persistidos; sem OCR; sem classificação global; UI em Streamlit precisa de teste visual real; não há comprovação de conformidade WCAG 2.2 AA nem validação estatística de usabilidade.
