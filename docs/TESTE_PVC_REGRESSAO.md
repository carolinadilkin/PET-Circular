# Teste de regressão — rótulo PVC (MVP v0.3.1)

**Casos sintéticos, sem certificação e sem evidência laboratorial real.**

## Evidência observada em 29/10/2026

- **Teste A (PDF):** escopo `DENTRO`, PET-01 `COMPATIVEL`, PET-05 `NAO_COMPATIVEL`; identificou PVC confirmado, mas ficaram pendentes `densidade_rotulo`, `fixacao_rotulo` e `desprendimento`.
- **Teste B (JSON exportado após a tentativa):** identificador `novo-produto`, escopo `INDETERMINADO`, todas as regras inconclusivas, sem evidências. O arquivo esperado possui ID `SYN-PET-PVC-LABEL-001`, seis fatos técnicos e 11 componentes. Portanto, a avaliação B refletiu um cadastro vazio. O JSON exportado não permite determinar *por que* a importação não persistiu.
- Importação programática com `import_case` do JSON de cenário: válida e PET-05 `NAO_COMPATIVEL`. Logo, não há evidência de erro de classificação do motor.

## Reproduzir o Teste B na interface

1. Abra o Streamlit desta versão.
2. Na barra lateral, expanda **Importar envelope JSON**, sem necessidade de clicar em **Criar produto novo**.
3. Selecione `examples/teste_rotulo_pvc_input.json` — **não** selecione um arquivo com nome `resultado`.
4. Clique em **Importar** e confira a mensagem **Importação confirmada**.
5. Confira antes de avaliar: **ID ativo `SYN-PET-PVC-LABEL-001`**, **6 fatos** e **11 componentes**. Se aparecer `novo-produto` ou `0 fatos`, a importação não aconteceu: volte ao passo 2.
6. Abra **Avaliação** e execute as 15 regras. Esperado: **PET-01 compatível**, **PET-05 não compatível**, escopo `DENTRO` e classe global não emitida. A densidade está no JSON; faltam fixação e desprendimento.
7. Abra **Assistente de ecodesign** e pergunte: "Por que a PET-05 está não compatível e quais alternativas de ecodesign a matriz recomenda?"
8. No modo local, confira a orientação da matriz sobre **PE/PP/OPP flutuantes** e as ressalvas sobre densidade final, desprendimento, tintas e cobertura/NIR.

**Atenção:** importar ou selecionar um JSON não é suficiente: é obrigatório clicar em **Importar**, observar a confirmação e manter o mesmo caso ativo. Nunca clique em **Criar produto novo** depois da importação se a intenção é avaliar o caso importado.
