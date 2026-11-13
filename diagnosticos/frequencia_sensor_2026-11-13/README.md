# Observação da frequência efetiva — 13/11/2026

Foram alterados somente testes, especificações Gherkin e documentação. Os cenários existentes de aumento e redução conservam a verificação dos comandos e passam a observar mensagens SensorData do sensor. As contagens históricas não foram reclassificadas.

## Critério operacional

As duas versões usam o mesmo módulo sampling_rate_oracle.py. Após a primeira mensagem de descoberta (espera máxima de 10 s), coletam os recebimentos por seis segundos com relógio monotônico. Exigem pelo menos quatro mensagens. A estimativa é o inverso da mediana dos intervalos de recebimento; o teste exige aumento superior a 10% ou redução superior a 10% em relação à referência medida.

A margem de 10% limita a aceitação por pequenas oscilações de temporização. É uma escolha operacional deste ensaio, não uma especificação do controlador, nem uma estimativa completa de incerteza. Uma mudança menor pode ser real e ainda não satisfazer esse critério. A verificação observa direção e magnitude mínima da mudança; não exige igualdade com um comando específico quando o controlador continua emitindo comandos. Os timestamps e a estimativa são registrados no stdout preservado pelo XML/trace.

No aumento, o Given adicional mede a referência antes da perturbação. Os Then/And verificam comando, registro e aumento da taxa observada. A injeção de falhas permanece ativa durante a observação do efeito e é encerrada ao final, inclusive se o teste falhar. Essa mudança na duração do estímulo impede tratar a nova execução como reprodução idêntica da campanha anterior.

Na recuperação, o Given mede a referência, aplica a perturbação e exige aumento efetivo antes de interrompê-la. O Then continua exigindo comando de redução; o novo And compara a taxa posterior com a taxa elevada observada. A marcação ROS 2 de falha esperada por ausência de comando não captura as novas AssertionError de medição: falhas da taxa devem aparecer como reprovações, e não como aprovações ou XFAIL genéricos.

A observação no assinante inclui efeitos de transporte e escalonamento. Não mede diretamente o instante de aquisição interna nem consumo de energia. Ausência ou insuficiência de mensagens é reportada separadamente de taxa inalterada.

## Verificação local

Os 31 casos de verificação do oráculo aprovaram, incluindo taxa constante, pequena oscilação, direção incorreta, mudança válida e dados insuficientes ou inválidos, além da limpeza das assinaturas e da janela de captura. Foi conferida a igualdade dos módulos nas duas versões. A execução ROS 1/Melodic deve ser realizada pelo autor:

```sh
python3 ../ferramentas_traces/coletar_ros1.py --workspace "$PWD" managing_system
```

A campanha ROS 2 iniciada com o novo contrato é ros2_20261113T151553Z_hdh5xtc4. Os resultados dos XML internos estão descritos abaixo.

## Evidência integrada ROS 2

O cenário de aumento aprovou os passos de comando e registro e reprovou no novo And da taxa: referência de 1,000944 Hz e observação posterior de 1,001366 Hz, com seis mensagens em cada janela. Os logs do sensor registram recebimento de comandos, incluindo 1,39 Hz, 1,80 Hz e 2,16 Hz. A taxa observada permaneceu próxima de 1 Hz.

Na preparação do cenário de recuperação, a verificação de elevação efetiva também reprovou. A nova condição não foi satisfeita, portanto essa execução não chegou a avaliar a redução. Os dois resultados são FAIL, não XFAIL. Os XML individuais e as observações extraídas das falhas estão neste diretório. Essa execução confirma a discrepância entre comando e efeito observado no sensor ROS 2; não identifica por si só toda a cadeia causal nem substitui a comparação com o ROS 1 sob o novo contrato.

A campanha terminou sem timeout, com 11 casos internos: oito PASS, dois FAIL e um XFAIL. As duas reprovações correspondem às novas verificações de taxa descritas acima; o XFAIL é o caso de ausência de comandos acima do limiar. O coletor sinalizou complete=False por haver reprovações, não por ausência de execução dos cenários.

## Evidência integrada ROS 1

A campanha `ros1_20261113T152349Z_managing_system_ikak33db` terminou com sete PASS, três FAIL e um XPASS. O JUnit apresenta oito casos sem falha porque não distingue o XPASS; o resumo pytest identifica essa condição no cenário de ausência de comandos.

O aumento reprovou por não observar comando acima de 1 Hz; o prazo local também reprovou por ausência de comando. A preparação da recuperação mediu 0,999269 Hz antes e 1,000277 Hz após a perturbação e reprovou por ausência de elevação. Portanto, esta campanha não demonstra que um comando válido recebido pelo sensor ROS 1 deixou de ser aplicado.

Todos os hashes de objetos registrados coincidem com os da campanha de 11/11. A cobertura de `Controller::receiveEvent` registra sete chamadas, todas no ramo de desativação, e zero no ramo de ativação. A campanha anterior registra sete ativações e sete desativações. O logger registrou 14 chamadas de tratamento de eventos na nova rodada. A falta de ativação do controlador é compatível com perda dos eventos durante a inicialização; o mecanismo exato dessa perda não foi demonstrado pelos logs. O erro de alvo indisponível do param_adapter aparece no último cenário, que provoca essa condição deliberadamente, e não explica as falhas anteriores.

O XPASS de ausência de comandos não comprova funcionamento: a inatividade observada também satisfaz essa asserção. Os resultados foram preservados sem modificar produção ou relaxar os critérios. Uma nova execução em diretório próprio permitirá verificar a recorrência da falha de inicialização. O diagnóstico estruturado conserva os contadores de cobertura usados na comparação.

## Repetição ROS 1 — 20h32 UTC

A campanha `ros1_20261113T203242Z_managing_system_luwyxrn5` registrou oito PASS, dois FAIL e um XFAIL. A cobertura registra sete ativações e sete desativações no controlador. O cenário de aumento passou pelos passos de comando e registro, mas a observação posterior não reuniu mensagens após a descoberta, na janela de seis segundos. O log do oxímetro registra intervalos de 9,178 e 9,175 segundos entre saídas próximas dessa etapa. A ausência de amostras nessa janela não permite calcular a taxa nem equivale a comprovar permanência em 1 Hz.

O cenário seguinte iniciou a medição com 38,821 Hz e observou 39,249 Hz após a perturbação, reprovando o aumento mínimo de 10%. A montagem compartilhada conserva estado entre cenários; essa referência já elevada torna inadequado exigir nova elevação relativa próxima do limite de comando de 40 Hz. O teste não chegou à verificação da redução. É necessário isolar a preparação dos cenários antes de repetir a avaliação de recuperação. A evidência de taxa elevada não substitui uma comparação controlada antes/depois, mas impede caracterizar o sensor ROS 1 como invariavelmente fixo em 1 Hz. Nenhum código de produção foi alterado.

## Sensor ROS 1 com comandos fixos

A campanha `frequencia_sensor_ros1_20261113T215252Z_aKcsuC` completou as quatro fases e aprovou o critério definido previamente. As taxas pela mediana foram 0,997708 Hz na referência de 1 Hz, 1,995944 Hz após comando de 2 Hz, 4,967240 Hz após comando de 5 Hz e 0,998872 Hz após retorno a 1 Hz. As janelas receberam respectivamente 9, 20, 49 e 10 mensagens; as frequências por contagem também satisfizeram a tolerância de 20%. A fração de intervalos compatíveis foi 100%, 100%, 97,92% e 100%, acima do mínimo de 80%. Os resultados foram recalculados a partir dos timestamps preservados.

Este ensaio confirma a aplicação dos comandos pelo sensor real ROS 1 nessa montagem isolada, sem controlador concorrente. Não demonstra a recuperação da malha completa nem resolve retroativamente as falhas do BDD. A tentativa anterior `frequencia_sensor_ros1_20261113T215142Z_DwSL_8` não iniciou as medições por ausência das mensagens geradas no ambiente Python; permanece preservada.
