#!/usr/bin/env python3
"""Coleta local de uma feature ROS 1; usa o mesmo recorte de coverage.sh."""
import argparse
import collections
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET

FEATURES = ['check_bsn', 'knowledge_repo', 'target_system', 'data_persistance',
            'health_status', 'injector', 'bsn_p03', 'managing_system']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('coverage.sh mudou; revisar adaptador: ' + old[:90])
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feature', choices=FEATURES)
    parser.add_argument('--workspace', type=Path, required=True, help='Raiz catkin ROS 1 com devel/setup.bash')
    parser.add_argument('--output', type=Path, help='Raiz das campanhas (padrão: workspace/traces_features)')
    parser.add_argument('--rebuild', action='store_true', help='Reconstruir instrumentado como coverage.sh; usar na primeira coleta se necessário')
    args = parser.parse_args()
    ws = args.workspace.resolve()
    if not (ws / 'devel/setup.bash').is_file():
        parser.error('Workspace ROS 1 não preparado: falta devel/setup.bash. Execute na VM ROS 1 após o build inicial.')
    # Hold a workspace lock across the build, test and coverage export.
    lock = (ws / '.coletar_ros1.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('Já há uma coleta por feature neste workspace.')
    source = (ws / 'coverage.sh').read_text()
    feature_launch = 'BSN-P03' if args.feature == 'bsn_p03' else args.feature
    launch = ws / 'src/sa-bsn/target_system/components/component/test/test_bdd' / ('test_' + feature_launch + '.launch')
    if not launch.is_file():
        parser.error('Launch ausente: ' + str(launch))
    if not args.rebuild:
        binary = ws / 'devel/lib/component/g3t1_1'
        if not binary.is_file() or b'__llvm_prf' not in binary.read_bytes():
            parser.error('Binário instrumentado não identificado. Use --rebuild após preparar o ambiente Clang/LLVM.')
    root = (args.output or ws / 'traces_features').resolve()
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='ros1_' + datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ_') + args.feature + '_', dir=str(root)))
    (run / 'events').mkdir()
    (run / 'bootstrap').mkdir()
    here = Path(__file__).resolve().parent
    for name in ['coletar_ros1.py', 'bsn_trace_ros1_plugin.py']:
        shutil.copy2(here / name, run / 'bootstrap' / name)
    shutil.copy2(ws / 'coverage.sh', run / 'bootstrap/coverage_original.sh')
    source = replace_once(source, 'BASE_DIR=$(mktemp -d "$COVERAGE_ROOT/run_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX") || exit 1', 'BASE_DIR="$BSN_ROS1_RUN"')
    if not args.rebuild:
        start = source.index('# 2. Compilação')
        end = source.index('# 2b. Validação', start)
        source = source[:start] + 'echo "Reutilizando binários instrumentados; sem rebuild."\nsource devel/setup.bash || exit 1\n\n' + source[end:]
    source = replace_once(source, 'run_logged "$LOG_DIR/test_output.log" catkin_make run_tests "${BUILD_CMAKE_ARGS[@]}"',
                          'run_logged "$LOG_DIR/test_output.log" rostest "$BSN_ROS1_LAUNCH"')
    # Export machine-readable and text reports before final test-status checks.
    export = '''llvm-cov report "$TARGET_BINARY" $OTHER_BINARIES "${LIBRARY_OBJECTS[@]}" -instr-profile="$PROFDATA_FILE" "${PRODUCTION_SOURCES[@]}" > "$BASE_DIR/coverage_production.txt" 2> "$LOG_DIR/coverage_report.stderr"
REPORT_RC=$?
llvm-cov export "$TARGET_BINARY" $OTHER_BINARIES "${LIBRARY_OBJECTS[@]}" -instr-profile="$PROFDATA_FILE" "${PRODUCTION_SOURCES[@]}" > "$BASE_DIR/coverage_production.json" 2> "$LOG_DIR/coverage_export.stderr"
EXPORT_RC=$?
if [ "$REPORT_RC" -ne 0 ] || [ "$EXPORT_RC" -ne 0 ]; then
    echo "Falha na exportação da cobertura; consulte os logs." >&2
    exit 1
fi
'''
    source = replace_once(source, '# 7. Resumo no terminal', export + '\n# 7. Resumo no terminal')
    generated = run / 'bootstrap/executar_feature.sh'
    generated.write_text(source)
    env = os.environ.copy()
    env.update(BSN_ROS1_RUN=str(run), BSN_ROS1_LAUNCH=str(launch),
               BSN_TRACE_DIR=str(run / 'events'), BSN_TRACE_FEATURE=args.feature,
               ROS_LOG_DIR=str(run / 'ros_logs'),
               ROS_TEST_RESULTS_DIR=str(ws / 'build/test_results'))
    env['PYTHONPATH'] = str(run / 'bootstrap') + os.pathsep + env.get('PYTHONPATH', '')
    plugins = env.get('PYTEST_PLUGINS', '').split(',')
    env['PYTEST_PLUGINS'] = ','.join(p for p in plugins + ['bsn_trace_ros1_plugin'] if p)
    # Preserve selected source/config files, including locally modified files.
    snapshots = {}
    with tarfile.open(str(run / 'sources.tar.gz'), 'w:gz') as archive:
        for path in sorted((ws / 'src').rglob('*')):
            if not path.is_file() or any(x in path.parts for x in ['.git', '__pycache__']):
                continue
            if path.suffix not in ['.py', '.cpp', '.cc', '.h', '.hpp', '.launch', '.feature', '.xml', '.yaml', '.cfg', '.txt']:
                continue
            rel = str(path.relative_to(ws)); snapshots[rel] = sha(path)
            archive.add(str(path), arcname=rel)
    for name, command in [('git_head.txt', ['git', 'rev-parse', 'HEAD']),
                          ('git_status.txt', ['git', 'status', '--short']),
                          ('git_diff.txt', ['git', 'diff', 'HEAD'])]:
        with (run / name).open('w') as stream:
            subprocess.call(command, cwd=str(ws), stdout=stream, stderr=subprocess.STDOUT)
    manifest = dict(schema=1, feature=args.feature, workspace=str(ws), rebuild=args.rebuild,
                    state='running', source_sha256=snapshots,
                    limitations=['Trace de passos BDD, não trace causal completo de mensagens ROS.',
                                 'Cobertura LLVM inclui preparação e encerramento; não é cobertura por cenário.',
                                 'Processos encerrados sem flush podem perder perfis.',
                                 'Binários não são copiados; hashes identificam os objetos locais.'])
    def save():
        (run / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    save()
    print('Campanha: ' + str(run), flush=True)
    with (run / 'collector.log').open('w') as stream:
        rc = subprocess.call(['bash', str(generated)], cwd=str(ws), env=env, stdout=stream, stderr=subprocess.STDOUT)
    manifest.update(state='finished', exit_code=rc)
    manifest['object_sha256'] = {str(p.relative_to(ws)): sha(p) for p in (ws / 'devel/lib').rglob('*')
                                 if p.is_file() and (p.suffix == '.so' or (p.suffix == '' and os.access(str(p), os.X_OK)))}
    events = []
    for p in sorted((run / 'events').glob('*.jsonl')):
        events.extend(json.loads(line) for line in p.read_text().splitlines())
    events.sort(key=lambda event: (event['time_s'], event['pid']))
    (run / 'trace.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=True) + '\n' for e in events))
    reports = [e for e in events if e['event'] == 'test_report']
    manifest['scenario_starts'] = sum(e['event'] == 'scenario_start' for e in events)
    manifest['trace_report_counts'] = dict(collections.Counter((e['phase'] + ':' + e['outcome']) for e in reports))
    # Preserve XML individually: wrappers must not be added to internal cases.
    manifest['junit'] = []
    for p in sorted((run / 'test_results').rglob('*.xml')):
        cases = list(ET.parse(str(p)).iter('testcase'))
        manifest['junit'].append(dict(path=str(p.relative_to(run)), cases=len(cases),
            failures=sum(c.find('failure') is not None or c.find('error') is not None for c in cases),
            skipped=sum(c.find('skipped') is not None for c in cases)))
    cov = run / 'coverage_production.json'
    try:
        data = json.loads(cov.read_text())
        manifest['coverage_totals'] = [d.get('totals') for d in data['data']]
    except (ValueError, OSError, KeyError):
        manifest['coverage_totals'] = None
    manifest['artifacts_present'] = bool(manifest['scenario_starts'] and reports and manifest['junit'] and manifest['coverage_totals'])
    save()
    hashes = {str(p.relative_to(run)): sha(p) for p in sorted(run.rglob('*')) if p.is_file() and not p.is_symlink() and p.name != 'sha256.json'}
    (run / 'sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print('Resultado: rc=%s; cenários=%s; artefatos=%s' % (rc, manifest['scenario_starts'], manifest['artifacts_present']))
    print('Saída completa: ' + str(run / 'collector.log'))
    return rc if rc else (0 if manifest['artifacts_present'] else 2)


if __name__ == '__main__':
    raise SystemExit(main())
