"""Boundary and stale-message checks for the BSN-P03 assertions, without ROS."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_function(path, name, globals_dict):
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == name)
    function.decorator_list = []
    module = ast.Module(body=[function], type_ignores=[])
    exec(compile(module, str(path), 'exec'), globals_dict)
    return globals_dict[name]


@pytest.fixture(params=['ros1', 'ros2'])
def accepts(request):
    if request.param == 'ros1':
        function = load_function(
            ROOT / 'bsn2/src/sa-bsn/target_system/components/component/test/asserts.py',
            'check_time_performance', {},
        )

        def check(samples):
            return function(
                {'sensor': {'risk': [90], '%time': [1000000000]}},
                {'risk': [value for value, delay in samples],
                 '%time': [1000000000 + delay * 1000000000 for value, delay in samples]},
                'sensor', 'risk', 'risk',
            )
    else:
        function = load_function(
            ROOT / 'bsn_ros2/features/steps/test_bsn_p03.py',
            'hub_reports_emergency_in_time',
            {'EMERGENCY_BUDGET_S': 0.25, 'REACTION_WINDOW_S': 2,
             'TARGET_SYSTEM_TOPIC': '/target_system_data', 'HUB_FREQUENCY_HZ': 2},
        )

        def check(samples):
            observation = SimpleNamespace(
                injection_time=1.0, injection_attempts=1, injected_datapoint=90,
                target_messages=[{'trm_data': value, 'stamp': 1.0 + delay}
                                 for value, delay in samples],
            )
            try:
                function(observation)
            except AssertionError:
                return False
            return True
    return check


@pytest.mark.parametrize('samples,expected', [
    ([(90, 0.0)], True),
    ([(90, 0.249)], True),
    ([(90, 0.250)], True),
    ([(90, 0.251)], False),
    ([(90, 0.400)], False),
    ([(90, -0.005)], False),
    ([(90, -0.400)], False),
    ([(89, 0.100)], False),
    ([], False),
    ([(90, -0.005), (90, 0.100)], True),
    ([(90, -0.005), (90, 0.400)], False),
])
def test_temporal_boundary(accepts, samples, expected):
    assert accepts(samples) is expected


@pytest.fixture
def temporal_capture_module():
    import importlib.util
    path = ROOT / 'bsn2/src/sa-bsn/target_system/components/component/test/temporal_capture.py'
    spec = importlib.util.spec_from_file_location('temporal_capture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('missing', [None, 'sensor', 'target'])
def test_capture_uses_observer_clock(temporal_capture_module, monkeypatch, missing):
    module = temporal_capture_module
    stamps = iter([1000000000, 1010000000, 1020000000, 1030000000])
    monkeypatch.setattr(module, 'monotonic_ns', lambda: next(stamps))
    closed = []

    def subscribe(topic, msg_type, callback):
        kind = 'sensor' if topic == '/sensor' else 'target'
        if kind != missing:
            callback(SimpleNamespace(risk=90, data=45, trm_risk=90, trm_data=45,
                                     header=SimpleNamespace(stamp=0)))
        return SimpleNamespace(unregister=lambda: closed.append(topic))

    ros = SimpleNamespace(Subscriber=subscribe, is_shutdown=lambda: False)
    info = {'topic': '/sensor', 'risk_key': 'trm_risk', 'data_key': 'trm_data'}
    if missing:
        with pytest.raises(AssertionError, match='No .* messages captured'):
            module.capture_temporal_topics(ros, object, object, info, 0)
    else:
        sensor, target = module.capture_temporal_topics(ros, object, object, info, 0)
        assert sensor['/sensor']['%time'] == [1000000000]
        assert target['%time'] == [1010000000]
        assert sensor['/sensor']['risk'] == target['trm_risk'] == [90]
    assert closed == ['/sensor', '/TargetSystemData']


def test_linux_clock_is_monotonic(temporal_capture_module):
    first = temporal_capture_module.monotonic_ns()
    second = temporal_capture_module.monotonic_ns()
    assert 0 < first <= second
