# PET Circular — Interface Streamlit v0.1

Primeira interface funcional do protótipo PET Circular, desenvolvida em Python + Streamlit e **conectada ao motor demonstrativo de 15 regras** da matriz científica v0.3.3. Inclui o exemplo documental Patrico e os catálogos técnico-científicos utilizados no motor v0.1.

**Não é ferramenta de certificação RecyClass.** O resultado permanece individual por critério; a classe global de reciclabilidade é sempre **NÃO EMITIDA**. A IA e a leitura automática de documentos ainda não foram integradas.

## Como executar no Windows

1. Instale Python 3.11 ou superior a partir de https://www.python.org/downloads/ e certifique-se de que Python funciona no terminal.
2. Extraia este ZIP em uma pasta (por exemplo, `Documentos/PET_Circular_App`).
3. Abra o **PowerShell** dentro da pasta extraída, no diretório que contém `app.py`.
4. Execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Caso a política do PowerShell bloqueie `Activate.ps1`, execute sem ativar:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O aplicativo abrirá no navegador, geralmente em `http://localhost:8501`.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Para interromper, volte ao terminal e pressione `Ctrl+C`.

## Fluxo de utilização

- **Visão geral:** status da embalagem e descrição do processo.
- **Produto:** cadastro de ID, nome, versão de design, fase e contexto.
- **Componentes:** informar se corpo, tampa, rótulo, sleeve, adesivo, tinta, barreira, liner, válvula, lacre e outros estão presentes, ausentes ou desconhecidos.
- **Dados técnicos:** formulário rápido de material/cor/capacidade, além dos campos detalhados da matriz. Valores com status *DECLARADO* ou *PROPOSTO* não geram conclusão técnica definitiva. No formulário rápido, a confirmação exige manifestação explícita de revisão e documento vinculado ou revisor identificado. No formulário detalhado, a seleção explícita de CONFIRMADO exige documento ou revisor.
- **Evidências:** cadastro de fontes, URL, versão, páginas e PDFs. O PDF não é analisado por IA nem armazenado pelo programa; apenas o SHA-256 e os metadados são registrados. Guarde o arquivo original.
- **Avaliação:** executar as 15 regras, consultar cada justificativa, ver documentos e campos faltantes, baixar JSON e CSV.

A barra lateral tem botões para carregar o **piloto Patrico**, criar um produto vazio, importar um JSON existente, exportar o envelope e salvar/recuperar snapshots.

### Persistência e segurança

Os envelopes e relatórios são gravados em `data/local.sqlite3`, **na máquina onde o Streamlit está rodando**. Cada salvamento gera um snapshot histórico. Se rodar em um serviço remoto, os dados estarão no servidor remoto. Não há autenticação ou isolamento multiusuário: use a interface apenas localmente, sem publicação pública e sem dados confidenciais de terceiros. O SQLite e o upload não oferecem, por si só, tratamento seguro de dados industriais sensíveis.

O código não faz chamadas para APIs de IA, não envia dados para a RecyClass nem recupera fontes online. As referências disponíveis são os links e registros preservados da matriz; verifique a atualidade de uma versão antes de tomar decisões técnicas.

### Testes

```bash
python -m unittest discover -s tests -v
python -m pet_circular examples/patrico_input.json -o examples/patrico_result.json
```

O motor de regras foi incorporado **sem alterar seus critérios científicos**. O conjunto de testes cobre as regras originais, a adaptação UI→JSON, importação/exportação, evidências, confirmação humana e snapshots SQLite. A validação visual com Streamlit deve ser realizada em um ambiente que tenha essa biblioteca instalada.

### Estrutura

```text
PET_Circular_App_Streamlit_v01/
  app.py                       Interface principal
  ui_helpers.py                Validação e transformação de dados da UI
  storage.py                   Histórico SQLite local
  requirements.txt             Dependências
  .streamlit/config.toml       Tema
  pet_circular/                Motor v0.1 e catálogos da matriz v0.3.3
  examples/                    Piloto documental Patrico
  tests/                       Testes originais e de integração
  data/                        Banco local criado na primeira execução
```

## Limites ainda pendentes

- PET-04: percentual de cobertura com método geométrico ainda não homologado.
- PET-16: determinação dimensional compactada ainda sem procedimento operacional aprovado.
- Balanço gravimétrico completo e acessórios: ainda sem implementação integral no motor Python.
- A presença/ausência declarada de componentes não tem vínculo documental obrigatório no motor atual: o inventário exige revisão humana independente.
- Não realiza extração PDF com IA; usuário registra fatos/evidências manualmente.
- **Não emite classificação global ou certificação oficial**, mesmo para uma entrada aparentemente completa.

Próximo passo de desenvolvimento: testes visuais de fluxo no Streamlit, tratamento seguro de documentos, validação humana estruturada para dados extraídos, integração opcional de um adaptador de IA e ampliação da cobertura do motor após revisão científica.

### Atalho no Windows

Também é possível dar um duplo clique em `iniciar_windows.bat` após extrair a pasta. O script cria o ambiente virtual local, instala as bibliotecas necessárias se ausentes (precisa de conexão à internet na primeira vez) e abre o Streamlit. O Python precisa estar previamente instalado.
