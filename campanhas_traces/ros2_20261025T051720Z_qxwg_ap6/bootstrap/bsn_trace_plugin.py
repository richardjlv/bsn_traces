"""Optional pytest plugin: BDD step events, separate append-only file per PID."""
import json
import os
from pathlib import Path
import time

import pytest


def emit(event, **fields):
    directory = os.environ.get('BSN_TRACE_DIR')
    if not directory:
        return
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    record = dict(schema=1, event=event, pid=os.getpid(),
                  feature_run=os.environ.get('BSN_TRACE_FEATURE'),
                  time_ns=time.time_ns(), monotonic_ns=time.monotonic_ns(), **fields)
    with (path / f'events_{os.getpid()}.jsonl').open('a') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')


def fields(request, feature, scenario, step=None):
    result = dict(nodeid=request.node.nodeid, feature=feature.name,
                  feature_file=str(feature.filename), scenario=scenario.name)
    if step is not None:
        result.update(keyword=step.type, step=step.name, line=step.line_number)
    return result


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_scenario(request, feature, scenario):
    emit('scenario_start', **fields(request, feature, scenario))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_after_scenario(request, feature, scenario):
    # End of the BDD function is not proof of PASS; use test_report below.
    emit('scenario_end', **fields(request, feature, scenario))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    emit('step_start', **fields(request, feature, scenario, step))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    # Capture textual parameters, not opaque fixture objects or their repr.
    parameters = {k: v for k, v in step_func_args.items()
                  if v is None or isinstance(v, (str, int, float, bool))}
    emit('step_end', parameters=parameters, **fields(request, feature, scenario, step))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    emit('step_error', exception_type=type(exception).__name__, message=str(exception),
         **fields(request, feature, scenario, step))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    emit('step_lookup_error', message=str(exception), **fields(request, feature, scenario, step))


def pytest_runtest_logreport(report):
    emit('test_report', nodeid=report.nodeid, phase=report.when, outcome=report.outcome,
         wasxfail=getattr(report, 'wasxfail', None), duration_s=report.duration,
         details=str(report.longrepr) if report.longrepr else None)
