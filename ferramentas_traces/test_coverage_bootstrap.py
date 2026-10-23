"""The bootstrap must instrument application children, but not ROS CLI clients."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from coverage_support import bootstrap_text


@pytest.mark.parametrize('script_name,enabled,expected', [
    ('ros2', True, False), ('sensor', True, True), ('pytest', True, True),
    ('sensor', False, False),
])
def test_process_selection_and_previous_hook(tmp_path, script_name, enabled, expected):
    marker = tmp_path / 'instrumented'
    previous_marker = tmp_path / 'previous_loaded'
    previous = tmp_path / 'previous.py'
    previous.write_text(f'from pathlib import Path\nPath({str(previous_marker)!r}).touch()\n')
    (tmp_path / 'coverage.py').write_text(
        'from pathlib import Path\ndef process_startup():\n'
        f'    Path({str(marker)!r}).touch()\n')
    (tmp_path / 'sitecustomize.py').write_text(bootstrap_text(
        str(previous), enabled=enabled, skip_ros_cli=True))
    script = tmp_path / script_name
    script.write_text('print("application executed")\n')
    env = dict(os.environ, PYTHONPATH=str(tmp_path))
    result = subprocess.run([sys.executable, str(script)], env=env,
                            capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'application executed'
    assert previous_marker.exists()
    assert marker.exists() is expected
