# Ensaios complementares para fechamento da monografia

Estes ensaios complementam as campanhas BDD; não substituem nem alteram seus resultados históricos. Cada execução cria um diretório novo com fontes, comandos, resultados e registros.

## Concentrador sob entradas controladas

`validar_hub_controlado.py` inicia somente o concentrador e um observador que publica seis mensagens sintéticas. Usa frequência nominal de 6 Hz e três repetições da sequência baixo–alto–retorno. Riscos de entrada: `[10,20,20,20,20,20]`, `[90,20,20,20,20,20]`, e o primeiro vetor novamente; estados esperados: 20, 90 e 20. As leituras são marcadores artificiais distintos para relacionar entrada e saída; não representam medições fisiológicas.

Cada fase dura 5 segundos. Após 2 segundos de acomodação operacional, exige pelo menos três saídas com os seis marcadores, os seis riscos e o estado esperado. Essas janelas pertencem ao protocolo, não são requisitos do SA-BSN. Não há retransmissão de entradas para descartar tentativas malsucedidas.

A latência é medida no mesmo observador, com relógio monotônico, desde o início da publicação do lote até a primeira saída correspondente. O indicador de 250 ms é informado separadamente da aprovação funcional. Essa fronteira não corresponde à cadeia completa paciente–sensor–detecção de emergência; três repetições não demonstram limite de pior caso.

### ROS 1 (executar em terminal Melodic)

A partir de `/ros_ws`, com o workspace ROS 1 já compilado:

```bash
source /opt/ros/melodic/setup.bash
source /ros_ws/src/bsn2/devel/setup.bash
python2 /ros_ws/src/ferramentas_traces/fechamento/validar_hub_controlado.py --ros 1 --output /ros_ws/src/campanhas_fechamento --repeticoes 3
```

Se a cópia compilada estiver em outro diretório, ajustar o caminho do `devel/setup.bash`. Não recompilar apenas para executar o ensaio. O script inicia um mestre ROS próprio em porta livre e observadores dos canais de diagnóstico exigidos pelo componente legado; não precisa iniciar a pilha completa. Preserva o hash do executável encontrado e cópias das fontes consultadas; isso não comprova sozinho que o binário foi compilado dessas fontes.

### ROS 2

```bash
source /opt/ros/jazzy/setup.bash
source /ros_ws/install/setup.bash
python3 /ros_ws/src/ferramentas_traces/fechamento/validar_hub_controlado.py --ros 2 --output /ros_ws/src/campanhas_fechamento --repeticoes 3
```

Reservar o domínio ROS 91 para esse ensaio. Não executar duas instâncias simultâneas. O registro discrimina falha de preparação de reprovação nas fases funcionais. O programa registra os endpoints do concentrador: a implementação cria publicadores na construção e na configuração; contagem de endpoints não equivale à contagem de produtores independentes.

## Ensaios de lógica isolada

- `comparar_fusao.py`: quatro vetores, fontes C++ e Python reais, expectativas fixadas e mutação que ignora o risco do termômetro. A cópia mutante deve divergir no vetor alto; não modifica produção. Resultado preservado em `fusao_20261027T001940Z_10dxlqab`: classes atuais concordantes com os quatro oráculos e mutação detectada.
- `comparar_controlador.py`: corpos reais dos métodos de controle com dependências substituídas. Resultado `controlador_20261027T002551Z_3hf84gh8`: diferenças na presença de comando com erro zero, na ação dentro da margem e na precisão do comando serializado (9.925000 versus 9.93). Isso caracteriza diferenças locais; não estabelece a causa integral da divergência de recuperação observada em BDD.

## Fechamento pendente

Confrontar a execução integrada ROS 1 com a ROS 2; avaliar persistência segundo a fronteira efetivamente implementada; separar resultados de método, integração e campanhas BDD; atualizar resultados/conclusão e publicar artefatos auditados. Não converter limitações observadas em alegação de preservação integral.

## Execução integrada ROS 2 disponível

`hub_ros2_20261027T003048Z_7311a_s5`: preparação concluída e nove fases funcionais aprovadas. Os JSON e traces preservam os tempos de cada fase. As três tentativas anteriores falharam na preparação (tipo do parâmetro de frequência, nome do componente e contagem de endpoints); não são reprovações dos vetores funcionais e foram preservadas. A execução ROS 1 correspondente permanece pendente.

## Correção da prontidão em 27/10/2026

A tentativa ROS 1 `hub_ros1_20261027T174028Z_6xbHl_` encontrou os pacotes e o executável, mas terminou sem executar fases (`phases: []`), com `Hub input connections/output not ready`. O protocolo aguardava uma saída espontânea antes da primeira entrada. Em `CentralHub::body`, o legado só processa e transfere quando `total_buffer_size > 0`; esse contador começa em zero. A preparação criava, portanto, uma dependência circular.

No ROS 1, o executor foi corrigido para aguardar as conexões dos seis canais de entrada e do canal de saída, sem exigir uma mensagem anterior ao estímulo. No ROS 2, conserva-se adicionalmente a primeira saída periódica como evidência de ativação: interfaces anunciadas ainda não garantem processamento. Uma tentativa intermediária, `hub_ros2_20261027T174424Z_ijb50zty`, que dispensou essa evidência, perdeu o primeiro lote e foi preservada. Essa tentativa motivou manter a preparação específica de cada implementação. As entradas, os oráculos, as janelas das fases e a contabilização temporal permanecem iguais. A primeira saída correspondente continua sendo exigida pelas verificações funcionais. A tentativa anterior foi preservada e não é classificada como regressão do concentrador. A mensagem de falha de registro no effector pertence à montagem sem adaptação; o método de inicialização registra o erro e prossegue.

## Adaptação: nó real com serviços controlados

`validar_adaptacao_controlada.py` inicia o enactor real. Dois serviços substitutos fornecem o parâmetro `reliability` e valores conhecidos de confiabilidade; eventos de ativação e estratégias são enviados por tópicos reais. O observador registra cada resposta do serviço e cada comando em `log_adapt`. O domínio ROS 2 reservado é 92; no ROS 1 o mestre é criado em porta livre.

A configuração usa frequência de execução 10 Hz, ganho 50, frequência inicial por alvo 10 Hz, referência 0,8 e margem 0,02 (valor fixo do construtor ROS 1). Quatro alvos distintos evitam reaproveitar o estado acumulado: confiabilidade 0,5, 0,95, 0,8 e 0,79. Cada caso recebe uma janela de respostas de quatro segundos, seguida de drenagem de meio segundo; esses tempos pertencem ao ensaio. Não representam requisito temporal. A preparação exige conexões e pelo menos uma consulta efetiva ao serviço.

O resultado `characterization_matches` significa concordância com a política inspecionada de cada implementação, não aprovação da migração. A regra comum proposta de não atuar dentro da margem não é aplicada retroativamente como especificação estabelecida. As divergências de presença, valor e arredondamento de comandos devem ser comparadas explicitamente. A ausência de comando só é interpretável junto à atividade do serviço e aos casos de controle positivo da mesma execução.

Este ensaio não utiliza o estimador real de confiabilidade, o planejador, o logger, o adaptador ou o sensor. Portanto, não demonstra recuperação da malha nem alteração da frequência efetiva do sensor. A causa da divergência sistêmica anterior não se reduz automaticamente às diferenças aqui caracterizadas.

No diretório `bsn2`, em terminal Melodic com workspace compilado:

```bash
source /opt/ros/melodic/setup.bash
source "$PWD/devel/setup.bash"
python2 ../ferramentas_traces/fechamento/validar_adaptacao_controlada.py --ros 1 --output src/campanhas_fechamento
```

No workspace ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
source /ros_ws/install/setup.bash
python3 src/ferramentas_traces/fechamento/validar_adaptacao_controlada.py --ros 2 --output src/campanhas_fechamento
```

### Precisão dos comandos

A sequência analítica é `10 + n × 0,5 × (0,8 − confiabilidade)`, com `n` igual ao número da resposta controlada. A comparação admite meia unidade da última casa serializada: 0,005 Hz no ROS 2 e 0,0000005 Hz no ROS 1, acrescidas de 1e-9 para ruído numérico. Essa tolerância caracteriza a serialização de cada implementação, não estabelece tolerância de equivalência entre as versões. Os comandos exatos permanecem registrados para comparação.

A primeira tentativa ROS 2 (`adaptacao_ros2_20261027T181738Z_r6hvnxd_`) terminou todos os casos, mas o comparador exigia identidade com o arredondamento da fórmula direta. Na redução, observou 9,63 contra 9,62 e 9,48 contra 9,47 nos empates decimais, devido à diferença entre acumular incrementos e calcular a fórmula direta. A execução foi preservada, e o comparador passou a confrontar a sequência analítica não arredondada com a resolução declarada. Não houve alteração do código de produção.

## Persistência operacional

O executor `validar_persistencia_controlada.py` envia 30 mensagens Status ao DataAccess real e compara os seis campos dos registros reabertos após encerrar o processo. O lote atinge o limiar de flush; não há teste de buffer parcial ou perda de energia. ROS 2 grava no diretório da campanha; ROS 1 usa os novos arquivos do diretório padrão do pacote e copia os logs Status para a campanha, sem remover os originais.

No diretório bsn2, após carregar Melodic e devel/setup.bash:

```bash
python2 ../ferramentas_traces/fechamento/validar_persistencia_controlada.py --ros 1 --output src/campanhas_fechamento
```

ROS 2 validado em `persistencia_ros2_20261027T184744Z_yjoqaqkq`: 30 registros recuperados, com campos e ordem conferidos. Isso não valida persistência de leituras fisiológicas nem consulta pela API.

Conferência pareada concluída: `persistencia_ros1_20261027T185045Z_xWH4g_` recuperou os mesmos 30 registros esperados, com o mesmo executor ROS 2. A origem exclusiva de campanha é normalizada apenas na comparação entre versões.
