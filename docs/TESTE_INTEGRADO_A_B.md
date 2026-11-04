# PET Circular | Teste integrado - Design A vs Design B

**CENÁRIOS INTEIRAMENTE SINTÉTICOS.** Nenhum documento é real. Os campos `CONFIRMADO` no JSON representam premissas do teste e não resultados laboratoriais. Matriz 0.3.3; motor 0.1.0; aplicativo v0.3.1. A ferramenta não emite classificação global nem certificação RecyClass.

## Objetivo

Avaliar integração de cinco componentes declarados presentes: corpo PET, tampa PP, rótulo, adesivo e tinta. O Design A foi construído com três incompatibilidades explícitas. O Design B simula modificações de ecodesign, mas **não deve ser classificado globalmente como reciclável** porque persistem critérios pendentes.

### Design A - base com incompatibilidades

- Corpo PET transparente incolor, 500 mL.
- Tampa PP de densidade sintética 0,92 g/cm³, desprendível; liner e válvula ausentes.
- Rótulo PVC de densidade sintética 1,38 g/cm³, não desprendível.
- Adesivo não liberável; tinta com ligante clorado, com declaração EuPIA simulada como negativa.
- Cobertura não PET informada como estimativa de 30%, **sem método homologado**.

**Resultado esperado:** PET-01 compatível; PET-07 compatível; PET-05, PET-09 e PET-18 não compatíveis; PET-04 inconclusivo; PET-17 com avaliação/ensaio pendente; classe global não emitida.

### Design B - proposta de redesenho

- Mantém corpo PET e tampa PP.
- Troca o rótulo PVC por PP de densidade sintética 0,91 g/cm³, com desprendimento afirmado no cenário.
- Adesivo liberável na faixa 70–90 °C e tinta não clorada, com condições e evidências **inteiramente simuladas**, sem ensaio real.
- Cobertura ainda é apenas estimativa geométrica (30%) e não é homologada para validação automática.

**Resultado esperado:** PET-01, PET-07, PET-09 e PET-18 compatíveis no cenário sintético. PET-05 permanece **inconclusivo** por integração com PET-04, que ainda não foi homologada. A classe global não deve ser emitida.

## Roteiro 1 - Testar os dados completos do motor e do assistente (RECOMENDADO)

1. Abra o aplicativo PET Circular v0.3.1 (`iniciar_windows.bat`).
2. Na barra lateral, use **Importar envelope JSON** e selecione `Design_A_Entrada.json`.
3. **Clique efetivamente em Importar** e confira o aviso de importação bem-sucedida. É normal que o Streamlit atualize a página.
4. Verifique o ID **SYN-PET-INTEGRADO-A-001**, a contagem de **27 fatos técnicos** e **11 componentes conhecidos** (5 presentes, 6 ausentes). Se o ID continuar `novo-produto`, o arquivo não foi aplicado: não prossiga.
5. Na aba **Avaliação**, clique em **Executar avaliação das 15 regras**. Confira 3 incompatibilidades: PET-05, PET-09, PET-18. A PET-07 deve ser compatível.
6. Na aba **Assistente de ecodesign**, no modo **Local**, pergunte:
   `Quais incompatibilidades foram identificadas para a embalagem e o que deve mudar?`
   **Nota:** o modo local atual seleciona no máximo três regras por resposta; espere PET-05, PET-09 e PET-18, não necessariamente todas as regras do projeto.
7. Faça outra pergunta direcionada: `Por que a PET-09 e a PET-18 estão não compatíveis? Que alternativas a matriz propõe?`
8. Exporte o JSON da avaliação, salve como `Meu_Resultado_A.json` e compare com `Design_A_Resultado_Esperado.json`.
9. Repita as etapas 2-8 com `Design_B_Entrada.json`. Confirme ID **SYN-PET-INTEGRADO-B-001** e **30 fatos técnicos**. Espera-se PET-05 inconclusivo, PET-09 e PET-18 compatíveis; não uma aprovação global.
10. Faça a pergunta: `Compare o que precisaria mudar no rótulo PVC do design original com a proposta PP, incluindo os critérios que ainda dependem de validação.` **Nota:** este modo local não tem comparação automática entre dois históricos. A pergunta serve para avaliar orientação geral sobre a avaliação atual; use o arquivo `Comparacao_Design_A_vs_B.json` para a comparação verdadeira.

**Cuidado:** não clique em **Criar produto novo** depois de importar o JSON, pois isso limpa o cenário ativo. Importe Design B apenas depois de exportar o resultado de A.

## Roteiro 2 - Testar PDFs e revisão humana

1. Clique em **Criar produto novo**, abra **IA · Documentos** e selecione o extrator **Local**.
2. Carregue `Ficha_Sintetica_Design_A.pdf` e execute a extração.
3. Confira pelo menos os campos `material_corpo`, `transparencia_corpo`, `cor_corpo`, `capacidade_ml`, `material_tampa`, `polimero_rotulo`, junto das respectivas citações.
4. Revise e confirme as informações extraídas.
5. Abra **Componentes** e marque explicitamente `corpo`, `tampa`, `rotulo`, `adesivo` e `tinta` como **Presentes**; os demais como **Ausentes**, SOMENTE NESTA SIMULAÇÃO.
6. Atenção: a extração local **não cobre todos** os dados de fixação, tinta, adesivo e densidade. Para reproduzir exatamente o resultado integrado, use o Roteiro 1 ou insira e confirme manualmente os demais fatos. Sem isso, resultados adicionais devem permanecer inconclusivos.
7. Repita opcionalmente com `Ficha_Sintetica_Design_B.pdf` em um **produto novo**.

## Critérios de aprovação

- O motor nunca emite classe global ou certificação.
- Design A identifica **PET-05, PET-09 e PET-18 como NAO_COMPATIVEL**.
- Design B mantém PET-04 e PET-05 inconclusivos; não inventa testes PET-17 ou homologação PET-16.
- As evidências associadas apontam para o documento sintético adequado (`SYN-INTEGRADO-A-01` ou `SYN-INTEGRADO-B-01`).
- O assistente explica os resultados reais do JSON atualmente carregado e não altera o motor.

## Arquivos

- `Ficha_Sintetica_Design_A.pdf` / `Ficha_Sintetica_Design_B.pdf`: PDFs fictícios para fluxo documental.
- `Design_A_Entrada.json` / `Design_B_Entrada.json`: envelopes com campos completos para avaliação reproduzível.
- `Design_A_Resultado_Esperado.json` / `Design_B_Resultado_Esperado.json`: saída exata de referência do motor.
- `Comparacao_Design_A_vs_B.json`: análise cruzada por regra.
- `MANIFESTO_SHA256.txt`: rastreabilidade dos arquivos do pacote.
