# Persistência controlada — 27/10/2026

Campanha ROS 2: `persistencia_ros2_20261027T184744Z_yjoqaqkq`.

Trinta mensagens Status foram publicadas diretamente em Persist, com identidade, destino e timestamp controlados, alternando success/fail. O DataAccess real gravou os trinta registros; a releitura após encerrar o processo recuperou todos os seis campos, na ordem esperada. A conferência independente dos arquivos copiados confirmou o JSON.

Não se trata de leitura fisiológica nem de consulta pela API do repositório. O ensaio contorna logger e sensores, verifica o lote que atinge o limiar de flush e não avalia perda de energia, fsync ou buffers incompletos. A comparação ROS 1 foi concluída conforme a conferência abaixo.

## Conferência ROS 1–ROS 2

Campanha ROS 1: `persistencia_ros1_20261027T185045Z_xWH4g_`.

Foram conferidos 30 registros em cada campanha contra os estímulos do trace, os resultados JSON e os arquivos copiados após encerramento. Os dados recuperados antes e depois de encerrar o processo coincidem. As cópias do executor são idênticas, e os hashes das fontes preservadas foram verificados.

| Verificação | ROS 1 | ROS 2 |
|---|---:|---:|
| Registros esperados | 30 | 30 |
| Registros recuperados com os seis campos corretos | 30 | 30 |
| Registros recuperados após encerrar o processo | 30 | 30 |

Cada campo de origem foi validado contra o identificador único da própria campanha. A comparação entre versões normaliza apenas esse identificador; os demais campos e a ordem coincidem. São dois lotes de 30 registros, não 60 cenários BDD nem novas medidas de cobertura.

A evidência sustenta preservação da gravação e releitura do lote operacional na fronteira exercitada. Permanecem fora dela o caminho sensor–logger, leituras fisiológicas, consulta pela API, buffers incompletos e durabilidade sob perda de energia. O hash do binário ROS 1 registrado não demonstra, sozinho, sua correspondência com a fonte consultada.
