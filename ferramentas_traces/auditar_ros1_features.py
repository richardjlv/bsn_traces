#!/usr/bin/env python3
"""Audita as campanhas ROS 1 de 26/10 e deriva cobertura com escopo explícito."""
from pathlib import Path
import collections, hashlib, json, re, tarfile
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
rows=[]
for folder in sorted((ROOT/'campanhas_traces').glob('ros1_20261026T*')):
 m=json.loads((folder/'manifest.json').read_text());feature=m['feature']
 hashes=json.loads((folder/'sha256.json').read_text())
 for rel,expected in hashes.items():
  assert hashlib.sha256((folder/rel).read_bytes()).hexdigest()==expected,(folder.name,rel)
 unavailable=[]
 with tarfile.open(folder/'sources.tar.gz') as archive:
  for rel,expected in m['source_sha256'].items():
   try: content=archive.extractfile(rel).read()
   except KeyError:
    unavailable.append(rel);continue
   assert hashlib.sha256(content).hexdigest()==expected,(folder.name,rel)
 expected='rosunit-'+({'target_system':'sensor_test','bsn_p03':'test_BSN-P03'}.get(feature,'test_'+feature))+'.xml'
 xml=folder/'test_results/component'/expected
 cases=[]
 for c in ET.parse(xml).iter('testcase'):
  skip=c.find('skipped')
  status='failure' if c.find('failure') is not None else 'error' if c.find('error') is not None else ('xfail' if skip.get('type')=='pytest.xfail' else 'skipped') if skip is not None else 'passed'
  cases.append(dict(name=c.get('name'),status=status))
 events=[json.loads(l) for l in (folder/'trace.jsonl').read_text().splitlines()]
 observed={e['nodeid'].split('::')[-1] for e in events if e['event']=='test_report' and e['phase']=='call'}
 assert observed=={c['name'] for c in cases},(feature,observed,{c['name'] for c in cases})
 scope=set((folder/'production_sources.txt').read_text().splitlines())
 raw=json.loads((folder/'coverage_production.json').read_text())
 files=[f for d in raw['data'] for f in d['files'] if f['filename'] in scope]
 totals={}
 for metric in ['lines','functions','regions']:
  total=sum(f['summary'][metric]['count'] for f in files);covered=sum(f['summary'][metric]['covered'] for f in files)
  totals[metric]=dict(count=total,covered=covered,percent=100*covered/total if total else 0)
 html=(folder/'html_production/index.html').read_text()
 last=re.findall(r'<tr.*?</tr>',html,re.S)[-1]
 html_counts=[(int(a),int(b)) for a,b in re.findall(r'\((\d+)/(\d+)\)',re.sub('<[^>]+>',' ',last))]
 assert html_counts==[(totals[k]['covered'],totals[k]['count']) for k in ['functions','lines','regions']],(folder.name,html_counts,totals)
 out=ROOT/'diagnosticos/ros1_features_2026-10-26';out.mkdir(exist_ok=True)
 filtered=out/(folder.name+'_coverage_filtered.json')
 filtered.write_text(json.dumps(dict(source_campaign=folder.name,scope='production_sources.txt',totals=totals,files=[dict(filename=f['filename'],summary=f['summary']) for f in files]),indent=2)+'\n')
 rows.append(dict(campaign=folder.name,feature=feature,counts=dict(collections.Counter(c['status'] for c in cases)),cases=cases,coverage=totals,raw_export_totals=m['coverage_totals'],filtered_files=len(files),hashes_verified=len(hashes),source_hashes_verified=len(m['source_sha256'])-len(unavailable),source_contents_unavailable=unavailable,errors=[e for e in events if e['event'] in ['step_error','step_lookup_error']],junit=str(xml.relative_to(folder))))
# Injector was run twice: retain both; choose the later run explicitly in the index.
selected={r['feature']:r for r in rows}
(ROOT/'indice_features_ros1.json').write_text(json.dumps(dict(campaigns=rows,selection={f:r['campaign'] for f,r in selected.items()}),ensure_ascii=False,indent=2)+'\n')
lines=['# ROS 1 — traces e cobertura por feature, 26/10/2026','',
 'As oito features foram executadas isoladamente. Foram preservadas nove campanhas, incluindo duas execuções do injetor. A tabela utiliza a segunda execução do injetor; a primeira permanece arquivada. O conjunto selecionado soma **51 casos: 49 PASS e dois XFAIL**, sem falhas inesperadas. Esses totais não representam uma execução geral única. Timestamps nos nomes de campanha estão em UTC.', '',
 '| Feature | Resultado interno | Linhas de produção | Evidências |','|---|---|---:|---|']
for f,r in selected.items():
 base='campanhas_traces/'+r['campaign'];c=r['coverage']['lines'];counts=', '.join(str(n)+' '+s.upper() for s,n in r['counts'].items())
 lines.append('| '+f+' | '+counts+' | %s/%s (%.2f%%)'%(c['covered'],c['count'],c['percent'])+' | [Campanha]('+base+'/manifest.json) · [Trace]('+base+'/trace.jsonl) · [JUnit]('+base+'/'+r['junit']+') · [HTML]('+base+'/html_production/index.html) · [Resumo]('+base+'/coverage_production.txt) |')
lines+=['','## Conferência e interpretação','',
 'Os hashes dos arquivos e das fontes arquivadas foram verificados, os casos internos foram confrontados com os reports do trace e a cobertura filtrada foi confrontada com o HTML de produção. Wrappers rostest não foram somados aos casos internos. Os binários não estão arquivados: seus hashes constam dos manifestos. O link src/CMakeLists.txt aponta para o catkin externo e seu conteúdo não está incluído no tar; essa exceção à conferência das fontes está explicitada no JSON.', '',
 '**Ressalva do export LLVM:** o arquivo original chamado coverage_production.json e os totais copiados ao manifesto incluem fontes fora de production_sources.txt nesta versão da ferramenta. Os relatórios HTML/texto aplicam o recorte corretamente. Este índice usa a soma dos resumos por arquivo filtrados pela lista explícita; os totais coincidem com o HTML. Os JSON originais foram preservados. Os [relatórios derivados](diagnosticos/ros1_features_2026-10-26/) tornam essa correção auditável. Não usar os percentuais brutos dos manifestos como cobertura de produção.', '',
 'O denominador do recorte é 4.263 linhas. Os percentuais incluem inicialização e encerramento dos processos; não são somáveis e não equivalem à cobertura geral nem aos ramos Python do ROS 2.', '',
 'O cenário positivo de estado de saúde (BDD08/P10), anteriormente comentado, aprovou no ROS 1. A asserção ROS 1 exige mais de um valor distinto de patient_status; a ROS 2 verifica valores percentuais válidos. As aprovações em ambas as versões fornecem evidências distintas, sem estabelecer igualdade do traço ou causalidade entre uma leitura e um estado.', '',
 'Os XFAIL pertencem à falha de persistência e à ausência de comandos de adaptação. Consulte os eventos de erro no JSON do índice para identificar o passo atingido. Os avisos LLVM registrados permanecem nos logs; a conferência de totais não demonstra completude dos perfis nem resolve a causa dos avisos.', '',
 'Para reproduzir esta auditoria: `python3 ferramentas_traces/auditar_ros1_features.py`. Consulte também o [índice ROS 2](INDICE_FEATURES.md).']
(ROOT/'INDICE_FEATURES_ROS1.md').write_text('\n'.join(lines)+'\n')
for f,r in selected.items():print(f,r['counts'],r['coverage']['lines'],[(e.get('keyword'),e.get('step')) for e in r['errors']])
