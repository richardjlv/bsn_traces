# Conferência pareada do concentrador — 27/10/2026

## Evidências

- ROS 1: `hub_ros1_20261027T174939Z_EZoyyZ`.
- ROS 2: `hub_ros2_20261027T174516Z_eb8d4j5f`.
- Executor idêntico nas duas campanhas: SHA-256 `46fb969763be7c88ca065c6b1d91261233d5de5cabb7d57d4cb0da1d566be15f`.

A conferência recalculou, a partir dos traces, as contagens de amostras, as asserções das janelas estáveis e a primeira resposta correspondente. Também verificou os hashes das cópias das fontes e do executor. Foram gerados arquivos SHA256SUMS para integridade futura. O hash do binário ROS 1 foi registrado na coleta, mas sua correspondência com as fontes não é demonstrada apenas por esses hashes.

## Resultado funcional

Nove fases aprovadas em cada implementação: três repetições da sequência baixo–alto–retorno. Os seis marcadores de leitura, os seis riscos e os estados esperados são iguais nos ensaios pareados. Os estados esperados foram 20, 90 e 20. Depois da acomodação operacional de dois segundos, todas as amostras observadas até cinco segundos satisfizeram as asserções, com pelo menos três amostras por fase.

Isso sustenta a preservação funcional para os vetores selecionados na fronteira de entrada sintética dos seis sensores até a saída do concentrador. Não abrange a geração pelo paciente, classificação dos sensores, persistência ou malha de adaptação. O nome `recuperado` identifica o retorno do vetor de risco, não a recuperação da confiabilidade dos sensores.

## Tempos observados

| Repetição | Fase | ROS 1 (ms) | ROS 2 (ms) |
|---|---|---:|---:|
| 1 | baixo | 252.17 | 166.79 |
| 1 | alto | 323.65 | 167.86 |
| 1 | recuperado | 237.32 | 164.51 |
| 2 | baixo | 60.95 | 165.09 |
| 2 | alto | 335.67 | 161.63 |
| 2 | recuperado | 290.62 | 161.74 |
| 3 | baixo | 55.94 | 160.17 |
| 3 | alto | 327.34 | 159.44 |
| 3 | recuperado | 277.77 | 159.16 |

No ROS 1, seis das nove respostas ultrapassaram 250 ms; no ROS 2, nenhuma. A aprovação funcional não inclui esse indicador temporal. A latência é medida do início da publicação do lote até a primeira saída correspondente, no relógio monotônico do observador. Os ambientes são diferentes e as três repetições pertencem à mesma execução de cada sistema: não são nove campanhas independentes. Os dados não comprovam superioridade do middleware nem atendimento universal ao requisito BSN-P03, cuja fronteira original é diferente.

## Uso na monografia

Acrescentar como ensaio complementar controlado, separado das contagens BDD e da cobertura histórica. A evidência resolve a falta de um oráculo numérico explícito para esses vetores do concentrador e demonstra retorno ao estado esperado. Não elimina as pendências de persistência, interpretação da política de adaptação e avaliação temporal da cadeia completa. As tentativas anteriores permanecem preservadas como problemas de preparação, inclusive a tentativa intermediária ROS 2 que perdeu o primeiro lote ao antecipar a prontidão.
