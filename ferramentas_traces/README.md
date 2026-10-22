# Coleta de traces BDD por feature

Esta instrumentação executa cada feature ROS 2 em um processo pytest próprio, com seus lançamentos, cobertura multiprocesso, resultados internos e eventos BDD. As saídas são criadas em pastas novas por campanha; não substituem as campanhas citadas na monografia nem o acervo v1.0.0.

```bash
source /opt/ros/jazzy/setup.bash
source /ros_ws/install/setup.bash
python3 /ros_ws/src/ferramentas_traces/coletar_ros2.py
```

Para selecionar uma feature:

```bash
python3 /ros_ws/src/ferramentas_traces/coletar_ros2.py --features knowledge_repo
```

Os nomes disponíveis correspondem aos arquivos `test_*_bdd.py`: `bsn_p03`, `check_bsn`, `data_persistance`, `health_status`, `injector`, `knowledge_repo`, `managing_system` e `target_system`. `--output-root`, `--domain-id` e `--timeout` permitem escolher destino, domínio DDS e limite de execução por feature. O domínio padrão é 87, com descoberta local. Usar um ambiente sem outros ensaios: alguns passos preexistentes encerram processos por nome.

Se este diretório vier do repositório documental, informar `--source-root /caminho/bsn_ros2` e carregar o workspace correspondente. `coverage_support.py` preserva os auxiliares do coletor original, com a raiz ajustada pelo executor; não deve ser executado diretamente. Não é preciso instalar as ferramentas dentro do projeto ROS 2.

`harness_traces.patch` registra a instrumentação adicional de prontidão, relativa à cópia do harness preservada no acervo v1.0.0. Para aplicar em um checkout compatível, usar `git -C /caminho/bsn_ros2 apply --check /caminho/ferramentas_traces/harness_traces.patch` e depois `git apply` com os mesmos caminhos. No workspace de desenvolvimento, as mudanças já estão aplicadas. Conferir diferenças antes de adaptar o patch a outra versão.

`--direct-readiness` consulta os serviços GetState com um executor ROS persistente: exige estado 3 (`active`) no prazo original, sem considerar um nó apenas anunciado como pronto. A opção foi verificada com um nó ativo e outro inativo. O modo padrão continua usando o CLI. `--without-coverage` permite uma campanha diagnóstica de traces sem instrumentação estrutural. `--hub-stack-after 40` registra uma pilha Python do concentrador após 40 s; esse registro auxiliar não é uma falha por si só.

## Conteúdo de cada campanha

- `manifest.json`: comandos, estado da execução, configurações, resultados e limites.
- `sources.tar.gz`, hashes, estado Git e diferenças locais: identificação do sistema exercitado.
- `bootstrap/`: cópia da instrumentação efetivamente utilizada.
- Uma pasta por feature, com `trace.jsonl`, XML internos, XML externo, log comprimido, logs ROS, perfis brutos e cobertura de produção.
- `sha256.json`: integridade dos arquivos produzidos ao término da campanha.

O trace contém início/fim de cenário, início/fim ou erro de passo, parâmetros textuais disponíveis e relatórios de setup/call/teardown do pytest. Cada evento inclui PID, identificador do caso, tempo de parede e relógio monotônico. O fim do cenário não indica aprovação: consultar os relatórios pytest e o XML interno para distinguir PASS, XFAIL, SKIP, falha e erro.

A cobertura abrange a execução inteira da feature, incluindo inicialização e encerramento dos nós; não atribui linhas a cada cenário. Os eventos BDD registram a execução da especificação; não capturam sistematicamente todas as mensagens ROS nem estabelecem correlação causal entre estímulo e resposta. Valores internos de fixtures não são serializados automaticamente. Logs e mensagens de asserção complementam o diagnóstico.

O runner recusa iniciar com menos de 100 MiB livres e interrompe a sequência antes da próxima feature se restarem menos de 40 MiB. Esses limites são verificações preventivas, não garantia de espaço suficiente. Falhas de inicialização permanecem no relatório e não são convertidas em aprovação. Processos mortos sem gravar seus perfis podem reduzir a cobertura coletada.

## Verificação e limites de ambiente

`python3 -m pytest -q -o addopts= ferramentas_traces/test_trace_plugin.py` verifica o registro de um cenário aprovado e de uma falha esperada, sem iniciar ROS. As execuções reais têm seus próprios manifestos e devem ser avaliadas separadamente.

O executor deste diretório é para ROS 2. ROS 1 não está instalado no ambiente atual; não há nova campanha ROS 1 nesta etapa. A instrumentação do legado precisa ser adaptada e validada no ambiente Melodic, inclusive quanto à versão Python/pytest-bdd e à separação dos perfis LLVM por feature. Não aplicar os percentuais Python às fontes C++.
