# Classificação de risco na suíte regular ROS 1

Quatro casos foram incorporados a `libbsn/test/unit/configuration/ConfigurationTest.cpp`, no grupo `RiskClassificationTest`. O arquivo já participa de `CATKIN_ADD_GTEST(run_test ...)`; não foi necessário alterar o CMake ou a implementação de produção.

Os casos retomam os vetores do ensaio complementar de 26/09: riscos 15, 45 e 90, esperados nas categorias baixa, média e alta, e uma leitura de 45 °C com risco esperado de aproximadamente 81,11 e categoria alta. Cada caso exige a categoria correta e rejeita as demais. A interpolação esperada é independente da função de produção. A configuração do termômetro é explícita.

## Validação local

| Variante | Casos executados | Aprovados | Reprovados |
|---|---:|---:|---:|
| Classe atual, testes de configuração existentes e novos | 15 | 15 | 0 |
| Cópia com B7, somente os quatro novos casos | 4 | 0 | 4 |

A mutação troca apenas as três consultas aos intervalos percentuais por consultas aos intervalos fisiológicos. Os testes e as opções de compilação são iguais. As reprovações são asserções de categoria, não erros de compilação. O valor numérico calculado no quarto caso continua correto na cópia defeituosa.

O ensaio foi executado diretamente com GCC e gtest, sem ROS e sem catkin. O gtest deste contêiner exige C++14; a tentativa inicial com C++11 não compilou e foi preservada nos arquivos `tentativa_cpp11_*`. A validação concluída usa C++14 nas duas variantes. O projeto ROS 1 continua configurado com C++11 e deve ser confirmado no ambiente Melodic do usuário. Não foi alterado o compilador da campanha de cobertura.

`validar.py` reproduz a compilação a partir das fontes preservadas. Os comandos, XML, logs, diff da mutação, versões e hashes acompanham o resultado. Binários temporários são removidos após a execução e podem ser regenerados. Os resultados não atualizam os totais históricos nem demonstram publicação de uma categoria pela cadeia ROS ou cobertura de todos os sensores e limites.

## Execução no ambiente ROS 1

Na raiz do workspace `bsn2`, após carregar Melodic e `devel/setup.bash`:

```sh
catkin_make run_tests_libbsn_gtest_run_test
catkin_test_results build/test_results/libbsn
```

O primeiro comando recompila o alvo quando necessário e executa os testes gtest da biblioteca. O novo grupo também integra a próxima execução geral da suíte.
