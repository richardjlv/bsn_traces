#!/usr/bin/env python3
"""Run ROS 2 BDD features separately; preserve traces, coverage and provenance."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time

TOOLS = Path(__file__).resolve().parent
PACKAGES = ('adaptation', 'central_hub', 'patient', 'sensor', 'shared_components', 'system_monitor')


def write_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def execute(command, cwd, env, destination, timeout):
    timed_out = threading.Event()
    with subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, start_new_session=True) as proc:
        def stop():
            timed_out.set()
            try:
                os.killpg(proc.pid, signal.SIGINT)
            except ProcessLookupError:
                return
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
        timer = threading.Timer(timeout, stop)
        timer.start()
        try:
            with gzip.open(destination, 'wb') as log:
                for line in proc.stdout:
                    log.write(line)
                    log.flush()
            code = proc.wait()
        finally:
            timer.cancel()
            # ROS CLI may leave a daemon in this session. Stop only our child
            # process group before combining profiles or starting another feature.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                for _ in range(50):
                    time.sleep(0.1)
                    try:
                        os.killpg(proc.pid, 0)
                    except ProcessLookupError:
                        break
                else:
                    os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    return dict(exit_code=code, timed_out=timed_out.is_set())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=TOOLS.parent / 'bsn_ros2')
    parser.add_argument('--output-root', type=Path, default=TOOLS.parent / 'campanhas_traces')
    parser.add_argument('--features', nargs='+', help='Names such as knowledge_repo or managing_system')
    parser.add_argument('--domain-id', type=int, default=87)
    parser.add_argument('--timeout', type=int, default=1200, help='Seconds per feature')
    parser.add_argument('--without-coverage', action='store_true', help='Diagnostic run with only BDD traces')
    parser.add_argument('--direct-readiness', action='store_true', help='Query lifecycle services directly within the original deadline')
    parser.add_argument('--hub-stack-after', type=int, default=0, help='Diagnostic: dump hub Python stacks after this many seconds')
    args = parser.parse_args()
    root = args.source_root.resolve()
    for name in ('coverage', 'pytest_bdd', 'launch_testing', 'rclpy'):
        if importlib.util.find_spec(name) is None:
            parser.error(f'Missing {name}; source ROS 2 and the workspace first')
    if os.environ.get('COVERAGE_PROCESS_START'):
        parser.error('Existing coverage instrumentation; use a clean environment')
    if not 0 <= args.domain_id <= 232 or args.timeout <= 0 or args.hub_stack_after < 0:
        parser.error('Invalid domain ID or timeout')
    files = {p.stem.removeprefix('test_').removesuffix('_bdd'): p
             for p in (root / 'features/test').glob('test_*_bdd.py')}
    selected = args.features or sorted(files)
    if not selected or len(set(selected)) != len(selected) or any(n not in files for n in selected):
        parser.error(f'Choose distinct features from {sorted(files)}')
    args.output_root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(args.output_root).free < 100 * 1024**2:
        parser.error('Less than 100 MiB free; preserve existing evidence before freeing space')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run = Path(tempfile.mkdtemp(prefix=f'ros2_{stamp}_', dir=args.output_root.resolve()))
    print(f'Campaign: {run}', flush=True)
    spec = importlib.util.spec_from_file_location('legacy_collector', TOOLS / 'coverage_support.py')
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.ROOT = root
    bootstrap = run / 'bootstrap'
    bootstrap.mkdir()
    previous = importlib.util.find_spec('sitecustomize')
    startup = collector.bootstrap_text(previous.origin if previous else None,
                                       enabled=not args.without_coverage, skip_ros_cli=True)
    if args.hub_stack_after:
        startup += ("import sys, faulthandler\n"
                    "if os.path.basename(sys.argv[0]) == 'emergency_detection':\n"
                    f"    faulthandler.dump_traceback_later({args.hub_stack_after}, repeat=False)\n")
    (bootstrap / 'sitecustomize.py').write_text(startup)
    for name in ('bsn_trace_plugin.py', 'coletar_ros2.py', 'coverage_support.py'):
        shutil.copyfile(TOOLS / name, bootstrap / name)
    manifest = dict(schema=1, started_utc=stamp, source_root=str(root), python=sys.version,
                    ros_distro=os.environ.get('ROS_DISTRO'), domain_id=args.domain_id,
                    coverage_enabled=not args.without_coverage,
                    coverage_process_exclusions=['ros2 CLI (executable basename)'],
                    direct_readiness=args.direct_readiness,
                    managing_groups=os.environ.get('BSN_MANAGING_GROUPS', 'default'),
                    hub_stack_after=args.hub_stack_after,
                    selected_features=selected, features={}, successful_collection=False,
                    limitations=['Coverage is per feature, including setup and shutdown, not per scenario.',
                                 'BDD hook events are not a complete causal trace of ROS messages.',
                                 'Processes killed without flushing may lose coverage data.'])
    manifest['source_sha256'] = collector.snapshot(run)
    for name, cmd in [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--short']),
                      ('diff', ['diff', 'HEAD', '--'])]:
        p = subprocess.run(['git', '-C', str(root), *cmd], capture_output=True)
        (run / f'git_{name}.txt').write_bytes(p.stdout)
    (run / 'dependencies.txt').write_bytes(subprocess.run(
        [sys.executable, '-m', 'pip', 'freeze'], capture_output=True).stdout)
    write_json(run / 'manifest.json', manifest)
    for name in selected:
        if shutil.disk_usage(run).free < 40 * 1024**2:
            manifest['stopped_reason'] = 'Insufficient free space; previous outputs preserved'
            break
        dest = run / name
        dest.mkdir()
        config = dest / 'coverage.ini'
        config.write_text(collector.configuration(root, dest / '.coverage', name))
        env = dict(os.environ)
        env.pop('PYTEST_ADDOPTS', None)
        env.update(COVERAGE_PROCESS_START=str(config), COVERAGE_RCFILE=str(config),
                   COVERAGE_FILE=str(dest / '.coverage'), BSN_COVERAGE_CAMPAIGN='1',
                   BSN_BDD_RESULTS_DIR=str(dest / 'internal_junit'), BSN_TRACE_DIR=str(dest / 'events'),
                   BSN_TRACE_FEATURE=name, ROS_DOMAIN_ID=str(args.domain_id),
                   ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST', ROS_LOG_DIR=str(dest / 'ros_logs'))
        env['PYTHONPATH'] = os.pathsep.join([str(bootstrap), *[str(root / p) for p in PACKAGES],
                                           env.get('PYTHONPATH', '')])
        env['PYTEST_PLUGINS'] = ','.join(filter(None, [env.get('PYTEST_PLUGINS'), 'bsn_trace_plugin']))
        env['BSN_TRACE_DIRECT_READINESS'] = '1' if args.direct_readiness else '0'
        if args.without_coverage:
            for key in ('COVERAGE_PROCESS_START', 'COVERAGE_RCFILE', 'COVERAGE_FILE'):
                env.pop(key, None)
        cmd = [sys.executable, '-m', 'pytest', '-v', '-rA', '-o', 'addopts=', '-p', 'no:pytest_cov',
               '--junitxml=' + str(dest / 'outer.xml'), str(files[name])]
        row = dict(command=cmd, state='running')
        manifest['features'][name] = row
        write_json(run / 'manifest.json', manifest)
        print(f'Starting {name}', flush=True)
        row.update(execute(cmd, root / 'features', env, dest / 'execution.log.gz', args.timeout))
        row['internal_junit'] = [collector.junit_counts(p) for p in sorted((dest / 'internal_junit').glob('*.xml'))]
        events = []
        for p in sorted((dest / 'events').glob('*.jsonl')):
            events.extend(json.loads(line) for line in p.read_text().splitlines())
        events.sort(key=lambda e: (e['monotonic_ns'], e['pid']))
        with (dest / 'trace.jsonl').open('w') as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False) + '\n')
        row['scenario_starts'] = sum(e['event'] == 'scenario_start' for e in events)
        row['step_starts'] = sum(e['event'] == 'step_start' for e in events)
        expected_cases = {c['name'] for report in row['internal_junit'] for c in report['cases']}
        traced_cases = {e['nodeid'].split('::')[-1] for e in events
                        if e['event'] == 'test_report' and e['nodeid'].startswith('steps/')}
        row['missing_case_traces'] = sorted(expected_cases - traced_cases)
        if args.without_coverage:
            row['coverage_status'] = 'disabled_for_diagnostic_comparison'
        else:
            try:
                from coverage import Coverage
                cov = Coverage(config_file=str(config), data_file=str(dest / '.coverage'))
                cov.combine(data_paths=[str(dest)], strict=True, keep=True)
                cov.save()
                cov.xml_report(outfile=str(dest / 'coverage_production.xml'), omit=collector.PRODUCTION_OMIT)
                cov.json_report(outfile=str(dest / 'coverage_production.json'), omit=collector.PRODUCTION_OMIT)
                row['coverage_contexts'] = sorted(cov.get_data().measured_contexts())
                row['coverage_totals'] = json.loads((dest / 'coverage_production.json').read_text())['totals']
            except Exception as error:
                row['coverage_error'] = str(error)
        row['state'] = 'finished'
        row['complete'] = (row['exit_code'] == 0 and bool(row['internal_junit'])
                           and row['scenario_starts'] > 0
                           and ('coverage_error' not in row or args.without_coverage)
                           and not row['missing_case_traces'])
        write_json(run / 'manifest.json', manifest)
        print(f'Finished {name}: rc={row["exit_code"]}, scenarios={row["scenario_starts"]}', flush=True)
    manifest['successful_collection'] = (len(manifest['features']) == len(selected)
                                         and all(r.get('complete') for r in manifest['features'].values()))
    manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
    write_json(run / 'manifest.json', manifest)
    hashes = {str(p.relative_to(run)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in run.rglob('*') if p.is_file()}
    write_json(run / 'sha256.json', hashes)
    print(f'Results: {run}; complete={manifest["successful_collection"]}', flush=True)
    return 0 if manifest['successful_collection'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
