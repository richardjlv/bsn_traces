# Margem de confiabilidade: validação pareada de 10/11/2026

Os quatro casos aprovaram em ROS 1 e ROS 2 sob o mesmo oráculo `symmetric_deadband_v1`. Foram preservados resultados, traces, logs, scripts e fontes identificadas por hash. A auditoria conferiu fontes copiadas, 40 respostas por caso, comandos registrados e tolerâncias numéricas.

| Caso | Respostas por versão | Comandos ROS 1 | Comandos ROS 2 |
|---|---:|---:|---:|
| Degradação (0,5) | 40 | 40 | 40 |
| Acima da referência (0,95) | 40 | 40 | 40 |
| Erro zero (0,8) | 40 | 0 | 0 |
| Dentro da margem (0,79) | 40 | 0 | 0 |

A referência é 0,8, a margem relativa 0,02, o ganho 50 e a frequência inicial 10 Hz. Foi corrigido apenas o limite inferior de `apply_reli_strategy` no ROS 1: agora é negativo. O controlador ROS 2 permaneceu inalterado. As tolerâncias conservam a precisão de serialização de cada versão; aprovação não significa identidade textual dos comandos.

O log ROS 1 contém uma mensagem de conexão interrompida ao final da execução. Os quatro casos têm 40 respostas e os comandos previstos; não foi identificada perda nas observações contabilizadas. Isso não determina a causa da mensagem. Respostas vazias fora das janelas ativas são produzidas pelo serviço substituto e também aparecem nos logs.

A evidência abrange o controlador real com serviços substitutos. Não revalida o BDD managing_system, a recuperação da malha completa ou a estratégia de custo. As campanhas de 27/10 permanecem como caracterização anterior à correção. O hash do executável ROS 1 consta do resultado; o binário não é copiado pelo coletor.
