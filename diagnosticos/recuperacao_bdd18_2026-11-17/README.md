# Recuperação BDD18 — execução isolada ROS 1

Campanha: ros1_20261117T023745Z_managing_system_uwlb_41r. Um cenário executado, FAIL na preparação. Nenhuma redução foi avaliada.

A nova medição em três janelas registrou taxas próximas de 1 Hz antes e depois da perturbação, sem aumento consistente. Esta rodada não herdou a taxa de 39 Hz do cenário anterior.

A cobertura registra sete chamadas de Controller::receiveEvent, zero execuções do ramo activate e sete do ramo deactivate. Logger::receiveAdaptationCommand, ParamAdapter::receiveAdaptationCommand e Sensor::reconfigure registram zero chamadas. Portanto, a rodada não fornece evidência de comando recebido e ignorado pelo sensor ROS 1; a ausência de ativação do controlador limita a preparação. O mecanismo exato da perda de ativação não foi observado diretamente.

A remoção do percentual mínimo não corrige a inicialização da montagem. É necessário garantir e observar a prontidão dos participantes antes dos eventos de ativação, sem fabricar uma aprovação nem modificar a produção. As tentativas anteriores, que não iniciaram cenários por problemas de resolução do lançamento temporário, permanecem preservadas.

## Execução 03h17 UTC

Campanha ros1_20261117T031727Z_managing_system_j9noi387. O cenário concluiu a preparação com aumento observado, a interrupção das falhas e a asserção de comando de redução. Reprovou apenas no And da taxa posterior. As taxas por contagem nas três janelas elevadas foram 38,7563, 38,4952 e 38,1510 Hz; após o comando, 38,1639, 37,8081 e 35,6474 Hz. Há redução observada ao longo das janelas posteriores, mas não separação completa: a primeira janela posterior supera ligeiramente a menor janela anterior. A redução passou no critério por mediana dos intervalos e falhou no critério adicional por contagem. O resultado permanece FAIL segundo o contrato executado. Não demonstra ausência de resposta do sensor; a leitura deve distinguir resposta observada de aprovação do oráculo de consistência. Nenhuma produção foi alterada.

## Execução aprovada

Na execução isolada ROS 1 de 17/11, BDD18 aprovou sob o contrato revisado: preparação em pilha nova, comparação das medianas de três janelas antes e durante a perturbação e após o comando de redução, pelos intervalos e pela contagem de mensagens, sem percentual mínimo fixo. Foram observados aumento da taxa e redução posterior à interrupção das falhas. Esse resultado não constitui nova execução integral de managing_system nem comprova recuperação da confiabilidade ou retorno exato à taxa inicial. A validação ROS 2 desse contrato permanece pendente; seus resultados de 13/11 continuam vinculados à versão então executada.

Campanha: ros1_20261117T032647Z_managing_system_3z1wo42a. Um cenário PASS; setup e teardown aprovados. XML e observações completos preservados neste diretório.
