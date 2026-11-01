# Separação entre emissão e registro — 01/11/2026

As duas campanhas executaram a feature managing_system isoladamente, com trace e cobertura. Os XML internos confirmam 12 casos por versão: ROS 1 com 11 PASS e um XFAIL; ROS 2 com dez PASS e dois XFAIL. Emissão do comando de aumento e registro no canal de persistência aprovaram separadamente em ambas. Executores externos e previous_test_results não entram nesses totais.

No ROS 1, a falha esperada é ausência de comandos acima do limiar. No ROS 2, também permanece a falha esperada de redução após recuperação enunciada. Não ocorreram falhas inesperadas. Os arquivos ros1.tar.gz e ros2.tar.gz preservam as campanhas completas; auditoria.json relaciona os resultados internos. Os resultados não demonstram armazenamento durável nem identidade causal única entre comando e registro.

## Recuperação: avaliação do próximo ajuste

Os passos atuais aceitam um pico apenas existente, interrompem a injeção de falhas no Given e usam uma espera fixa no When. Não observam o cruzamento da confiabilidade pelo limiar. Os ensaios controlados de 27/10 demonstraram comandos de redução nas duas versões com confiabilidade fornecida por serviços substitutos; não validam a recuperação da malha real.

Para manter o contrato de recuperação, a preparação deve comprovar frequência comandada inicial e aumento em relação a ela; a injeção deve terminar no When, marcando o início da observação. O oráculo deve observar a estimativa efetivamente usada pelo controlador, confirmar sua passagem pelo limiar e procurar o comando posterior. Medir a frequência efetiva do sensor é uma verificação adicional. Não basta elevar o timeout ou substituir recuperação por uma espera.

Uma consulta adicional ao DataAccess não deve ser presumida equivalente à observação consumida pelo controlador: o serviço ROS 1 chama applyTimeWindow ao responder. A forma de instrumentar essa observação precisa ser definida e validada nas duas versões antes de alterar o contrato executável. Nenhuma modificação do cenário de recuperação foi aplicada nesta revisão.
