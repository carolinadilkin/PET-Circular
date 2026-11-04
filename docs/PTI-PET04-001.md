# PTI-PET04-001 v0.1 — Cobertura não-PET (método interno)

**Decisão de projeto:** os casos geométricos foram considerados aprovados pela responsável pelo projeto. Não se trata de ensaio físico ou homologação pela RecyClass.

## Medição
- **M1 — Projeções:** informar área de referência e área coberta, em cm², para frente e verso; calcular cada razão e adotar o maior percentual como alerta conservador.
- **M2 — Lateral:** informar área superficial lateral de referência e área lateral coberta, em cm²; calcular `100 * área_coberta / área_referência`.
- Denominadores positivos; áreas cobertas entre zero e as respectivas referências. Sobreposições contabilizadas uma vez. Excluir tampa e faces planas de base/topo na convenção interna. Declarar método e fonte (CAD, desenho ou medição).
- Percentual legado continua aceito para não quebrar casos existentes, mas é identificado como não homologado no PTI.
- Divergência superior a 0,01 ponto percentual entre percentual informado e geométrico exige conciliação antes de emitir alerta baseado em percentual. Este limite é tolerância de arredondamento de software, **não** tolerância de medição.
- Se há incerteza declarada que atravessa o limite indicativo (50% para ≤500 mL, 70% acima), registrar `LIMITROFE`, sem afirmar acima/abaixo.

## Gatilhos, interpretação e limites
- Rótulo de polímero diferente do PET com cobertura >50%, sleeve integral ou metalização identificada: registrar `REQUERIDO` para avaliação aplicável do SEP-01, a conferir segundo o protocolo vigente.
- Gatilhos desconhecidos explicitamente relevantes: `PENDENTE`. Nenhum gatilho verificado: `NAO_REQUERIDO` **para o conjunto observado**, não declaração de dispensa universal.
- Sem documentação válida da identificabilidade, PET-04 permanece `INCONCLUSIVO`. Valor geométrico não é eficiência NIR nem prova de reciclabilidade.
- O procedimento M1/M2 não é apresentado como equivalente à determinação normativa RecyClass/EN 18120-1.

## Rastreabilidade
Registrar produto/versão, capacidade, tipo/material da decoração, método, áreas, percentual, evidência, revisor, data, limitações e versão PTI. Valores extraídos de documento precisam confirmação humana no aplicativo.
