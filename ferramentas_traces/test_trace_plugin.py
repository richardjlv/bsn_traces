"""Checks the observable trace contract without starting ROS."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_bdd_trace_distinguishes_pass_and_expected_failure(tmp_path):
    (tmp_path / 'sample.feature').write_text('''Feature: Trace contract
  Scenario: Passing example
    Given a value
    Then it is accepted
  Scenario: Known defect
    Given a value
    Then it is rejected
''')
    (tmp_path / 'test_sample.py').write_text('''import pytest
from pytest_bdd import scenario, given, then
@scenario('sample.feature', 'Passing example')
def test_pass(): pass
@pytest.mark.xfail(reason='known defect', strict=True)
@scenario('sample.feature', 'Known defect')
def test_known_defect(): pass
@given('a value')
def value(): pass
@then('it is accepted')
def accepted(): assert 2 + 2 == 4
@then('it is rejected')
def rejected(): assert False, 'expected mismatch'
''')
    env = dict(os.environ, BSN_TRACE_DIR=str(tmp_path / 'events'), BSN_TRACE_FEATURE='sample',
               PYTEST_PLUGINS='bsn_trace_plugin', PYTHONPATH=str(Path(__file__).parent))
    env.pop('PYTEST_ADDOPTS', None)
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-o', 'addopts=', 'test_sample.py'],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    events = [json.loads(line) for p in (tmp_path / 'events').glob('*.jsonl')
              for line in p.read_text().splitlines()]
    assert sum(e['event'] == 'scenario_start' for e in events) == 2
    assert sum(e['event'] == 'step_start' for e in events) == 4
    errors = [e for e in events if e['event'] == 'step_error']
    assert len(errors) == 1 and 'expected mismatch' in errors[0]['message']
    reports = [e for e in events if e['event'] == 'test_report' and e['phase'] == 'call']
    assert len(reports) == 2
    assert any(e['outcome'] == 'passed' and not e['wasxfail'] for e in reports)
    assert any(e['outcome'] == 'skipped' and e['wasxfail'] for e in reports)
