# Campanhas de trace e cobertura do SA-BSN

Este repositório preserva evidências de execução das features BDD da validação da migração ROS 1--ROS 2. Cada diretório em `campanhas_traces/` é imutável: contém o manifesto, hashes, fontes arquivadas, configuração, resultados JUnit, logs compactados e o trace de eventos dos cenários.

## Leitura de uma campanha

Em `<campanha>/<feature>/`:

- `trace.jsonl`: eventos de início e término de cenários e passos, além dos resultados do pytest;
- `internal_junit/*.xml`: resultado individual de cada cenário;
- `execution.log.gz`: saída integral da execução;
- `outer.xml`: resultado do invólucro `launch_testing`;
- `coverage_production.xml` e `coverage_production.json`: cobertura do recorte de produção, quando a coleta a habilitou;
- `manifest.json`: comandos, versões, hashes, totais e limitações da campanha.

## Situação inicial deste acervo

As campanhas de 22/10/2026 com `check_bsn`, `knowledge_repo`, `target_system`, `data_persistance`, `health_status`, `injector` e `bsn_p03` foram executadas com `coverage_enabled: false`, para reduzir o consumo de armazenamento durante a coleta de traces. Elas preservam os traces e resultados por feature, mas **não devem ser usadas como evidência de cobertura**.

As campanhas históricas `ros2_20261022T181912Z_lo_2z9we` (`managing_system`) e `ros2_20261022T182336Z_la6kiyl4` (`check_bsn`) incluem cobertura por feature. Seus manifestos registram as divergências de cenário daquela rodada; cobertura e aprovação funcional devem ser interpretadas separadamente.

As próximas coletas devem usar `ferramentas_traces/coletar_ros2.py` sem `--without-coverage`, executando uma feature por vez e publicando a campanha antes de liberar espaço local.

## Cobertura geral

As campanhas gerais ROS 1 (`bsn2`) e ROS 2 (`bsn_ros2`) estão em [cobertura_geral](cobertura_geral/README.md), com arquivos integrais compactados, inventários SHA-256 e relatórios para consulta. As campanhas por feature foram executadas separadamente, cada uma com inicialização e encerramento próprios.

## Diagnósticos posteriores

- [23/10/2026 — cenário temporal de managing_system](diagnosticos/managing_system_2026-10-23/README.md): reexecução após alteração da ordem dos cenários; aprovação do executor externo, sem nova cobertura nem resultados individuais preservados.

- [23/10/2026 — isolamento dos cenários de adaptação](diagnosticos/managing_system_isolado_2026-10-23/README.md): temporal aprovado sozinho e após recuperação em pilha nova; execução completa com 8 PASS, 2 XFAIL e 1 timeout no estímulo de registro, corrigido e aprovado em reexecução individual. XML internos, traces e cobertura preservados.
