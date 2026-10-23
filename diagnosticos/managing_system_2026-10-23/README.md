# Diagnóstico do cenário temporal de managing_system — 23/10/2026

## Falha histórica

A campanha [ros2_20261022T181912Z_lo_2z9we](../../campanhas_traces/ros2_20261022T181912Z_lo_2z9we/managing_system/) registrou 11 casos: nove aprovados, uma falha esperada e uma falha inesperada. Esta última pertence ao cenário de emissão de comando em até 10 segundos após degradação da confiabilidade (BSN-C10).

O cenário de recuperação precedia o temporal na mesma pilha ROS. O log histórico registra o último comando anterior ao teste para `/g3t1_1` em 39,77 Hz (instante 1792693330.259); o estímulo temporal começa em 1792693339.619. O controlador somente publica se a nova frequência calculada estiver entre 0,1 e 40 Hz. Esses achados são compatíveis com interferência pelo estado acumulado e rejeição de aumentos acima do limite. A frequência candidata e a confiabilidade durante toda a janela não foram capturadas para confirmar cada decisão interna.

## Alteração e reexecução

O cenário temporal foi movido para antes do cenário longo de recuperação. Não foram alterados passos, asserções, prazo de 10 segundos, marcações de falha esperada ou código de produção nesta intervenção. A ordem anterior está preservada na campanha histórica. As fontes aqui arquivadas foram copiadas após a reexecução; o comentário explicativo na feature foi acrescentado depois dela. Não são um snapshot integral do ambiente executado.

Comando executado em `/ros_ws`:

```sh
ROS_LOG_DIR=/tmp/bsn_ros_log PYTEST_ADDOPTS='' python3 -m pytest -q src/bsn_ros2/features/test/test_managing_system_bdd.py > /tmp/bsn_managing_retest_escalated.log 2>&1
```

O processo retornou zero e `resultado_executor.txt` registra `1 passed in 158.14s`. Esse único teste é o executor externo que inicia a feature e exige retorno zero do pytest interno. Não houve XML interno nem saída detalhada dos cenários preservados nesta reexecução: não se atribui um novo total de PASS/XFAIL/XPASS aos casos. Falhas esperadas e aprovações inesperadas não estritas podem coexistir com retorno zero. Não houve coleta de cobertura ou trace estruturado por passo nesta rodada. Os resultados de 22/10 permanecem válidos como registro histórico e não foram substituídos.

A tentativa anterior foi bloqueada pela sandbox ao abrir sockets DDS; seu log está separado em `tentativa_sandbox.log.gz`. O arquivo `ros_logs.tar.gz` conserva os logs ROS das duas tentativas, identificados pelas pastas de início 02:06:17 (sandbox) e 02:07:38 (reexecução autorizada), em UTC. O resumo da primeira tentativa que não pôde criar o diretório padrão de logs não foi preservado antes de ser reutilizado o arquivo temporário.

## Alcance e pendências

A aprovação após reordenar a feature sustenta uma mitigação da interferência observada, não independência dos cenários. A solução robusta exige uma montagem própria ou restauração verificável do estado por cenário. O `Given` atual não mede a estabilidade da confiabilidade; o `Then` aceita a chegada de qualquer comando após iniciar os relatos `fail`, sem demonstrar o cruzamento do limiar ou o nexo causal com o estímulo. A recuperação e a política de limites continuam exigindo avaliação própria. Esta reexecução não corrige nem comprova resolução das falhas esperadas históricas.
