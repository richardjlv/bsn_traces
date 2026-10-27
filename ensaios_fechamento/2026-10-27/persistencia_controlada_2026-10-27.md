# Persistência controlada — 27/10/2026

Campanha ROS 2: `persistencia_ros2_20261027T184744Z_yjoqaqkq`.

Trinta mensagens Status foram publicadas diretamente em Persist, com identidade, destino e timestamp controlados, alternando success/fail. O DataAccess real gravou os trinta registros; a releitura após encerrar o processo recuperou todos os seis campos, na ordem esperada. A conferência independente dos arquivos copiados confirmou o JSON.

Não se trata de leitura fisiológica nem de consulta pela API do repositório. O ensaio contorna logger e sensores, verifica o lote que atinge o limiar de flush e não avalia perda de energia, fsync ou buffers incompletos. A comparação ROS 1 permanece pendente.
