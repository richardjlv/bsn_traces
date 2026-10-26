# -*- coding: utf-8 -*-
"""BDD events compatible with Python 2.7 and 3 (ROS 1 Melodic)."""
from __future__ import unicode_literals
import io
import json
import os
import time
import pytest


def emit(event, **fields):
    directory = os.environ.get('BSN_TRACE_DIR')
    if not directory:
        return
    record = dict(event=event, schema=1, pid=os.getpid(), time_s=time.time(),
                  feature_run=os.environ.get('BSN_TRACE_FEATURE'), **fields)
    clock = getattr(time, 'monotonic', None)
    record['monotonic_s'] = clock() if clock else None
    with io.open(os.path.join(directory, 'events_%s.jsonl' % os.getpid()), 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=True) + '\n')


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
    emit('scenario_end', **fields(request, feature, scenario))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    emit('step_start', **fields(request, feature, scenario, step))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    emit('step_end', **fields(request, feature, scenario, step))


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
