# PET Circular — App com extração documental e revisão humana (MVP v0.2)

**Objetivo:** avaliar aspectos de design de garrafas PET transparentes incolores ou azul-claras com base nas **15 regras individuais da matriz v0.3.3**, usando o motor determinístico v0.1. Esta versão acrescenta a leitura de PDFs, a extração de candidatos de dados técnicos, a proveniência por página e a confirmação humana antes de usar qualquer valor extraído na avaliação.

> **Não emite classe global nem certificação RecyClass.** Fichas técnicas do corpo da garrafa não comprovam as propriedades da embalagem final. Os limites das PET-04 e PET-16 e a integração da composição gravimétrica permanecem pendentes de metodologia ou implementação. A cobertura científica do motor não foi ampliada nesta versão.

## Execução no Windows

1. Instale Python 3.11+ pelo site https://www.python.org/downloads/ (caso ainda não tenha).
2. Extraia o ZIP **inteiro** para uma pasta nova, sem misturar com o aplicativo anterior.
3. Abra a pasta `PET_Circular_App_IA_v02` e dê duplo clique em **`iniciar_windows.bat`**. O arquivo instala as dependências necessárias na primeira execução, com internet.
4. Acesse `http://localhost:8501` no navegador se não abrir automaticamente.

Outra forma, pelo PowerShell dentro da pasta do aplicativo:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Feche o aplicativo com `Ctrl+C` no terminal. Se uma instalação anterior for usada, confirme que o `iniciar_windows.bat` está dentro da **nova** pasta, pois as dependências `pypdf` e `openai` são novas.

## Teste orientado (sem chave nem custos de API)

1. Clique em **Criar produto novo**; não utilize dados fictícios como evidência do piloto Patrico.
2. Acesse **IA · Documentos** e carregue `examples/ficha_sintetica_teste.pdf` (esse arquivo é **sintético**, elaborado exclusivamente para teste de software, não uma especificação comercial).
3. Selecione **Local — padrões explícitos**; clique em **Ler PDF e propor dados**.
4. Confira o documento registrado e os **seis candidatos** apresentados com transcrição literal e número de página.
5. Selecione os candidatos que deseja confirmar, digite a identificação do revisor, marque a confirmação explícita e clique em **Confirmar selecionados e atualizar o produto**.
6. Em **Dados técnicos**, confira que os campos aceitos estão `CONFIRMADO` e estão associados ao ID do PDF, com trecho e página registrados em `observation`.
7. Em **Componentes**, confirme separadamente a presença/ausência de acessórios; a inferência de presença a partir de material NÃO é automática.
8. Em **Avaliação**, execute novamente as 15 regras e exporte o JSON. O sistema manterá **classe global: NÃO EMITIDA**.

Opcionalmente, carregue o piloto Patrico para comparar a avaliação documental existente. **Não utilize** a ficha sintética como evidência da Patrico.

## Extração usando IA OpenAI (opcional)

Para experimentar o modo por modelo de linguagem:

1. Tenha uma chave válida de **API OpenAI** com faturamento/habilitação apropriados. Uma assinatura do ChatGPT não substitui credenciais de API.
2. Abra **IA · Documentos** → **IA — OpenAI API**.
3. Cole a chave no campo protegido da sessão ou defina `OPENAI_API_KEY` como variável de ambiente antes de executar o aplicativo.
4. Escolha o modelo disponível em sua conta (valor inicial `gpt-4.1-mini`). Marque o consentimento **somente se tiver autorização** para enviar texto do documento ao provedor externo.
5. Clique em **Ler PDF e propor dados**, depois revise individualmente as citações antes de aceitar.

A integração usa o endpoint **Responses API** com Structured Outputs e `store=False`. Somente texto extraído do PDF é enviado; não é feito upload do arquivo bruto nem envio de dados ao serviço sem o consentimento explícito. **A disponibilidade do modelo, custo e comportamento remoto não puderam ser verificados neste ambiente**. O modo local funciona sem essa integração. Evite testar com documentos sigilosos ou de terceiros sem autorização.

## Segurança, limites e proveniência

- O PDF precisa conter texto pesquisável. PDFs escaneados exigem OCR, que **não faz parte deste incremento**. Limites: 12 MB, 35 páginas e até 48 mil caracteres enviados à extração.
- O parser local é deliberadamente conservador e reconhece apenas algumas propriedades com rótulos explícitos. A IA tenta até 13 campos canônicos permitidos, mas **não pode inventar campos nem classificações**.
- Propostas da IA são recusadas se apresentarem página inválida, citação não encontrada no texto extraído ou valor sem suporte textual detectável. Isso **não garante** que toda interpretação semântica da IA esteja correta; é necessária revisão humana.
- Nenhum dado é importado como `CONFIRMADO` por simples upload. É necessário aceitar cada proposta e informar o revisor, que pode corrigir o valor se ele for sustentado pelo trecho citado.
- Substituir um valor já confirmado exige autorização explícita por campo. A presença de tampa, rótulo, sleeve e outros componentes é tratada separadamente.
- O PDF original e a chave API **não são gravados no SQLite**. Só são salvos metadados, hash, fatos confirmados, trechos citados e identificador do revisor; o usuário deve arquivar o PDF original.
- O banco local `data/local.sqlite3` contém informações potencialmente confidenciais da embalagem após confirmação. Não publique o app na internet sem autenticação, isolamento de usuários e controles de segurança. Na execução remota o armazenamento fica no servidor.
- Nenhuma resposta do modelo decide reciclabilidade diretamente: o motor Python, inalterado, avalia as regras individualmente.
- O cartão **Ensaios requeridos** foi separado de **Medições pendentes**, eliminando a leitura equivocada do zero ensaio no piloto com a PET-16 inconclusiva.

## Testes automatizados

```bash
python -m unittest discover -s tests -v
python -m pet_circular examples/patrico_input.json -o examples/patrico_result.json
```

Foram executados testes unitários offline de extração de PDF, verificação literal de citações, rejeição de campos inventados, proteção contra substituição de valor confirmado, revisão humana e motor de regras. A chamada à API foi testada com uma implementação simulada (*mock*), **não com credenciais reais**. O Streamlit não estava instalado no ambiente de desenvolvimento, então a interface visual precisa ser verificada no Windows.

## Estrutura

```text
PET_Circular_App_IA_v02/
  app.py                         Interface, navegador de regras e nova página IA · Documentos
  ui_document_ai.py              Upload, propostas, revisão humana e consentimento
  document_ai.py                 PDF, parser local, Responses API, validação de citações
  ui_helpers.py                  Fatos, evidências e transformação para o motor
  storage.py                     Snapshots locais SQLite
  pet_circular/                 Motor v0.1 e regras da matriz científica v0.3.3
  examples/
    patrico_input.json           Piloto documental real (dados previamente registrados)
    ficha_sintetica_teste.pdf     Arquivo FICTÍCIO exclusivamente para teste de extração
  tests/                         Testes do motor, interface e integração de PDFs
  iniciar_windows.bat            Inicialização no Windows
  requirements.txt               Dependências
```

## Assistente de ecodesign — MVP v0.3 (prova de conceito)

Na barra lateral, abra **Assistente de ecodesign**. O modo **Local — rastreável, sem API** responde com status do motor, campos faltantes, recomendações da matriz e links das referências das regras relacionadas. O modo **IA — OpenAI API** redige a explicação em linguagem natural, mediante chave e consentimento explícito; sua chamada envia somente a pergunta, os resultados relevantes e os trechos das regras (não os PDFs originais). A API não decide compatibilidade e sua resposta exige revisão.

**Limitações:** identificação de regras por palavras-chave/IDs; a interpretação é limitada às 15 regras e ao estado corrente. O modo local não é IA generativa. A chamada externa foi verificada com mock, não com chave real. Dúvidas normativas exigem consulta humana à diretriz, e classe global não é emitida. Histórico da conversa é mantido somente na sessão Streamlit. Com os dados atuais do produto alterados, o diálogo é reiniciado.

**Testes:** `python -m unittest discover -s tests -v` (70 testes offline).

**Próximas entregas:** teste visual de extração e revisão no Windows, validação com documento real completo e autorizado, OCR opcional, avaliação de precisão da IA e melhorias de usabilidade. O agente conversacional e a plataforma multiempresa permanecem fora deste MVP.
