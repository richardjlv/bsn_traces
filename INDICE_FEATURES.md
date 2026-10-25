# Índice de traces e cobertura por feature — ROS 2

Seleção explícita em `selecao_features.json`. Cada linha corresponde a uma execução isolada da feature, com inicialização e encerramento próprios. Managing_system utiliza montagens independentes por grupo. As linhas não formam uma execução única da suíte geral.

| Feature / campanha | Resultado interno | Linhas | Ramos | Evidências |
|---|---|---:|---:|---|
| [check_bsn](campanhas_traces/ros2_20261025T133430Z_5iul_jhu/manifest.json) | 7 PASS, 1 FAIL | 2064/3147 (65.59%) | 438/888 (49.32%) | [Trace](campanhas_traces/ros2_20261025T133430Z_5iul_jhu/check_bsn/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T133430Z_5iul_jhu/check_bsn/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T133430Z_5iul_jhu/check_bsn/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T133430Z_5iul_jhu/check_bsn/coverage_production.xml) |
| [knowledge_repo](campanhas_traces/ros2_20261025T133738Z_lq2j_aml/manifest.json) | 1 FAIL | 2088/3147 (66.35%) | 389/888 (43.81%) | [Trace](campanhas_traces/ros2_20261025T133738Z_lq2j_aml/knowledge_repo/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T133738Z_lq2j_aml/knowledge_repo/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T133738Z_lq2j_aml/knowledge_repo/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T133738Z_lq2j_aml/knowledge_repo/coverage_production.xml) |
| [target_system](campanhas_traces/ros2_20261025T133804Z_lza7ktd9/manifest.json) | 18 PASS | 2127/3147 (67.59%) | 424/888 (47.75%) | [Trace](campanhas_traces/ros2_20261025T133804Z_lza7ktd9/target_system/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T133804Z_lza7ktd9/target_system/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T133804Z_lza7ktd9/target_system/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T133804Z_lza7ktd9/target_system/coverage_production.xml) |
| [data_persistance](campanhas_traces/ros2_20261025T133856Z_g2_t0zqp/manifest.json) | 1 XFAIL, 1 FAIL | 2106/3147 (66.92%) | 403/888 (45.38%) | [Trace](campanhas_traces/ros2_20261025T133856Z_g2_t0zqp/data_persistance/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T133856Z_g2_t0zqp/data_persistance/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T133856Z_g2_t0zqp/data_persistance/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T133856Z_g2_t0zqp/data_persistance/coverage_production.xml) |
| [health_status](campanhas_traces/ros2_20261025T133922Z_qom_1chl/manifest.json) | 2 PASS | 1855/3147 (58.95%) | 353/888 (39.75%) | [Trace](campanhas_traces/ros2_20261025T133922Z_qom_1chl/health_status/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T133922Z_qom_1chl/health_status/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T133922Z_qom_1chl/health_status/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T133922Z_qom_1chl/health_status/coverage_production.xml) |
| [injector](campanhas_traces/ros2_20261025T134004Z_lsn_55i5/manifest.json) | 7 XFAIL | 2122/3147 (67.43%) | 415/888 (46.73%) | [Trace](campanhas_traces/ros2_20261025T134004Z_lsn_55i5/injector/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T134004Z_lsn_55i5/injector/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T134004Z_lsn_55i5/injector/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T134004Z_lsn_55i5/injector/coverage_production.xml) |
| [bsn_p03](campanhas_traces/ros2_20261025T134059Z_qq2jtc3r/manifest.json) | 2 PASS | 988/3147 (31.39%) | 172/888 (19.37%) | [Trace](campanhas_traces/ros2_20261025T134059Z_qq2jtc3r/bsn_p03/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T134059Z_qq2jtc3r/bsn_p03/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T134059Z_qq2jtc3r/bsn_p03/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T134059Z_qq2jtc3r/bsn_p03/coverage_production.xml) |
| [managing_system](campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/manifest.json) | 9 PASS, 2 XFAIL | 2357/3147 (74.90%) | 518/888 (58.33%) | [Trace](campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/managing_system/trace.jsonl) · [JUnit](campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/managing_system/internal_junit/) · [Cobertura](campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/managing_system/coverage_production.json) · [XML cobertura](campanhas_traces/ros2_20261025T054442Z_l7kfhjkk/managing_system/coverage_production.xml) |

## Interpretação

Os hashes, os totais JUnit, a presença dos casos nos traces e os totais de cobertura foram conferidos pelo gerador. Isso verifica consistência dos arquivos preservados; não demonstra completude dos perfis de processos encerrados nem força dos oráculos.

XFAIL representa expectativa não atendida. Consulte `step_errors` em `indice_features.json` para distinguir erro na preparação e falha na asserção. A cobertura inclui inicialização, preparação e encerramento, não apenas os passos ou asserções. Os percentuais não são somados e não substituem a [cobertura geral](cobertura_geral/README.md).

| Feature | Propriedades | Alcance e limitação |
|---|---|---|
| check_bsn | BSN-C01, BSN-P09 (recorte alto), BSN-C02 | Recepção e risco no recorte exercitado; não comprova todas as categorias ou preservação integral. |
| knowledge_repo | BSN-C06 | Conexões e canais anunciados; não comprova armazenamento durável. |
| target_system | BSN-C13–C15 | Interfaces e respostas do simulador nas faixas configuradas; topologia não comprova processamento nem aplicação dos comandos. |
| data_persistance | BSN-P08 (observação parcial), BSN-C03 | Encaminhamento em /persist; não equivale à recuperação do valor armazenado. |
| health_status | BSN-P10, BSN-C04 | Saídas e ausências na montagem ensaiada; conferir estímulo e força das asserções. |
| injector | BSN-C05 | Falhas esperadas associadas à funcionalidade ausente; não representam aprovação do injetor. |
| bsn_p03 | BSN-P03 (instrumentação limitada) | Prazo no trecho e oráculo implementados; limites de causalidade e comparabilidade permanecem. |
| managing_system | BSN-C07–C12 | Comandos e registros; recuperação e silêncio não atendidos, sem comprovação da frequência efetiva. |

## Histórico e reprodução

As tentativas anteriores continuam em `campanhas_traces/`, incluindo falhas e coletas interrompidas. A escolha da campanha desta tabela não altera seus resultados nem os agrega retrospectivamente.

Para conferir novamente: `python3 ferramentas_traces/gerar_indice_features.py --root .` na raiz deste repositório. O arquivo JSON preserva os nomes exatos das campanhas e casos.
