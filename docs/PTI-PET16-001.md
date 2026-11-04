# PTI-PET16-001 v0.1 — Interpretação dimensional da embalagem PET

**Status:** procedimento interno de aplicação do motor PET Circular; não é homologação ou certificação RecyClass. **Motor:** 0.1.2. **Matriz:** 0.3.3 (anotação de implementação no catálogo).

## Referências
- RecyClass, *DfR Guidelines — Transparent Clear & Light-Blue PET Bottles*, março/2026, categoria **Size**: `≤4 cm (compacted)` e `>5-liter content` na coluna de incompatibilidade: https://recyclass.eu/wp-content/uploads/2026/03/RecyClass-DfR-Guidelines-Transparent-clear-light-blue-PET-bottles.pdf
- RecyClass, *Sorting Evaluation Protocol SEP-01 v3.0*, fevereiro/2026, §4.3: em embalagens rígidas, verificação distinta de **ao menos duas das três dimensões <50 mm**, após compressão/fricção, podendo demandar teste de tambor peneira: https://recyclass.eu/wp-content/uploads/2026/03/SEP-01-V3.0.pdf

## Requisitos de entrada e interpretação

1. **Capacidade**: usar valor confirmado `volume_l` ou `capacidade_ml`/`volume_ml` convertido a litros. Exigir valor positivo. Caso duas unidades fornecidas diverjam, sinalizar conflito e não usá-las para concluir o veto de volume. `>5 L` é veto; `=5 L` não é veto.
2. **Dimensão compactada**: usar `dimensoes_apos_compactacao` como dimensão de controle da amostra física **definida no protocolo do projeto**, expressa em centímetros. Registrar a escolha da dimensão e suas condições no campo `protocolo_compactacao`. Não substituir com dimensões originais, CAD ou conversão de capacidade.
3. **Proveniência dimensional**: exigir `fonte_medicao` (identificação do relatório/registro), `protocolo_compactacao` e confirmação explícita `validacao_operacional_4cm = sim`, cada um como fato CONFIRMADO. Essa validação é uma **declaração técnica interna rastreável**, não homologação RecyClass.
4. **Veto dimensional**: `≤4 cm` **somente** com as três verificações anteriores e medição em cm válida. Ausência de qualquer verificação produz INCONCLUSIVO e possível alerta; dado isolado não gera veto.
5. **Sem vetos identificados**: `NAO_ACIONADA` somente quando capacidade válida `≤5 L` e dimensão compactada válida `>4 cm` com protocolo/validação/fonte; **não** implica aprovação global ou sucesso no SEP-01.
6. **Independência dos vetos**: capacidade `>5 L` ou dimensão comprovada `≤4 cm` geram `NAO_COMPATIVEL` mesmo se o outro elemento não estiver preenchido. Pendências do outro elemento são preservadas no resultado.
7. **Conflitos e dados inválidos**: capacidade ausente, inválida ou divergente impede conclusão baseada no volume. Dimensões negativas, zero, não numéricas e unidades diferentes de cm não fundamentam veto dimensional.

## Limitação operacional
A diretriz DfR disponível não define, nesta tabela, qual dimensão de controle deve representar os 4 cm após compactação. O método e a dimensão escolhidos deverão ser explicitados no procedimento interno/relatório; esta automação depende de **aceite humano**. O SEP-01 possui parâmetro próprio (<50 mm em duas dimensões) e não é substituído por este cálculo. **Nenhuma classe global ou certificação é emitida.**

## Testes automatizados
Limites 5 e 5,001 L; 4 e 4,001 cm; ausência de fonte, protocolo ou validação; dados provisórios e inválidos; unidades inconsistentes; divergência entre L e mL; veto independente de volume e dimensão.
