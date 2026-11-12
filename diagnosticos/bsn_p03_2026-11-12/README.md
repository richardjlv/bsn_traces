# Revisão da asserção temporal BSN-P03 — 12/11/2026

Apenas testes e documentação foram alterados. ROS 1 passou a calcular saída menos entrada, aceitando de 0 a 250.000 µs inclusive. ROS 2 aceita de 0 a 0,25 s e exclui saídas com carimbo anterior à injeção, inclusive na seleção da tentativa nominal.

Os 22 casos de verificação das funções reais de asserção aprovaram, incluindo zero, exatamente 250 ms, atraso de 400 ms, intervalos negativos, valores diferentes e saída antiga seguida de saída válida. As funções foram extraídas por AST para executar sem importar ROS; isso não valida o ambiente ROS 1.

A campanha ROS 2 `ros2_20261112T140223Z_vx4cp8l5` registrou dois casos internos aprovados, sem skip, XFAIL ou falha inesperada. A coleta preservou fontes, trace e XML; não coletou cobertura. O hash do arquivo de passos foi conferido contra o manifesto. A tentativa anterior `ros2_20261112T140052Z_zvljajya` não executou cenários: getifaddrs foi bloqueado pelo ambiente e os nós não alcançaram o estado ativo. Ambas as campanhas foram preservadas em src/campanhas_traces.

A execução ROS 1/Melodic continua pendente. A associação por valor repetido, a comparação entre relógios distintos, a seleção da última tentativa ROS 2 e as diferenças de estímulo e de fronteira continuam limitando a interpretação. Não foi demonstrada equivalência temporal ponta a ponta.

Para rodar no diretório do workspace ROS 1 já preparado:

```sh
python3 ../ferramentas_traces/coletar_ros1.py --workspace "$PWD" bsn_p03
```

A nova execução deve usar o asserts.py revisado. Os resultados históricos não foram reclassificados.

## Execução ROS 1 recebida e revisão da captura

A campanha `ros1_20261112T140638Z_bsn_p03_zefkd5g0` executou os dois cenários e ambos reprovaram no Then. O hash de asserts.py coincide com a revisão do intervalo. Os logs preservados no XML contêm dez pares nominais com diferenças entre −1.000.242 e −330.196 µs e nove pares sob carga entre −50.091 e −9.051 µs. Todos são negativos. As colunas %time e header.stamp contêm valores negativos e decrescentes da ordem de −1,794 × 10^18 ns; a captura usa rostopic echo -p --offset. Esses valores não permitem interpretar a diferença como latência positiva de propagação.

A revisão apenas do sinal da subtração e do intervalo aceito foi insuficiente para validar a medição ROS 1. Não se atribui essa reprovação a atraso real ou regressão de produção. O snapshot e os resultados dessa tentativa foram preservados.

A nova captura exclusiva de BSN-P03 usa assinantes rospy para os dois tópicos e registra os recebimentos no mesmo relógio CLOCK_MONOTONIC. Não usa os carimbos do cabeçalho nem modifica o parser compartilhado com outras features. A observação é de recebimento no teste; escalonamento dos callbacks e associação por valores repetidos continuam limitando a inferência causal. A antiga verificação adicional de atividade do coletor, executada pelo auxiliar geral de captura, não integra a captura temporal exclusiva. A descrição de alto risco no cenário ainda requer cuidado: a associação temporal, isoladamente, não verifica a categoria de emergência.

Os 26 testes locais aprovaram, incluindo os 22 de asserção e quatro de captura/relógio. O novo XML está em assercoes_captura.xml. Ainda é necessária nova execução Melodic com test_BSN-P03.py e temporal_capture.py atualizados, usando o mesmo comando de coleta. O resultado ROS 2 de dois casos aprovados permanece inalterado.

## Reexecução ROS 1 com captura monotônica

A campanha `ros1_20261112T141511Z_bsn_p03_hvv_1_rq` registrou dois casos internos aprovados, sem skip, XFAIL ou falhas. O executor externo também aprovou, sem ser somado aos casos internos. Os hashes de asserts.py, temporal_capture.py e test_BSN-P03.py coincidem com os arquivos revisados. Assim, a pendência de execução da captura revisada foi atendida para esta campanha.

No caso nominal, foram avaliados intervalos de 349,444 ms e 15,115 ms, com aprovação no segundo. Sob carga, o primeiro intervalo avaliado foi de 2,224 ms e aprovou. A função retorna ao encontrar o primeiro par de valores correspondentes dentro do prazo; esses resultados não demonstram que todos os pares atendem a 250 ms. O par nominal acima do prazo permanece registrado. A associação por valor não garante identidade causal do evento, nem a classificação de emergência.

As duas versões agora têm dois cenários aprovados nas campanhas identificadas, com o mesmo intervalo numérico aceito. As fronteiras, os estímulos e a política de seleção das observações continuam diferentes. Nenhum código de produção foi alterado para obter esses resultados. O XML recebido foi copiado para ros1_bdd_revalidado.xml e os intervalos avaliados constam de ros1_revalidacao.json. A campanha original, com traces e cobertura, foi preservada integralmente no diretório de coleta.

## Publicação

As quatro campanhas integrais estão nos arquivos .tar.gz deste diretório. Os nomes conservam os identificadores das campanhas. ROS 1 inclui trace e cobertura; as duas tentativas ROS 2 desta revisão foram executadas sem cobertura. Esses dados não substituem as campanhas gerais nem as coletas anteriores por feature.

Fontes de teste publicadas nos forks de Richard Viana:

- ROS 1, bsn_, branch pytest-bdd: commit 808c139b.
- ROS 2, bsn2, branch campanhas/traces-features-2026-10-21: commit 9085a17.

As fontes copiadas dentro das campanhas identificam o estado executado antes dos commits. Os hashes foram confrontados com os arquivos revisados. Nenhuma alteração de produção integra esses commits. O teste test_temporal_assertions.py foi copiado para rastreabilidade; sua execução regular utiliza os caminhos dos dois projetos no workspace original.
