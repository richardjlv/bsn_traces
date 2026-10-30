# Revalidação das reversões ROS 1 — 30/10/2026

A campanha de 30/10/2026 avaliou separadamente a retirada das correções B2, B3, B4, B5 e B7 sobre uma mesma cópia da referência ROS 1. Uma execução inicial e outra final conservaram todas as correções. Cada rodada executou 27 lançamentos, com 156 casos internos; os 27 executores externos foram contabilizados separadamente. Todas as compilações terminaram com sucesso. O conjunto não inclui os testes gtest da biblioteca e não substitui a campanha geral de cobertura.

**Tabela 4.2 — Casos internos da campanha de reversões de 30/10/2026.**

| Rodada | Aprovados | Falhas esperadas | Reprovados |
|---|---:|---:|---:|
| Referência inicial | 154 | 2 | 0 |
| Sem B2 | 153 | 2 | 1 |
| Sem B3 | 151 | 1 | 4 |
| Sem B4 | 154 | 2 | 0 |
| Sem B5 | 150 | 1 | 5 |
| Sem B7 | 150 | 2 | 4 |
| Referência final | 154 | 2 | 0 |

Fonte: XML internos e [registros preservados da campanha](https://github.com/richardjlv/bsn_traces/tree/main/reversoes_ros1/2026-10-30).

As duas referências registraram 154 aprovações e duas falhas esperadas, sem falhas inesperadas. A retirada de B3, que corrige o retorno de uma função declarada bool, resultou em quatro reprovações internas de managing_system. O log registra o encerramento de reli_engine com código −4, seguido do esgotamento do limite de 120 segundos do executor. Esse erro externo não foi somado aos casos internos. A manifestação foi observada com Clang 6.0 e otimização desabilitada; não é uma consequência universal em qualquer ambiente.

A retirada de B5, relativa à obtenção da configuração na inicialização, produziu cinco reprovações em managing_system: duas verificações de interfaces do enactor e três de comandos de adaptação. Os resultados demonstram sensibilidade a essa alteração nas condições ensaiadas. A perda de um evento inicial continua sendo uma hipótese, pois não foi observada diretamente.

Na rodada sem B2, que corrige a chamada de ros::ok() na condição de repetição, o encerramento de reli_engine exigiu SIGTERM e SIGKILL. A execução de managing_system durou aproximadamente 54,5 segundos, ante 37,9 na referência inicial e 38,8 na final. Esses tempos incluem execução e encerramento, não medem latência de detecção. Houve também uma reprovação em test_collect_thermometer_data, por ausência da mensagem esperada. Como essa montagem não inicia o mecanismo alterado, a falha não foi atribuída a B2; sua causa permanece inconclusiva.

Nas variantes sem B3 e sem B5, o caso que espera ausência de adaptação acima do limiar passou, embora fosse uma falha esperada nas referências. A ausência de comandos coincidiu com problemas do mecanismo de adaptação. Essa mudança não comprova atendimento ao requisito; evidencia que o teste precisa verificar a atividade do mecanismo antes da janela sem comandos.

A retirada de B4, inicialização do contador cycles, manteve 154 aprovações e duas falhas esperadas. Portanto, a campanha atual não demonstrou sensibilidade a essa intervenção. Isso não invalida a correção: a manifestação de uma variável não inicializada depende das condições de execução.

A rodada sem B7 produziu quatro reprovações em test_transfer_with_accuracy_fail, nos sensores de ECG, temperatura e pressão arterial sistólica e diastólica. Os testes receberam dados do sensor, mas não observaram o estado fail esperado após a perturbação. Os mesmos casos aprovaram nas duas referências. Essa evidência amplia a detecção do defeito para testes de componentes com comunicação ROS; não equivale a verificar diretamente todos os rótulos de risco publicados.

A campanha teve uma execução por variante e duas da referência. As reversões foram independentes, ao contrário das combinações sucessivas do histórico. Assim, os novos registros fundamentam a análise atual de sensibilidade, sem reconstruir as antigas rodadas R1–R6 nem atribuir seus resultados à suíte atual.


Integridade: 4.068 arquivos conferidos por SHA-256. Das 478 entradas do inventário de fontes, 477 arquivos foram conferidos no arquivo de fontes. A entrada CMakeLists.txt é um link externo para o catkin do ROS Melodic; o destino não está disponível no ambiente Jazzy da auditoria. Não foi considerado um arquivo de produção perdido.

O arquivo de evidências conserva todos os itens da campanha, exceto a cópia de trabalho workspace. Essa cópia contém artefatos reconstruíveis; fontes congeladas, patches, parâmetros de construção, hashes dos binários e perfis coletados permanecem preservados. Os resultados antigos não foram sobrescritos.

Para conferir os arquivos originais, extraia `evidencias.tar.gz`, entre no diretório extraído e execute `sha256sum -c SHA256SUMS`. O resumo independente está em `auditoria.json`; `manifest.json` é o manifesto original.
