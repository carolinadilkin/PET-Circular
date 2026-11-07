# PET Circular v0.11 — resumo técnico (07/11/2026)

**Status:** aplicativo v0.11 implementado e validado em testes automatizados; aceitação Windows e API Gemini real ainda pendentes. Esta branch contém DOCUMENTAÇÃO. A versão integral do código v0.11 está no pacote ZIP e no bundle Git de entrega, não nesta branch.

## Evolução funcional
- Nova jornada: origem PDF/JSON/manual → conhecer embalagem → catálogo técnico → validação final única → resultados → redesign A/B.
- Catálogo de 84 atributos com alternativas selecionáveis, estados Desconhecido/Ausente e seleção múltipla para polímeros secundários.
- Dados `DECLARADO` são utilizados para **pré-avaliação** por 15 regras do motor v0.1.2, matriz v0.3.3; registro de proveniência declaratória. Não são convertidos silenciosamente em `CONFIRMADO`.
- Ausência de sleeve informada resulta em PET-19 não aplicável; PP/PEAD de tampa informado é reconhecido em PET-07, mas densidade/vedação/separabilidade podem continuar pendentes.
- Índice IPR-PET/1.0.0 permanece experimental, com intervalos de incerteza e sem equivalência a classe oficial ou taxa efetiva de reciclagem.
- Gemini por `google-genai` permanece opcional, com `GEMINI_API_KEY` apenas no servidor e consentimento por tarefa.

## Evidência de software
`python -m unittest discover -s tests -q` na distribuição v0.11: 169 testes, 167 aprovados, 2 ignorados, 0 falhas. O teste remoto real da API Gemini, o aceite no Windows do usuário e a validação científica independente NÃO constam como concluídos.

## Documentos vigentes do pacote
- README.md
- docs/PROPOSTA_CIENTIFICA_TECNOLOGICA_V011.md
- docs/PET_Circular_Proposta_Cientifica_Tecnologica_V011.docx e .pdf
- docs/IMPLEMENTACAO_V011_ARQUITETURA_E_UX.md
- docs/RELATORIO_VALIDACAO_V011.md
- docs/IPR_PET_METODOLOGIA_V07.md (com nota operacional v0.11)
- docs/INTEGRACAO_GEMINI_V10.md (integração ainda vigente)

**Importante:** não considerar o código v0.4 existente no GitHub como implementação da v0.11 apenas porque esta documentação foi publicada. O código completo exige commit/push separado.