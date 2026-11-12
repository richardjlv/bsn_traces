# Recuperação da adaptação ROS 2 — 11–12/11/2026

> **Correções descartadas em 12/11/2026.** Por decisão do autor, o commit experimental `fc7c959` foi retirado da branch do fork ROS 2, que retornou a `3153596`. Os resultados de aprovação abaixo pertencem ao código modificado durante o diagnóstico e **não representam a versão mantida**. A falha de recuperação permanece registrada como possível regressão, sem correção de produção adotada. Os arquivos são preservados para rastreabilidade da investigação.

A investigação reproduziu e corrigiu quatro problemas: estados `running` no denominador da confiabilidade; separadores incompatíveis entre planejador e controlador; marca de desativação mantida após reativação; e desempate de prioridades dependente da ordem de inserção. Os testes dirigidos falharam antes dos respectivos ajustes e aprovaram depois. A seleção final de componentes aprovou 68 casos.

Na montagem BDD, a prontidão deixou de exigir comando espontâneo e passou a aguardar conexão e inicialização do enactor. A frequência de planejamento do lançamento de teste foi alinhada ao ROS 1 (0,2 Hz); o padrão de produção continua 0,02 Hz. O cenário continua exigindo comando inferior ao pico e encaminhamento do registro.

## Resultados

- `ros2_20261112T002519Z_yngm5q5r`: recuperação isolada com XPASS, ainda sob a marcação antiga; pico de 2,58 Hz e comando posterior de 2,43 Hz.
- `ros2_20261112T002723Z__jwyuwdd`: feature completa, 11 casos, 10 PASS e 1 XPASS (ausência de comandos). Recuperação aprovada como PASS; nenhum FAIL. Trace com 11 cenários e 30 passos, sem casos sem trace. Cobertura: 2.388/3.149 linhas e 537/888 ramos, neste recorte e versão.

O XML JUnit não distingue XPASS de PASS; `audit.json` usa `wasxfail` dos eventos internos, incluindo a razão vazia, para conservar essa distinção. A cobertura da feature não substitui a cobertura da suíte geral.

## Artefatos

Cada arquivo `.tar.gz` preserva a campanha identificada no nome, incluindo fontes, diferenças locais, logs, XML, eventos e, quando habilitada, cobertura. `audit.json` registra os hashes dos arquivos compactados e os resultados internos por caso. Os arquivos foram conferidos contra suas origens antes da publicação. `componentes/` reúne testes dirigidos, fontes e resultados antes/depois; seu README detalha as tentativas intermediárias.

A aprovação observa comandos e encaminhamento de registro. Não comprova retorno à frequência inicial, recuperação medida da confiabilidade ou frequência efetivamente executada. As tentativas intermediárias foram preservadas; a aprovação final não lhes é atribuída retroativamente.

A repetição isolada `ros2_20261112T003515Z_o4rn9tou`, com trace e cobertura, confirmou o caso de ausência de comandos como PASS, sem marcação de falha esperada. Essa repetição é complementar à feature completa e não foi somada como um novo caso distinto.
