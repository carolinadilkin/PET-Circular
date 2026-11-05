# Implementação da interface Web v0.4

**Base visual:** `pet_circular_v04_ux/PROTOTIPO_NAVEGAVEL_v04.html` aprovado no projeto. A folha de estilo de `web/styles.css` parte da CSS desse arquivo; o layout do início foi preservado, enquanto as telas de Avaliação, Comparação e Projetos foram conectadas à API.

## Arquitetura

- Frontend HTML/CSS/JavaScript próprio em `web/`, sem bibliotecas externas ou rede de conteúdo.
- `server.py`: FastAPI local, com host `127.0.0.1`, token de sessão em cabeçalho e proteção de origem.
- `pet_circular/engine.py`: motor determinístico inalterado com 15 regras.
- `document_ai.py`: extração PDF local e API opcional com consentimento, candidatos rastreáveis.
- `ecodesign_assistant.py`: respostas locais e IA opcional; nenhuma muda as classificações.
- `comparison_v04.py`: comparação de relatórios, não classifica embalagem integral.
- `storage.py`: snapshots imutáveis em SQLite local.

## Fluxos disponíveis

1. Nova embalagem, inventário explícito de componentes e preenchimento de escopo sem confirmação presumida.
2. Upload de PDF com extração local por padrão; proposta em tabela com trecho, página, revisor e confirmação por campo. PDF original não é salvo.
3. Registro manual como declarado, ou confirmado mediante conferência explícita, responsável e registro de origem quando houver.
4. Avaliação por critério com destaque dos problemas, pendências e recomendações; assistente dentro da página de resultados.
5. Comparação de dois relatórios dos exemplos A/B, arquivos JSON de relatório ou versões salvas, sem declarar `NAO_COMPATIVEL → INCONCLUSIVO` como aprovação.
6. Histórico local e importação de projeto com prévia/confirmar; aviso de alterações não salvas.

## Limitações

- Não é um sistema multiusuário. Não disponibilizar o servidor na rede pública.
- Não existe OCR de PDFs digitalizados, nem preservação do PDF original no banco.
- Não existe nota global, certificação ou ensaio físico.
- Somente relatório de 15 regras e matriz 0.3.3; versões incompatíveis geram aviso.
- Avaliação heurística de UX e testes de execução não substituem teste de usabilidade com usuários nem auditoria WCAG completa.
- A comunicação com serviços de IA exige escolha e consentimento, chave própria, autorização de envio de dados; não há validação de respostas reais da API neste desenvolvimento.

## Testes

- Suíte original e v0.4: 127 testes reportados após a atualização PET-16; executar novamente para conferir o total atual (`python -m unittest discover -s tests -v`).
- Navegador headless Chromium com HTML/CSS/JS reais e endpoints Python executados por ponte local em memória: jornada de criação, avaliação, comparação A/B, importação JSON e salvamento de snapshot; nenhuma exceção JS observada, sem rolagem horizontal de página a 390 px.
- Acesso HTTP via FastAPI TestClient e servidor local verificado. Não foi possível executar browser direto para `localhost` no ambiente de teste devido a uma restrição de rede do executor, portanto é necessária verificação final da abertura no Windows.

## Uso correto na fase de design

A comparação A/B da PoC representa uma análise preventiva: A é referência comercial observada; B é proposta ainda não fabricada. Campos de B não devem ser artificialmente marcados `CONFIRMADO` sem evidência. Uma regra que requer confirmação continua inconclusiva nesse estágio. A IA pode sugerir extrações, mas exige revisão humana antes de alimentar o motor. Ver `ALINHAMENTO_DESAFIO2_CASO_REAL.md`.
