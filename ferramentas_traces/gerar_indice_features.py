#!/usr/bin/env python3
"""Gera o índice de campanhas escolhidas explicitamente, sem somar percentuais."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

LIMITES = {
 'check_bsn': 'Recepção e risco no recorte exercitado; não comprova todas as categorias ou preservação integral.',
 'knowledge_repo': 'Conexões e canais anunciados; não comprova armazenamento durável.',
 'target_system': 'Interfaces e respostas do simulador nas faixas configuradas; topologia não comprova processamento nem aplicação dos comandos.',
 'data_persistance': 'Encaminhamento em /persist; não equivale à recuperação do valor armazenado.',
 'health_status': 'Saídas e ausências na montagem ensaiada; conferir estímulo e força das asserções.',
 'injector': 'Falhas esperadas associadas à funcionalidade ausente; não representam aprovação do injetor.',
 'bsn_p03': 'Prazo no trecho e oráculo implementados; limites de causalidade e comparabilidade permanecem.',
 'managing_system': 'Comandos e registros; recuperação e silêncio não atendidos, sem comprovação da frequência efetiva.',
}

PROPRIEDADES = {
 'check_bsn': 'BSN-C01, BSN-P09 (recorte alto), BSN-C02',
 'knowledge_repo': 'BSN-C06', 'target_system': 'BSN-C13–C15',
 'data_persistance': 'BSN-P08 (observação parcial), BSN-C03',
 'health_status': 'BSN-P10, BSN-C04', 'injector': 'BSN-C05',
 'bsn_p03': 'BSN-P03 (instrumentação limitada)',
 'managing_system': 'BSN-C07–C12',
}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,required=True)
 args=parser.parse_args();root=args.root.resolve()
 selection=json.loads((root/'selecao_features.json').read_text())
 rows=[]
 for feature,campaign in selection.items():
  folder=root/'campanhas_traces'/campaign
  hashes=json.loads((folder/'sha256.json').read_text())
  for rel,expected in hashes.items():
   actual=hashlib.sha256((folder/rel).read_bytes()).hexdigest()
   if actual!=expected:raise ValueError(f'Hash divergente: {campaign}/{rel}')
  manifest=json.loads((folder/'manifest.json').read_text())
  record=manifest['features'][feature]
  if record.get('state')!='finished':raise ValueError(f'Campanha não finalizada: {campaign}')
  counts=collections.Counter()
  for report in record['internal_junit']:counts.update(report['counts'])
  cases=[]
  for xml in sorted((folder/feature/'internal_junit').glob('*.xml')):
   for case in ET.parse(xml).iter('testcase'):
    skip=case.find('skipped')
    status=('failure' if case.find('failure') is not None else
            'error' if case.find('error') is not None else
            'xfail' if skip is not None and skip.get('type')=='pytest.xfail' else
            'skipped' if skip is not None else 'passed')
    cases.append(dict(name=case.get('name'),status=status))
  parsed=collections.Counter(c['status'] for c in cases)
  if parsed!=counts:raise ValueError(f'XML e manifesto divergem: {feature}: {parsed} != {counts}')
  events=[json.loads(line) for line in (folder/feature/'trace.jsonl').read_text().splitlines()]
  traced={e['nodeid'].split('::')[-1] for e in events if e.get('event')=='test_report' and e.get('nodeid','').startswith('steps/')}
  missing=sorted({c['name'] for c in cases}-traced)
  if missing or record.get('missing_case_traces'):raise ValueError(f'Trace ausente: {feature}: {missing}')
  coverage=json.loads((folder/feature/'coverage_production.json').read_text())['totals']
  if coverage!=record['coverage_totals']:raise ValueError(f'Cobertura diverge: {feature}')
  errors=[{k:e.get(k) for k in ('scenario','keyword','step','exception_type','message')} for e in events if e.get('event')=='step_error']
  rows.append(dict(feature=feature,campaign=campaign,counts=dict(counts),cases=cases,
                   collector_complete=record['complete'],exit_code=record['exit_code'],
                   scenario_starts=record['scenario_starts'],missing_case_traces=missing,
                   coverage=coverage,step_errors=errors,properties=PROPRIEDADES[feature],limitation=LIMITES[feature],
                   hashes_verified=len(hashes),coverage_enabled=manifest['coverage_enabled']))
 (root/'indice_features.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 lines=['# Índice de traces e cobertura por feature — ROS 2','',
 'Seleção explícita em `selecao_features.json`. Cada linha corresponde a uma execução isolada da feature, com inicialização e encerramento próprios. Managing_system utiliza montagens independentes por grupo. As linhas não formam uma execução única da suíte geral.', '',
 '| Feature / campanha | Resultado interno | Linhas | Ramos | Evidências |',
 '|---|---|---:|---:|---|']
 for row in rows:
  feature=row['feature'];base='campanhas_traces/'+row['campaign'];cov=row['coverage'];c=row['counts']
  result=', '.join(f'{c[k]} {label}' for k,label in [('passed','PASS'),('xfail','XFAIL'),('failure','FAIL'),('error','ERROR'),('skipped','SKIP')] if c.get(k))
  lp=100*cov['covered_lines']/cov['num_statements'];bp=100*cov['covered_branches']/cov['num_branches']
  links=' · '.join(f'[{title}]({base}/{feature}/{name})' for title,name in [('Trace','trace.jsonl'),('JUnit','internal_junit/'),('Cobertura','coverage_production.json'),('XML cobertura','coverage_production.xml')])
  lines.append(f'| [{feature}]({base}/manifest.json) | {result} | {cov["covered_lines"]}/{cov["num_statements"]} ({lp:.2f}%) | {cov["covered_branches"]}/{cov["num_branches"]} ({bp:.2f}%) | {links} |')
 lines+=['','## Interpretação','',
 'Os hashes, os totais JUnit, a presença dos casos nos traces e os totais de cobertura foram conferidos pelo gerador. Isso verifica consistência dos arquivos preservados; não demonstra completude dos perfis de processos encerrados nem força dos oráculos.', '',
 'XFAIL representa expectativa não atendida. Consulte `step_errors` em `indice_features.json` para distinguir erro na preparação e falha na asserção. A cobertura inclui inicialização, preparação e encerramento, não apenas os passos ou asserções. Os percentuais não são somados e não substituem a [cobertura geral](cobertura_geral/README.md).', '',
 '| Feature | Propriedades | Alcance e limitação |','|---|---|---|']
 lines += [f'| {r["feature"]} | {r["properties"]} | {r["limitation"]} |' for r in rows]
 lines+=['','## Histórico e reprodução','',
 '[Repetições de 25/10](diagnosticos/repeticoes_features_2026-10-25/README.md): as três features com falha foram reexecutadas; as falhas reapareceram. As tentativas anteriores continuam em `campanhas_traces/`, incluindo falhas e coletas interrompidas. A escolha da campanha desta tabela não altera seus resultados nem os agrega retrospectivamente.', '',
 'Para conferir novamente: `python3 ferramentas_traces/gerar_indice_features.py --root .` na raiz deste repositório. O arquivo JSON preserva os nomes exatos das campanhas e casos.']
 (root/'INDICE_FEATURES.md').write_text('\n'.join(lines)+'\n')
 print(f'{len(rows)} features auditadas; índice gerado.')

if __name__=='__main__':main()
