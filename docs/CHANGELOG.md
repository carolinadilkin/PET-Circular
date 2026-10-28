## v0.3 — 28/10/2026
- Assistente de ecodesign em página Streamlit, vinculado ao produto e ao resultado das 15 regras.
- Modo local determinístico e modo OpenAI API opcional mediante consentimento.
- Fontes rastreadas pela matriz, status e campos faltantes exibidos; sem classe global nem edição do motor.
- Dez testes de assistente adicionados; 70 testes offline aprovados.
- A interface real e a chamada remota ainda precisam ser testadas no ambiente de usuário.

# Registro de versões

## MVP v0.2 — documentos e revisão humana
- Adiciona leitura de PDFs textuais e candidatos de dados com evidência por página.
- Inclui extração local sem chave de API e adaptador opcional para OpenAI.
- Protege dados confirmados: exigência de revisão humana antes de aplicar regras.
- Corrige separação entre ensaios formalmente exigidos e medições pendentes.
- Inclui documento sintético de teste e testes de extração / proveniência.

## MVP v0.1 — interface e motor técnico
- Motor demonstrativo de 15 regras individuais da matriz PET Circular v0.3.3.
- Aplicativo Streamlit com cadastro, componentes, evidências, avaliação e exportações.
- Histórico local SQLite e testes automatizados.
- Limitação: não emite classe global ou certificação.
