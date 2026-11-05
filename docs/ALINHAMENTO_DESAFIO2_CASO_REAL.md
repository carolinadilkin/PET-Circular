# PET Circular — alinhamento ao Desafio 2 e estudo de caso A/B

**Natureza:** protocolo de prova de conceito (PoC), não laudo de reciclabilidade nem certificação.  
**Escopo:** garrafas PET transparentes (incolor ou azul-claro); matriz PET Circular v0.3.3, 15 regras ativas; motor Python 0.1.2 e Web v0.4.

## 1. Aderência ao desafio

O **Desafio 2 — Soluções para Avaliar e Melhorar a Reciclabilidade de Embalagens Plásticas Utilizando Dados e Inteligência Artificial** contempla avaliação desde a concepção e o design. Seus requisitos incluem princípios de Design for Recycling, **avaliação quantitativa ou comparativa** e uso de informações acessíveis. O PET Circular atende conceitualmente por meio de: (i) matriz rastreável de incompatibilidades, (ii) comparação por critério entre alternativas, (iii) recomendações preventivas e (iv) uso assistivo de IA para interpretar dados documentais.

A conformidade demonstrada depende do **estudo de caso executado**: é preciso comprovar na prática o fluxo, a comparação, as recomendações e pelo menos um uso verificável de IA, sem atribuir à IA decisões que cabem ao motor determinístico.

## 2. Quem utiliza e quando

- **Persona principal:** engenheira(o) de desenvolvimento de embalagens de uma fabricante, transformadora ou marca.
- **Personas secundárias:** sustentabilidade, P&D de materiais e qualidade.
- **Momento de uso:** ideação, especificação, revisão e validação documental **antes** da materialização de um novo design.
- **Entrada:** desenho conceitual ou ficha técnica de componentes, alternativas de material/rótulo/tampa, dimensões, propriedades e dados de triagem conhecidos.
- **Saída:** critérios com evidência, limitações, ressalvas e alterações de ecodesign sugeridas.

“Modo ideação”, “modo desenvolvimento” e “modo validação” não são recursos implementados automaticamente na Web v0.4. São três **níveis de maturidade das informações** que orientam o protocolo.

## 3. Estudo de caso real sem desviar do caráter preventivo

1. **Escolher Design A:** garrafa PET comercial existente e fotografável. Registrar identificação, aplicação, corpo, cor, rótulo, adesivo, tampa, fechamento e dimensões. Anexar fontes documentais e distinguir observação de hipótese.
2. **Preencher a matriz:** registrar cada campo conhecido e suas evidências; deixar lacunas explícitas. Não inferir composição exata apenas pela aparência.
3. **Propor Design B:** alterar 1–3 atributos potencialmente problemáticos (por exemplo material/cobertura do rótulo, adesivo, tampa, cor), mantendo a mesma função da embalagem. B é **projeto ainda não produzido**, não nova embalagem física.
4. **Rodar A e B no motor:** capturar resultados por regra, classificações e recomendações, preservando os estados de confiança.
5. **Comparar objetivamente:** contar incompatibilidades, inconclusões, pendências e transições por critério, com tabela de antes/depois e justificativa de cada mudança.
6. **Demonstrar IA:** oferecer à ferramenta uma ficha/documento técnico apropriado, registrar campos extraídos/sugeridos, conferir manualmente e evidenciar correções. Se não houver disponibilidade de IA real, declarar a função não validada, sem simular sucesso.
7. **Concluir:** avaliar utilidade para a equipe de desenvolvimento, o que pode ser decidido antes da fabricação e o que exige ensaio de triagem/reciclagem ou informação adicional.

## 4. Limites da interpretação

- Design A é **baseline empírica** para testar o processo; o produto-alvo da solução continua sendo o **Design B preventivo**.
- Dados **propostos** de B não são “confirmados” por terem sido digitados. Na implementação atual, regras que exigem confirmação podem permanecer **INCONCLUSIVAS**: isso é um resultado legítimo e deve ser relatado.
- Comparação de regras não equivale a taxa real de reciclagem, rendimento de separação ou certificação RecyClass.
- Não calcular índice global arbitrário para satisfazer o desafio: a alternativa **comparativa** está prevista no enunciado.
- Não afirmar que um redesenho melhora a reciclagem no mundo real sem evidência experimental; afirmar somente que reduz **incompatibilidades sinalizadas pelos critérios implementados**, quando demonstrado.
- Respeitar limites do recorte PET transparente; nenhum resultado é transferível automaticamente a outros polímeros.

## 5. Evidências mínimas para concluir a PoC

| Evidência | Como registrar |
|---|---|
| Embalagem A | Fotos + descrição dos componentes + origem das especificações |
| Proposta B | Tabela de alterações, justificativas e status PROPOSTO |
| Motor | Exportação dos resultados de A e B, versão da matriz e do motor |
| Comparação | Quadro por regra: A, B, transição, ressalva |
| IA | Documento de entrada, extração gerada, correção humana e limitações |
| Reprodutibilidade | Versão do código, arquivos de entrada, procedimento de execução |

## 6. Extensão futura para outro polímero

A implementação do PET é referência de **esforço estrutural**, não de horas medidas: recorte; pesquisa bibliográfica e regulatória; elaboração/validação de regras e fontes; modelagem dos campos; implementação do catálogo e mapeamento de saídas no motor; criação de cenários/testes; integração com interface e IA; revisão de casos industriais; documentação e QA. Não presumir que regras ou critérios de PET se aplicam diretamente a PP, PEAD, PS ou PVC. Um novo polímero requer matriz própria e validação especializada.

**Registro do desenvolvimento PET:** a ficha de estudo de caso da Biblioteca mantém histórico reportado de 16 commits, 5 PRs mesclados, 15 regras ativas e 127 testes; são marcos de implementação, **não estimativa de horas** nem indicador de trabalho futuro.

## 7. Referências de governança

- Enunciado oficial do *Desafio 2*, CBQ 2026, consultado na documentação do projeto.
- Matriz técnica PET Circular v0.3.3 e seus registros de fontes, conforme `docs/ORIGENS.md`.
- `docs/WEB_V04_IMPLEMENTACAO.md` para o que está efetivamente implementado.
- `docs/UX_V04_ESPECIFICACAO_APROVADA.md` para premissas de experiência e interface.
