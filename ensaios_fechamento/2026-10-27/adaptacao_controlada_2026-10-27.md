# Adaptação controlada ROS 2 — 27/10/2026

Campanha: `adaptacao_ros2_20261027T181847Z_o_a_z2b1`.

O nó real de controle foi executado com dois serviços substitutos para fornecer parâmetro e confiabilidade. A referência foi enviada por Strategy; a inicialização dos alvos, por Event. Não houve alteração de produção. Os quatro casos concluíram e concordaram com a caracterização da política ROS 2.

| Caso | Respostas controladas | Comandos | Primeiro comando |
|---|---:|---:|---|
| degradacao | 40 | 40 | freq=10.15 |
| acima_referencia | 40 | 40 | freq=9.93 |
| erro_zero | 40 | 0 | nenhum |
| dentro_margem | 40 | 0 | nenhum |

Referência 0,8; confiabilidades 0,5, 0,95, 0,8 e 0,79; ganho 50; margem 0,02; frequência inicial do alvo 10 Hz. A comparação numérica usa a sequência analítica e meia unidade da precisão serializada (0,005 Hz no ROS 2), com 1e-9 adicional. Os valores exatos estão no trace.

As contagens foram conferidas contra o trace. `characterization_matches=True` não é equivalência entre versões nem atendimento a um requisito independente: descreve concordância com a política inspecionada. A comparação ROS 1 integrada permanece pendente. O ensaio isolado anterior indica emissão de comandos no legado também dentro da margem, a confirmar no nó real.

A ausência de comando foi observada com respostas de serviço durante a janela e com controles positivos na mesma execução. Ainda assim, não houve sensor, adaptador ou malha de realimentação real: a frequência efetivamente produzida pelo sensor não foi medida. Os valores de confiabilidade foram fornecidos pelo ensaio, não estimados a partir de falhas reais.

A tentativa anterior, `adaptacao_ros2_20261027T181738Z_r6hvnxd_`, permanece preservada: a comparação inicial exigia arredondamento idêntico nos empates decimais e foi corrigida para considerar a resolução serializada. Não foi usada como aprovação nem apagada.

## Comparação integrada ROS 1–ROS 2

ROS 1: `adaptacao_ros1_20261027T182917Z_N5qKxD`. O executor preservado é idêntico ao da campanha ROS 2. As contagens, os valores dos comandos e as consultas foram conferidos contra os traces; os hashes das fontes preservadas foram verificados.

| Caso | Respostas ROS 1 / ROS 2 | Comandos ROS 1 / ROS 2 | Primeiro comando ROS 1 / ROS 2 |
|---|---:|---:|---|
| degradacao | 40 / 40 | 40 / 40 | freq=10.150000 / freq=10.15 |
| acima_referencia | 40 / 40 | 40 / 40 | freq=9.925000 / freq=9.93 |
| erro_zero | 40 / 40 | 40 / 0 | freq=10.000000 / nenhum |
| dentro_margem | 40 / 40 | 40 / 0 | freq=10.005000 / nenhum |

A diferença de emissão dentro da margem foi reproduzida nos nós reais. Com erro zero, o legado publica comandos repetindo 10 Hz; com confiabilidade 0,79 e referência 0,8, aumenta a frequência em incrementos de 0,005 Hz. O ROS 2 não emite comandos nesses dois casos. A redução acima da referência ocorre em ambas as versões sob estímulo controlado; portanto, o cenário BDD anterior de recuperação não pode ser explicado simplesmente por uma incapacidade do controlador ROS 2 de reduzir a frequência. As entradas produzidas pelo estimador e pelo planejador, bem como a montagem daquele cenário, continuam relevantes para investigar sua causa.

O erro zero satisfaz a condição C++ `error > margin*reference || error < margin*reference` quando a referência é positiva; a condição Python `abs(error) > margin*reference` o mantém dentro da margem. Isso confirma uma divergência observável, sem atribuir automaticamente defeito à implementação migrada. A política pretendida deve ser explicitada antes de classificar a diferença como regressão ou correção deliberada.

O aviso TCP/IP informado no terminal não veio acompanhado de perda observável nos casos: todos os comandos esperados pela caracterização ROS 1 estão no trace. A origem exata da conexão não está identificada nesses artefatos, portanto não se atribui o aviso com certeza ao encerramento. As respostas vazias registradas antes e entre casos são deliberadas no serviço substituto, para não fornecer estímulos fora das janelas; o legado as registra como erro.

Esta evidência é restrita à fronteira serviços/eventos/estratégia–comando. Não mede frequência efetiva no sensor, consumo energético ou recuperação da confiabilidade real.
