# Investigação da recuperação no ROS 2 — 11/11/2026

O diagnóstico preserva tentativas sucessivas; o sucesso do executor externo não significa aprovação do cenário marcado XFAIL.

## Defeitos reproduzidos em componentes

- `DataAccess.process_query`: o denominador incluía estados `running`, embora o cálculo de confiabilidade do legado e o auxiliar interno considerem apenas `success` e `fail`. Dois dos cinco vetores falharam antes da correção; os cinco aprovaram depois.
- `ReliabilityEngine.execute`: referências separadas por vírgula eram descartadas por `Enactor.receive_strategy`, que espera ponto e vírgula. Um teste passando a mensagem produzida diretamente ao consumidor falhou antes e aprovou depois. O separador corrigido corresponde ao legado.
- A seleção de testes de DataAccess, planejador e controlador, incluindo os novos casos, registrou 66 aprovações em `components_after.xml`.

## Execuções BDD intermediárias

| Campanha | Condição | Resultado interno |
|---|---|---|
| `ros2_20261111T133144Z_bnjiswrk` | Código inicial | XFAIL na redução |
| `ros2_20261111T133422Z_bhjjp027` | Denominador corrigido | Falha na preparação: exigência de comando espontâneo |
| `ros2_20261111T183241Z_wzx91_w1` | Prontidão sem exigir comando espontâneo | XFAIL; pico de 2,39 Hz |
| `ros2_20261111T183609Z_2h3915oj` | Separador da estratégia corrigido | XFAIL; pico de 2,29 Hz |

A correção dos componentes não bastou para aprovar essas execuções. O lançamento BDD ROS 1 utiliza `actuation_freq=0.2`, enquanto o ROS 2 herdava o padrão de produção `0.02`. A próxima execução usa `0.2` exclusivamente no lançamento BDD; o padrão de produção permanece `0.02`.

Os XML e logs unitários nesta pasta e os diretórios de campanha preservam os resultados. A configuração e o critério usados em cada tentativa devem acompanhar qualquer comparação.

## Reativação dos componentes

A campanha `ros2_20261111T183919Z_j5awyd3j`, já com planejamento a 0,2 Hz, ainda registrou XFAIL (pico de 2,28 Hz). Os logs mostram desativação e ativação dos sensores na inicialização. `_process_context_response` mantinha a marca de desativação depois de receber `activate`, excluindo os sensores das variáveis ajustáveis do planejamento. Um teste de transição reproduziu o defeito; a correção limpa a marca na reativação de sensores e concentrador. Diferentemente do protocolo de separadores, trata-se de tratamento explícito da reativação no ciclo de vida ROS 2, não de transcrição literal da implementação de sensores do legado.

A seleção ampliada de componentes aprovou 67 casos em `components_reactivation_after.xml`.

## Desempate de prioridades — 12/11/2026

A execução `ros2_20261111T184224Z_66h2p_ui` ainda registrou XFAIL. O planejador já ajustava sensores reativados, mas manteve a referência do oxímetro em 1,0. Foi identificada outra diferença de implementação: o comparador C++ usa prioridade e nome do componente; a ordenação Python usava somente prioridade. Um teste com duas ordens de inserção da mesma configuração produziu referências diferentes antes da correção e iguais depois. O desempate foi alinhado ao comparador C++.

A campanha `ros2_20261112T002519Z_yngm5q5r` aprovou como XPASS após o desempate: pico de 2,58 Hz e comando posterior de 2,43 Hz, com verificação de registro aprovada. A marcação de falha esperada foi removida para a próxima execução. A seleção ampliada registra 68 aprovações em `components_ordering_after.xml`. A mudança de resultado acompanha o último ajuste sob as demais correções já aplicadas; não demonstra que esse ajuste isoladamente bastaria sobre o código inicial.
