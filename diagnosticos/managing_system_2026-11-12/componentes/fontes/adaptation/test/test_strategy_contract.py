from types import SimpleNamespace
from unittest.mock import Mock

from adaptation.enactor.enactor import Enactor
from adaptation.engines.reli_engine import ReliabilityEngine


def test_published_strategy_updates_all_controller_references():
    publisher = Mock()
    engine = SimpleNamespace(
        strategy={'R_G3_T1_1': 0.85, 'R_G4_T1': 0.9},
        strategy_publisher=publisher, get_logger=Mock(),
    )
    controller = SimpleNamespace(
        adaptation_parameter='reliability',
        r_ref={'/g3t1_1': 1.0, '/g4t1': 1.0}, get_logger=Mock(),
    )
    ReliabilityEngine.execute(engine)
    message = publisher.publish.call_args.args[0]
    Enactor.receive_strategy(controller, message)
    assert controller.r_ref == {'/g3t1_1': 0.85, '/g4t1': 0.9}


def test_reactivation_restores_component_to_planning():
    engine = SimpleNamespace(strategy={}, deactivated_components={}, get_logger=Mock())
    for component, key in [('/g3t1_1', 'R_G3_T1_1'), ('/g4t1', 'R_G4_T1')]:
        ReliabilityEngine._process_context_response(engine, component + ':deactivate')
        assert engine.deactivated_components[key] == 1
        ReliabilityEngine._process_context_response(engine, component + ':activate')
        assert engine.deactivated_components[key] == 0


def test_equal_priority_plan_is_independent_of_term_insertion_order():
    from math import prod

    outputs = []
    for components in [('G3_T1_1', 'G4_T1'), ('G4_T1', 'G3_T1_1')]:
        strategy = {}
        for component in components:
            strategy.update({prefix + component: 1.0 for prefix in ('R_', 'CTX_', 'F_')})
        engine = SimpleNamespace(
            strategy=strategy, priority={key: 50 for key in strategy if key.startswith('R_')},
            deactivated_components={}, setpoint=0.9, tolerance=0.02,
            offset=0.5, gain=0.01, target_system_model=None,
            calculate_qos=lambda model, values: prod(values.values()),
            get_logger=Mock(), execute=Mock(),
        )
        ReliabilityEngine.plan(engine)
        engine.execute.assert_called_once()
        outputs.append(engine.strategy)
    assert outputs[0] == outputs[1]
    assert outputs[0]['R_G3_T1_1'] < outputs[0]['R_G4_T1']
