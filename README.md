# PET Circular — Guided Ecodesign Studio v0.4 (prévia funcional)

Aplicativo Streamlit orientado a tarefas para apoiar avaliações de **design de garrafas PET transparentes incolores ou azul-claras**, com 15 regras individuais da **matriz técnica v0.3.3** e motor determinístico **v0.1.0**.

> **Não emite classe global, laudo ou certificação de reciclabilidade.** Nenhuma recomendação de IA substitui documentação técnica, revisão humana ou ensaio necessário. Casos demonstrativos não representam evidência de produtos reais.

## Executar no Windows

1. Instale [Python 3.11+](https://www.python.org/downloads/) com o Python Launcher (`py`).
2. Extraia o **ZIP inteiro** em uma pasta nova, sem misturá-lo com a v0.3.1.
3. Entre na pasta `PET_Circular_App_v04` e execute **`iniciar_windows.bat`**.
4. Na primeira execução, com internet, as dependências Python serão instaladas. O aplicativo abrirá em `http://127.0.0.1:8501`.
5. Para interromper, feche o terminal ou pressione `Ctrl+C`.

Alternativa no terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Navegação principal

- **Início:** escolha entre avaliar, comparar ou continuar um projeto.
- **Avaliação:** etapas flexíveis `Embalagem → Informações → Revisar → Resultados`.
  - Na etapa **Embalagem**, identifique produto/versão, material do corpo e presença de componentes. `Ainda não sei` não equivale a `Ausente`.
  - Na etapa **Informações**, carregue uma ficha PDF (extração local padrão; API OpenAI opcional com chave e consentimento) ou preencha manualmente.
  - Na etapa **Revisar**, confira os estados `DECLARADO`/`CONFIRMADO`, evidência e revisor. A confirmação exige ação e identificação humana; upload não confirma.
  - Na etapa **Resultados**, clique em **Avaliar com os dados disponíveis**, examine incompatibilidades e pendências, abra fontes, exporte o resultado e pergunte ao assistente local.
- **Comparação:** selecione dois relatórios de avaliação JSON já gerados, duas avaliações salvas ou uma demonstração A/B sintética. Quando os IDs diferirem, confirme a relação entre os designs. A comparação bloqueia versões diferentes da matriz/motor e não calcula classe global.
- **Projetos:** salve snapshots em SQLite local, exporte JSON de entrada, importe novo projeto com prévia/consentimento ou abra versões salvas. **Não há salvamento automático.**
- **Avançado:** conserva as telas técnicas anteriores para auditoria e edição detalhada, sem atalhos de substituição do projeto.

## Teste rápido recomendado

### Percurso 1 — comparação A/B

1. Acesse **Comparação**.
2. Em *Como deseja selecionar*, escolha **Experimentar dados demonstrativos**. Confirme a relação entre os relatórios A/B.
3. Compare as transições de **PET-09** e **PET-18** (`NAO_COMPATIVEL → COMPATIVEL`), **PET-05** (`NAO_COMPATIVEL → INCONCLUSIVO`) e pendências **PET-04**, **PET-16**, **PET-17**.
4. Exporte o resultado da comparação. Nenhuma embalagem recebe aprovação global.

### Percurso 2 — importação e avaliação

1. Vá a **Projetos → Importar um projeto existente**.
2. Selecione `examples/integrated/Design_A_Entrada.json`.
3. Confira a prévia do produto atual e o produto que será importado. Marque a confirmação e clique em **Substituir produto ativo**.
4. Em **Avaliação → 4. Resultados**, clique em **Avaliar com os dados disponíveis**.
5. Devem aparecer **3 incompatibilidades confirmadas** (PET-05, PET-09, PET-18). Exporte o relatório JSON.
6. Em **Projetos**, salve o snapshot para retomar/comparar no futuro.
7. Repita com `Design_B_Entrada.json`: **0 incompatibilidades identificadas**, mas **PET-05 inconclusivo**. Salve e compare.

### Percurso 3 — PDF com revisão humana

1. Crie um novo projeto em **Projetos**, confirme a substituição.
2. Em **Avaliação → 1. Embalagem**, salve o cadastro e indique os componentes cuja presença conhece.
3. Em **2. Informações → Enviar ficha técnica PDF**, carregue `examples/ficha_sintetica_teste.pdf` e use modo **Local**.
4. Revise os trechos literais por página; marque cada valor correto, informe o revisor e confirme explicitamente.
5. Na etapa **3. Revisar**, confira a proveniência e, então, execute a avaliação na etapa **4. Resultados**.

O extrator local é conservador: ele **não** reconhece todos os campos da matriz. PDF digitalizado sem texto pesquisável requer OCR, ainda não implementado. A presença dos componentes não é inferida automaticamente do documento.

## Versões, armazenamento e privacidade

- Motor `0.1.0`, matriz `0.3.3`, interface `0.4` (prévia funcional).
- SQLite fica no computador/servidor que executa o Streamlit; **não é uma conta multiusuário**.
- PDF original e credencial de API não são guardados no banco; mantenha o arquivo original.
- A API externa é opcional, com consentimento e chave própria. O modo local não necessita API.
- Salvamento é explícito; exporte também o JSON de entrada. Abrir outro projeto substitui o estado na sessão somente após confirmação.
- Alterar qualquer dado invalida o resultado ativo; é necessário reavaliar.
- Nunca use dados sintéticos como evidências laboratoriais ou de fornecedor.

## Testes e limites da implementação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Foram executados **93 testes offline** neste incremento, incluindo regressões do motor, parser documental, assistente, comparação A/B, histórico SQLite e testes estruturais de navegação com *stub*. Não foi executado um teste visual do **Streamlit real** neste ambiente. A validação de acessibilidade WCAG, navegação por teclado e teste independente de usabilidade precisam ser realizados em navegador no Windows.

## Estrutura principal

```text
PET_Circular_App_v04/
  app.py                    Ponto de entrada: nova navegação + telas avançadas
  ui_v04.py                 Fluxo guiado, resultados, projetos e comparação
  comparison_v04.py         Algoritmo determinístico de transições A/B
  ui_document_ai.py         Extração documental e revisão humana
  ui_assistant.py           Assistente por regra e evidência
  ecodesign_assistant.py    Respostas locais / adaptador API opcional
  pet_circular/engine.py    Motor técnico original, sem alteração nas 15 regras
  storage.py                Snapshots históricos SQLite
  examples/integrated/      Cenários A/B inteiramente sintéticos
  tests/                    Testes automatizados
  docs/UX_V04_IMPLEMENTACAO.md
  iniciar_windows.bat
```

A especificação de UX aprovada está registrada em `docs/UX_V04_ESPECIFICACAO_APROVADA.md`. O protótipo HTML inicial é apenas uma referência visual; o aplicativo que executa avaliações reais é **`app.py`**.
