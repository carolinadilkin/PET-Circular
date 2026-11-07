# Critérios de aceite — PET Circular v0.11

## Fluxo funcional esperado
1. Importar Design A por PDF/JSON ou iniciar manualmente; conferir identidade, material do corpo, capacidade e presença de componentes.
2. Visualizar os 84 atributos, incluindo os que não possuem dados, e registrar valores via listas, múltipla escolha e números/textos.
3. Declarar a conferência do conjunto de dados apenas uma vez.
4. Avaliar: tampa PP declarada é reconhecida; PET-07 pode exigir outros requisitos. Ausência explícita de sleeve produz PET-19 `NAO_APLICAVEL`. Polímero secundário do corpo explicitamente inexistente pode produzir PET-02 `NAO_ACIONADA`.
5. Exportar entrada, relatório por regra e IPR-PET; verificar alertas de base declaratória e inconclusões legítimas.
6. Criar Design B como hipótese de redesenho, preservando o original, e comparar A/B sem transformar projetos propostos em comprovação industrial.

## Testes e pendências
- 169 testes executados no pacote v0.11; 0 falhas; 2 ignorados.
- Teste de Windows na instalação do usuário: pendente.
- Execução Gemini com chave e quota reais: pendente.
- Revisão independente de composição, ensaios NIR, compactação, PET-17 e IPR-PET: pendente.
- Auditoria WCAG completa e piloto industrial: não demonstrados.

## Semântica crítica
`DECLARADO` é base para pré-avaliação condicional; `CONFIRMADO` requer suporte. `Desconhecido` não significa `Ausente`; ausência de dado técnico não pode gerar compatibilidade automática. O IPR-PET não é porcentagem reciclada, nem certificação.