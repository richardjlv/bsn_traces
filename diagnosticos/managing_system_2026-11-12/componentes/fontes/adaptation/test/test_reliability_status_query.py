from collections import deque
from types import SimpleNamespace

import pytest

from adaptation.data_access.data_access import DataAccess
from bsn_interfaces.srv import DataAccessRequest


@pytest.mark.parametrize('statuses, expected', [
    (['success', 'running'], 1.0),
    (['success', 'fail', 'running'], 0.5),
    (['success', 'success', 'fail'], 2.0 / 3.0),
    (['running'], 0.0),
    ([], 0.0),
])
def test_query_counts_only_success_and_fail(statuses, expected):
    subject = SimpleNamespace(status={
        'g3t1_1': deque((i, value) for i, value in enumerate(statuses))
    })
    request = DataAccessRequest.Request()
    request.query = 'all:reliability:'
    response = DataAccess.process_query(subject, request, DataAccessRequest.Response())
    payload = response.content.rstrip(';').split(':', 1)[1]
    assert float(payload.split(',')[-1]) == pytest.approx(expected, abs=1e-6)
    assert list(subject.status['g3t1_1']) == list(enumerate(statuses))
