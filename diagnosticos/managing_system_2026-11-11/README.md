# managing_system ROS 1 — revalidação de 11/11/2026

A feature foi executada isoladamente após a correção da margem de confiabilidade: **11 casos, 10 PASS, um XFAIL, sem falhas inesperadas**. O executor externo aprovou e não foi somado aos casos internos. O cenário de aumento inclui os passos Then e And para comando e registro, ambos aprovados. O cenário de redução após a recuperação também aprovou.

O XFAIL é `test_no_adaptation_is_triggered_while_sensor_reliability_stays_above_the_threshold_g4g5`: exige ausência de comandos acima do limiar. Não é equivalente à ausência de comandos dentro da margem, validada no ensaio controlado de 10/11. A expectativa BDD permanece não atendida.

O hash do executável enactor é igual ao da campanha controlada ROS 1 de 10/11. O snapshot identifica a fonte corrigida por hash. A coleta não recompilou o sistema. O trace preserva 11 inícios e fins de cenário, 30 inícios de passo, 29 fins e um erro associado ao XFAIL.

A cobertura de produção do relatório textual é 2.837/4.263 linhas (66,55%). Os totais globais do JSON exportado incluem fontes externas e não devem substituir esse recorte. A cobertura inclui preparação e encerramento, não é atribuível separadamente a cada cenário.

O arquivo ros1.tar.gz conserva a campanha completa, com traces, resultados internos, cobertura, perfis, logs, fontes e manifestos originais. Os hashes do manifesto foram conferidos antes do arquivamento. Esta execução não revalida o ROS 2 nem altera suas falhas esperadas históricas.
