# PET Circular v0.4 Web — Guided Ecodesign Studio

Nova interface web baseada **diretamente no protótipo HTML aprovado**, preservando os elementos visuais de navegação, cores, tipografia e cartões. O motor científico Python, a matriz 0.3.3, a revisão humana, as regras e a comparação determinística não foram alterados.

## Executar no Windows

1. Extraia o ZIP integralmente em uma pasta nova, **sem misturar com a versão Streamlit**.
2. Dentro de `PET_Circular_App_Web_v04`, execute `iniciar_windows.bat`.
3. Na primeira execução, o script cria `.venv` e instala as dependências (internet necessária).
4. O navegador abrirá automaticamente `http://127.0.0.1:8501` (ou abra o endereço manualmente).
5. Para encerrar, feche a janela do terminal ou pressione `Ctrl+C`.

Alternativa PowerShell (Python 3.11+):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
.\.venv\Scripts\python.exe server.py
```

## Começar e testar

- **Início:** selecionar Avaliar embalagem, Comparar designs ou Projetos.
- **Avaliação:** preencher dados básicos e componentes; enviar PDF ou registrar dados manualmente; revisar trechos e valores; avaliar com os dados disponíveis; consultar recomendações ou assistente.
- **Comparação:** clicar em **Usar demonstração A/B** para comparar relatórios sintéticos previamente verificados pelo motor; também é possível comparar dois relatórios exportados ou snapshots.
- **Projetos:** salvar explicitamente uma versão no SQLite local, abrir outra versão, importar projeto JSON com prévia/confirmar ou exportar entrada/resultado.

**Importante:** trocar projetos com alterações não salvas exige confirmação. Ao recarregar o navegador sem salvar, o trabalho em curso pode ser perdido, portanto use **Projetos → Salvar versão atual**. O histórico SQLite é local ao servidor. Os PDFs originais não são armazenados.

## Segurança e limites

- É um protótipo **local de um único usuário**, iniciado em `127.0.0.1`. Não implante na internet sem login, gerenciamento de sessões, proteção de dados e controles de segurança adequados.
- O modo padrão de extração é **local**, sem envio a serviços externos. PDF pesquisável, até 12 MB e 35 páginas; PDF digitalizado requer OCR, ainda não implementado.
- O modo API é opcional e requer chave e consentimento específico. As chaves e PDFs não são guardados no SQLite. A chave segue ao servidor local para a chamada remota, se explicitamente ativada.
- Não há classes globais de reciclabilidade, laudos, certificação RecyClass nem ensaios reais executados pelo app.
- A interface usa CSS, HTML e JavaScript próprios, sem CDN, e API FastAPI com motor Python determinístico.
- A interface Web é independente da versão Streamlit mantida no repositório somente por rastreabilidade; o arquivo a executar é **server.py**, não `app.py`.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes de API ficam em `tests/test_web_v04.py`. O fluxo de navegador foi executado por ponte em memória com o FastAPI local; o ambiente bloqueia acesso direto do navegador à porta localhost. É necessária verificação final de uso real no Windows.

Para a suíte completa (incluindo testes legados de Streamlit) no repositório, instale também as dependências de `requirements.txt` e `httpx` conforme o workflow GitHub Actions.

## Atualização PET-04 (motor v0.1.1)

O procedimento interno [PTI-PET04-001](docs/PTI-PET04-001.md) permite registrar M1 (áreas de frente/verso; prevalece maior proporção) ou M2 (área lateral), além do percentual legado. Gatilhos SEP-01 independentes (rótulo de outro polímero >50%, sleeve integral, metalização) são apontados quando identificados. A geometria **não** comprova o desempenho NIR, por isso a PET-04 permanece inconclusiva sem validação específica. A PET-16 também foi implementada; consulte a seção abaixo e [PTI-PET16-001](docs/PTI-PET16-001.md).

## PET-16 — dimensões após compactação (motor 0.1.2)

A PET-16 distingue `>5 L` de dimensão compactada `≤4 cm`, com fonte, protocolo e confirmação operacional explícitos. Sem medição adequada, o critério permanece inconclusivo. `NAO_ACIONADA` não é certificação. Detalhes em `docs/PTI-PET16-001.md`.

## Alinhamento científico e caso de validação

O **Desafio 2 — Soluções para Avaliar e Melhorar a Reciclabilidade de Embalagens Plásticas Utilizando Dados e Inteligência Artificial** admite expressamente análises desde a **concepção e o design**. A persona principal desta PoC é a pessoa de engenharia/desenvolvimento de embalagens; sustentabilidade, qualidade e materiais são personas de apoio. O PET Circular apoia decisões preventivas de *Design for Recycling* em garrafas PET transparentes, sem certificar a reciclabilidade final.

O estudo de caso deve comparar **Design A** (embalagem comercial existente como referência técnica observada) com **Design B** (redesenho hipotético proposto antes da fabricação). O B não deve ser relatado como produto real ou ensaiado. Resultados devem ser comparativos, por exemplo contagem de critérios incompatíveis, inconclusivos e pendentes e transições por regra, sem converter tais contagens em um índice global sem validação. A IA ajuda a extrair dados de especificações/documentos, com conferência humana; o motor de regras continua determinístico. Os estados de maturidade *ideação, desenvolvimento e validação* são uma **interpretação metodológica**, não três modos de software já implementados.

Ver protocolo em [Alinhamento ao Desafio 2 e estudo de caso A/B](docs/ALINHAMENTO_DESAFIO2_CASO_REAL.md).
