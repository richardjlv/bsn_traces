# Repetições das features com falha — 25/10/2026

As três features foram reexecutadas separadamente com cobertura, sem edição dos testes ou da produção nesta revisão. Os hashes de fontes foram comparados às campanhas anteriores. Nenhuma tentativa substitui a anterior; a seleção do índice continua identificada explicitamente.

| Feature | Campanha | Resultados internos |
|---|---|---|
| check_bsn | [ros2_20261025T232415Z_v1iy3ef0](../../campanhas_traces/ros2_20261025T232415Z_v1iy3ef0/manifest.json) | [{'failure': 1, 'passed': 7}] |
| knowledge_repo | [ros2_20261025T232722Z_uu8nnywb](../../campanhas_traces/ros2_20261025T232722Z_uu8nnywb/manifest.json) | [{'failure': 1}] |
| data_persistance | [ros2_20261025T232742Z_o1zp8574](../../campanhas_traces/ros2_20261025T232742Z_o1zp8574/manifest.json) | [{'failure': 1, 'xfail': 1}] |

Check_bsn voltou a falhar no caso do oxímetro: nesta repetição, tanto a captura do sensor quanto a do concentrador vieram vazias, causando KeyError em sensor_datapoint. Knowledge_repo voltou a falhar na consulta CLI, agora sem localizar /logger, em vez de /data_access. Os registros indicam falhas de captura/descoberta, mas não isolam sua causa. Consulte resultados.json para os eventos exatos de cada tentativa.

O campo complete=false do coletor é conservado: o critério implementado exige retorno zero do executor. Isso não implica ausência de XML, trace ou cobertura; os artefatos presentes e seus hashes foram preservados. Não se apresenta a repetição como validação bem-sucedida.
