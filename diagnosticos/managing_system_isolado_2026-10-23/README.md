# Isolamento dos cenários de managing_system — 23/10/2026

## Implementação e alcance

O executor passou a criar uma pilha ROS nova para cada um dos cinco cenários de adaptação. Os seis casos de topologia compartilham uma montagem de inspeção separada. Os grupos são executados sequencialmente na ordem `topology,increases,recovers,deadline,silent,logging`, com encerramento da montagem anterior. O estado em memória do controlador e do repositório é inicializado em novos processos. A seleção foi conferida por coleta do pytest: os 11 casos aparecem exatamente uma vez nos seis grupos (`selecao_cenarios.json`).

Cada grupo produz seu próprio XML interno, evitando sobrescrita. O executor externo continua sendo um único item agregador; suas contagens não devem ser somadas às internas. A fixture dos cenários que observam o controlador aguarda um primeiro comando real para o oxímetro, por até 90 s, para separar seu período inicial de 60 ciclos do prazo de resposta do cenário. Essa observação comprova atividade, não estabilidade da confiabilidade. A configuração de produção e as asserções funcionais não foram alteradas por esta intervenção.

## Execuções preservadas

| Campanha | Montagem | Resultado interno |
|---|---|---|
| [122341Z](../../campanhas_traces/ros2_20261023T122341Z_7sj4kj7u/) | Somente temporal; primeira tentativa | Nenhum cenário executado: a fixture interna por CLI esgotou a preparação, apesar da prontidão externa por serviço |
| [122618Z](../../campanhas_traces/ros2_20261023T122618Z_mqbypydy/) | Somente temporal; prontidão direta também na fixture interna | 1 PASS; 1 cenário e 3 passos no trace |
| [122757Z](../../campanhas_traces/ros2_20261023T122757Z_s9czcx_k/) | Feature completa, seis montagens | 8 PASS, 2 XFAIL, 1 FAIL; 11 cenários e 28 passos no trace |
| [123635Z](../../campanhas_traces/ros2_20261023T123635Z_cmd7psup/) | Somente registro, após correção do publicador de teste | 1 PASS; 1 cenário e 3 passos no trace |

Todos os casos registrados nos XML das três execuções com cenários possuem eventos correspondentes no trace (`missing_case_traces` vazio). A tentativa de preparação tem zero casos: seu arquivo XML vazio não representa aprovação. Os resultados desta primeira etapa não são somados como se pertencessem a uma única execução. A continuação está documentada abaixo.

O cenário temporal passou sozinho e depois do ensaio de recuperação no executor completo, com uma nova pilha. Isso sustenta a remoção da interferência observada nessas execuções; não prova ausência de dependências em toda condição. A recuperação continuou como XFAIL no `Then`, por ausência de comando inferior ao pico medido de 6,380 Hz. A expectativa de silêncio também continuou como XFAIL no `Then`, pela presença de comandos. Os traces identificam essas asserções, distinguindo as falhas esperadas de problemas de preparação.

A falha inesperada da execução completa ocorreu no `When` do registro: `ros2 topic pub --once` excedeu seu limite operacional de 5 s ao publicar o comando sintético. Essa falha não demonstra perda de persistência. A chamada foi substituída por um publicador no participante rclpy já existente, aguardando um assinante e mantendo cinco publicações do mesmo conteúdo (`source=/enactor`, `target=/g3t1_1`, `action=freq=5.0`). A espera de 10 s e a asserção sobre o registro real em `/persist` foram preservadas. A reexecução individual aprovou. O resultado verifica o encaminhamento do registro; não acrescenta uma consulta a armazenamento durável.

## Cobertura

| Execução | Linhas cobertas/total | Ramos cobertos/total |
|---|---:|---:|
| Temporal isolado | 2.331/3.147 | 499/888 |
| Feature completa com montagens independentes | 2.352/3.147 | 519/888 |
| Registro isolado corrigido | 2.166/3.147 | 430/888 |

A cobertura inclui preparação, execução e encerramento. Na feature completa, ela é a união das seis montagens e inclui a tentativa reprovada. Os percentuais combinados emitidos por coverage.py não devem ser rotulados como cobertura apenas de linhas. As coberturas dos três relatórios não são somadas nem substituem a campanha geral de 01/10. A execução de preparação também pode cobrir fontes, mesmo sem executar um cenário.

## Limitações e continuidade

O oráculo temporal ainda aceita qualquer comando após iniciar a publicação dos estados `fail`. Não observa diretamente o cruzamento de um limiar nem estabelece causalidade entre estímulo e resposta. A fixture de prontidão não resolve essa limitação. O estímulo repetido de status ainda usa CLI, enquanto a correção do publicador persistente se aplica apenas ao cenário de registro.

O próximo refinamento é observar a confiabilidade e os comandos correlacionados ao estímulo, com relógio monotônico e condições iniciais verificáveis. A repetição em ordens adicionais pode ampliar a avaliação. As campanhas históricas e a primeira mitigação por reordenação permanecem preservadas.

## Reprodução

```sh
# Cenário temporal isolado
BSN_MANAGING_GROUPS=deadline python3 src/ferramentas_traces/coletar_ros2.py --features managing_system --direct-readiness --timeout 300
# Todos os cenários, com montagens independentes
python3 src/ferramentas_traces/coletar_ros2.py --features managing_system --direct-readiness --timeout 1200
# Cenário de registro isolado
BSN_MANAGING_GROUPS=logging python3 src/ferramentas_traces/coletar_ros2.py --features managing_system --direct-readiness --timeout 300
```

Os comandos foram executados a partir de `/ros_ws`, com ROS Jazzy e o workspace carregados. Cada campanha contém fontes, diferenças locais, dependências, hashes, XML, logs, trace e cobertura próprios. O primeiro manifesto não inclui a opção de grupos (acrescentada ao coletor em seguida); sua seleção `deadline` está registrada neste relatório e no comando pytest interno do log. As fontes arquivadas são a referência exata de cada execução; pequenas revisões posteriores de comentários não alteram esses snapshots.

## Continuação: preparação e consultas ao grafo

Na campanha `ros2_20261023T183646Z_if2mkg0o`, uma nova execução completa registrou oito falhas e dois XFAIL internos, com dez cenários iniciados. As consultas CLI de presença e interfaces excederam seus limites; o cenário de registro não chegou a produzir um resultado interno. Os dois XFAIL ocorreram na preparação, não nas asserções funcionais conhecidas. Portanto, não constituem evidência sobre recuperação ou silêncio do controlador.

A exclusão dos processos CLI `ros2` do bootstrap de cobertura foi verificada por quatro testes de subprocesso, mantendo instrumentação nos nós e no pytest e preservando o hook anterior. Ela não resolveu sozinha o problema: `ros2_20261023T184437Z_94kgk9tk` registrou quatro aprovações e duas falhas de presença na topologia. A consulta de presença por um participante rclpy persistente eliminou essa dependência do CLI, mas `ros2_20261023T184726Z_jbr2le1b` ainda apresentou quatro falhas em `ros2 node info`, incluindo uma após imprimir suas interfaces.

A consulta das interfaces também passou a utilizar a API do grafo no modo `--direct-readiness`. As asserções continuam exigindo os mesmos publicadores e assinantes. A campanha `ros2_20261023T185048Z_syeo2uvm` aprovou os seis casos de topologia. As duas marcações XFAIL foram restringidas a `BehaviorExpectationNotMet`, emitida apenas pelas respectivas asserções de comportamento: erros de preparação devem reprovar normalmente. Essas intervenções alteram a instrumentação e a classificação do resultado, sem alterar a política do controlador ou seus limites.

Os manifests registram a exclusão do CLI da cobertura. Não foi isolado experimentalmente quanto do atraso das chamadas decorre da instrumentação, da descoberta DDS ou do encerramento dos processos; o timeout de CLI não deve ser apresentado como um defeito funcional confirmado do sistema.

A execução completa `ros2_20261023T185135Z_6mweno8n` registrou oito aprovações e uma falha interna em nove cenários iniciados. Recuperação e silêncio não chegaram ao pytest interno: a consulta externa ainda usava `ros2 node list` e falhou na preparação. O registro falhou na chamada CLI de `/EffectorRegister`, anterior ao estímulo. A correção seguinte estendeu a consulta direta ao grafo externo e substituiu essa chamada CLI por um cliente do mesmo serviço, conservando o pedido, a exigência de `ack` e o prazo de 10 s. Não foram contadas aprovações para os cenários ausentes.

## Estado da retomada em 24/10/2026

A campanha `ros2_20261023T185710Z_oitpv2vt` terminou pelo timeout global de 1.200 s: 2 PASS, 2 XFAIL e 6 FAIL internos, dez cenários iniciados, sem resultado do registro. Aumento e prazo aprovaram; recuperação e silêncio tiveram falhas esperadas. Os seis casos de topologia falharam na observação das interfaces. A cobertura parcial registrou 2.369/3.147 linhas e 528/888 ramos; o encerramento forçado impede presumir completude dos perfis. O arquivo integral foi preservado compactado para economizar espaço.

A consulta direta foi complementada com espera limitada de cinco segundos pelos tópicos exigidos, distinguindo presença do nó e descoberta de suas interfaces. Três verificações isoladas do auxiliar confirmaram aprovação imediata, aprovação após descoberta e reprovação por ausência. Essa alteração ainda não foi validada com ROS. A nova coleta está pendente porque o volume dispõe de menos de 100 MiB, limite mínimo do coletor. Não se conclui aprovação integral da feature ou resolução dos dois comportamentos marcados XFAIL.
