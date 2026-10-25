# Revalidação de managing_system — 25/10/2026

A retomada encontrou aproximadamente 28 GiB livres no volume, removendo o bloqueio de armazenamento da etapa anterior. Foi validado o código `becfda5`, que aguarda até cinco segundos pelos endpoints exigidos pelas asserções de topologia. A configuração e a lógica de produção não foram alteradas nesta retomada.

A campanha [topologia isolada](../../campanhas_traces/ros2_20261025T051128Z_md_b0ax2/) aprovou os seis casos, sem resultados internos ausentes do trace. A cobertura registrou 2.341/3.147 linhas e 511/888 ramos; inclui inicialização, execução e encerramento, não apenas instruções associadas às asserções. O executor externo aprovou separadamente e não integra a contagem dos seis casos.

A execução completa foi iniciada com limite operacional de 1.800 s, diante da carga elevada observada no ambiente (memória disponível próxima de 1 GiB e swap ocupado). Esse limite encerra a coleta; não modifica o prazo de dez segundos do cenário temporal nem os demais critérios funcionais. A carga é uma condição observada, não uma causa isolada experimentalmente para os problemas anteriores.

A primeira tentativa completa, [051720Z](../../campanhas_traces/ros2_20261025T051720Z_qxwg_ap6/), não foi finalizada pelo coletor. Na retomada às 05:44 UTC não havia processos ativos, embora o manifesto permanecesse em `running`. Os registros disponíveis mostram seis aprovações de topologia e uma falha de preparação: nenhum comando inicial do oxímetro foi observado em 90 s. A causa da interrupção não foi determinada. Os arquivos foram preservados com hashes próprios e sem modificar o manifesto original; não há cobertura consolidada dessa tentativa. Uma nova campanha foi iniciada em outro diretório, com aproximadamente 4 GiB de memória disponível e sem processos ROS residuais.

A nova execução completa [054442Z](../../campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/) terminou com **9 PASS e 2 XFAIL, sem falhas inesperadas**, código de retorno zero e coleta marcada como completa. Foram preservados 11 inícios de cenário, 29 inícios de passo e os seis XML internos; não há casos dos XML ausentes do trace. O teste externo agregador não foi somado aos casos internos. Os hashes dos arquivos preservados foram conferidos.

| Grupo | Resultado interno |
|---|---|
| Topologia | 6 PASS |
| Aumento de frequência | 1 PASS |
| Recuperação | 1 XFAIL no Then: nenhum comando inferior ao pico de 10,480 Hz em 30 s |
| Prazo de dez segundos | 1 PASS, executado depois de recuperação em nova pilha |
| Ausência de comandos | 1 XFAIL no Then: comandos observados |
| Registro da tentativa | 1 PASS |

A cobertura da união das seis montagens foi de **2.357/3.147 linhas (74,90%) e 518/888 ramos (58,33%)**. Essa é uma execução da feature com pilhas independentes, não uma repetição da suíte geral. Não se somam seus percentuais aos das outras campanhas, nem se atribui a cobertura somente aos passos BDD.

O log não contém `PytestUnhandledThreadExceptionWarning` ou `TimeoutExpired`. Contém exceções no encerramento, como `ExternalShutdownException`, `KeyboardInterrupt` e `RCLError` por contexto já encerrado. Portanto, ausência de falhas inesperadas de teste não significa ausência de mensagens de erro dos processos. A marcação de coleta completa pelo coletor e os hashes não provam que todo processo gravou todos os seus contadores antes do encerramento. As tentativas anteriores permanecem no [diagnóstico de isolamento](../managing_system_isolado_2026-10-23/README.md).

## Interpretação dos oráculos

A marcação XFAIL é restrita a `BehaviorExpectationNotMet`, emitida pelas asserções de recuperação e ausência de comandos. Erros de prontidão não devem ser tratados como essas falhas esperadas. A descrição de recuperação continua mais ampla que sua observação: interromper a injeção e esperar não mede diretamente o cruzamento da estimativa de confiabilidade pelo limiar.

O cenário temporal observa emissão de comando, sem correlação causal completa com o estímulo nem medição da frequência efetivamente executada. Uma aprovação após isolamento valida o critério implementado nessa montagem; não demonstra preservação integral do mecanismo de adaptação. O cenário de registro verifica encaminhamento em `/persist`, não consulta armazenamento durável.

## Reprodução da rodada completa

```sh
. /opt/ros/jazzy/setup.sh
. /ros_ws/install/setup.sh
/usr/bin/python3 src/ferramentas_traces/coletar_ros2.py --features managing_system --direct-readiness --timeout 1800
```

Executado a partir de `/ros_ws`, com os grupos padrão `topology,increases,recovers,deadline,silent,logging`. Código de teste no commit `becfda5`; fontes, estado local e diferenças estão no snapshot da campanha. Não foi alterado código de produção nesta retomada. Os quatro testes do bootstrap de cobertura também aprovaram.
