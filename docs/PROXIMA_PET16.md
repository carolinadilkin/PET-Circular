# Próxima tarefa — PET-16 (escopo direto)

A PET-04 está implementada com o PTI-PET04-001 v0.1. Na PET-16, o motor já separa o veto por **capacidade >5 L** da pendência de **dimensão pós-compactação ≤4 cm**.

## Decisão de implementação proposta

1. Preservar a não compatibilidade por capacidade nominal comprovada >5 L, sem depender do ensaio de compactação.
2. Distinguir claramente informação insuficiente de um possível alerta de dimensão compactada ≤4 cm; não classificar pela geometria CAD original.
3. Só habilitar classificação definitiva por dimensões compactadas quando o protocolo operacional de medição e sua evidência tiverem sido aceitos. Não equiparar o parâmetro de 4 cm ao procedimento SEP-01 de 50 mm.

## Critério de conclusão

O motor deve emitir justificativas e pendências separadas para capacidade e compactação, sem produzir certificação global. Seguir com implementação incremental; evitar estudos geométricos extensos nesta fase.
