# Cobertura geral das duas implementações

Aqui, ROS 1 corresponde ao projeto `bsn2` (legado), e ROS 2 ao projeto `bsn_ros2` (migrado).

| Implementação | Campanha | Linhas no recorte de produção | Ramos |
|---|---|---|---|
| ROS 1 | run_20260928T015653Z_iY2pcY | 3.429/4.263 (80,44%) | Não apresentado nessa métrica |
| ROS 2, união das fases | run_20261001T210002Z_6u7cg27x | 2.724/3.147 (86,56%) | 674/888 (75,90%) |

Cada pasta contém a campanha integral em `.tar.gz`, um inventário com SHA-256 de cada arquivo e do arquivo compactado, e cópias de relatórios para consulta direta. Todos os arquivos regulares do arquivo compactado foram conferidos por hash contra a origem local antes da publicação. Os arquivos conservam caminhos históricos e resultados antigos explicitamente arquivados pela própria campanha; esses resultados não devem ser somados à execução corrente.

No ROS 1, consulte `ros1/relatorios/report_production.log`. O arquivo compactado inclui perfis LLVM, relatórios HTML, resultados de testes e diagnósticos disponíveis. No ROS 2, consulte `ros2/relatorios/combined/coverage_production.xml` e os relatórios das fases `packages` e `bdd`. O manifesto original e sua revalidação foram preservados.

Estas campanhas gerais são distintas das campanhas de 22/10 em `campanhas_traces`, que executaram cada feature separadamente, com inicialização e encerramento próprios. As aprovações posteriores sem cobertura não substituem as medições anteriores. A cobertura por feature inclui também a montagem e a finalização dos processos; não mede exclusivamente as asserções de cada cenário.

Não houve reexecução dos testes nesta publicação. A preservação integral dos arquivos disponíveis não garante que todos os processos tenham gravado seus perfis durante a campanha original.
