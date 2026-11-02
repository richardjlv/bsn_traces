# Revalidação de três features ROS 2 — 02/11/2026 (UTC)

As features foram executadas separadamente, com inicialização própria, trace e cobertura. A seleção das reexecuções aprovadas reúne dez PASS e um XFAIL em onze casos internos; não é uma nova execução da suíte completa.

| Feature | Campanha | Resultado | Linhas | Ramos |
|---|---|---|---|---|
| check_bsn | ros2_20261102T010219Z_ftsgif7l | 8 PASS | 2079/3147 | 448/888 |
| data_persistance | ros2_20261102T010219Z_ftsgif7l | 1 PASS, 1 XFAIL | 2117/3147 | 411/888 |
| knowledge_repo | ros2_20261102T164547Z_jjbmzcaa | 1 PASS | 2083/3147 | 385/888 |

Os subdiretórios com os nomes das campanhas permitem consultar diretamente trace.jsonl, XML internos e relatórios de cobertura por feature. Os arquivos tar.gz preservam as campanhas completas, incluindo fontes, configuração, logs e estado Git. auditoria.json registra as contagens internas e a conferência dos 389 hashes dos três manifestos. Os executores externos não entram nos totais. A cobertura inclui preparação e encerramento; seus percentuais não devem ser somados.

## Resultados anteriores e ajuste

A tentativa ros2_20261102T010038Z_6oaveyyg foi executada em um sandbox que impediu a abertura de sockets UDP (Operation not permitted). Nenhum cenário interno foi executado. Essa tentativa registra uma restrição do ambiente do agente, sem atribuí-la às falhas históricas de outubro.

Na campanha 010219Z, executada com rede DDS habilitada e domínio 88, todos os casos de check_bsn e o caso nominal de data_persistance aprovaram sem nova alteração de código nesta revalidação. Isso resolve a falta de uma aprovação posterior dos casos, mas não determina a causa das capturas vazias de 25/10. O código atual também inclui revisões anteriores dos auxiliares de captura; as campanhas não constituem um experimento com todas as demais condições congeladas.

knowledge_repo ainda reprovou na campanha 010219Z: a preparação encontrou data_access, mas uma consulta posterior por ros2 node info retornou Unable to find node '/data_access'. O teste foi ajustado para, no modo --direct-readiness, consultar publicadores e assinantes pelo mesmo observador persistente do grafo utilizado na preparação. A descoberta dos endpoints admite espera limitada a cinco segundos. Permanecem exigidos os mesmos tópicos e as mesmas direções de comunicação; não houve alteração do código de produção nem do cenário Gherkin.

A campanha 164547Z aprovou o caso com esse ajuste, registrado no fork ROS 2 pelo commit 3153596. A versão executada está preservada no snapshot e no diff da campanha, coletados antes do commit. Três verificações locais adicionais confirmaram rejeição de tópico incorreto, aceitação do tópico correto e aceitação de descoberta posterior dentro da espera. A aprovação integrada sustenta o ajuste nesta montagem, sem demonstrar ausência de intermitência em todos os ambientes.

O XFAIL remanescente em data_persistance corresponde à simulação de falha de armazenamento, uma limitação conhecida nas duas versões. O caso nominal observa registro no canal de persistência; sua aprovação não comprova recuperação de uma leitura fisiológica armazenada.

## Reprodução

A partir de /ros_ws, com ROS 2 Jazzy e install/setup.bash carregados:

```sh
python3 src/ferramentas_traces/coletar_ros2.py --features check_bsn knowledge_repo data_persistance --domain-id 88 --direct-readiness --timeout 1200
```

É necessário permitir a comunicação DDS local. Nenhuma campanha anterior foi sobrescrita. A campanha 010219Z permanece incompleta no manifesto original devido à falha de knowledge_repo; a aprovação posterior está em outro diretório.
