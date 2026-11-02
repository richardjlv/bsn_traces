from pathlib import Path
import difflib
import hashlib
import json
import platform
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
sources = root / 'sources'
include = sources / 'include'
lib = Path('/ros_ws/src/bsn2/src/libbsn')
if not sources.exists():
    for rel in ['include/libbsn/configuration/SensorConfiguration.hpp',
                'include/libbsn/range/Range.hpp', 'src/configuration/SensorConfiguration.cpp',
                'src/range/Range.cpp', 'test/unit/configuration/ConfigurationTest.cpp',
                'test/main.cpp', 'CMakeLists.txt']:
        dest = sources / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(lib / rel, dest)
original = sources / 'src/configuration/SensorConfiguration.cpp'
mutant = sources / 'SensorConfiguration_b7.cpp'
text = original.read_text()
for before, after in [
    ('return lowPercentage.in_range(val);', 'return lowRisk.in_range(val);'),
    ('return midPercentage.in_range(val);', 'return (mediumRisk[0].in_range(val) || mediumRisk[1].in_range(val));'),
    ('return highPercentage.in_range(val);', 'return (highRisk[0].in_range(val) || highRisk[1].in_range(val));'),
]:
    assert text.count(before) == 1
    text = text.replace(before, after)
mutant.write_text(text)
(root / 'b7.diff').write_text(''.join(difflib.unified_diff(
    original.read_text().splitlines(True), text.splitlines(True),
    fromfile='SensorConfiguration.cpp', tofile='SensorConfiguration_b7.cpp')))
results = {}
for variant, implementation in [('atual', original), ('b7_reintroduzido', mutant)]:
    binary = root / ('tests_' + variant)
    command = ['g++', '-std=c++14', '-O0', '-I' + str(include),
               str(sources / 'test/main.cpp'),
               str(sources / 'test/unit/configuration/ConfigurationTest.cpp'),
               str(implementation), str(sources / 'src/range/Range.cpp'),
               '-lgtest', '-pthread', '-o', str(binary)]
    (root / (variant + '_command.json')).write_text(json.dumps(command, indent=2))
    build = subprocess.run(command, capture_output=True, text=True)
    (root / (variant + '_build.log')).write_text(build.stdout + build.stderr)
    assert build.returncode == 0, build.stderr
    xml = root / (variant + '.xml')
    run = [str(binary), '--gtest_output=xml:' + str(xml)]
    if variant != 'atual':
        run.append('--gtest_filter=RiskClassificationTest.*')
    proc = subprocess.run(run, capture_output=True, text=True)
    (root / (variant + '.log')).write_text(proc.stdout + proc.stderr)
    cases = [{'suite': c.get('classname'), 'name': c.get('name'),
              'passed': c.find('failure') is None} for c in ET.parse(xml).iter('testcase')]
    results[variant] = {'returncode': proc.returncode, 'cases': cases}
    if variant == 'atual':
        assert proc.returncode == 0 and all(c['passed'] for c in cases)
        assert sum(c['suite'] == 'RiskClassificationTest' for c in cases) == 4
    else:
        assert proc.returncode == 1 and len(cases) == 4 and all(not c['passed'] for c in cases)
    binary.unlink()
(root / 'resultados.json').write_text(json.dumps(results, indent=2) + '\n')
(root / 'ambiente.json').write_text(json.dumps({
    'platform': platform.platform(),
    'compiler': subprocess.check_output(['g++', '--version'], text=True),
    'gtest': subprocess.check_output(['dpkg-query', '-W', 'libgtest-dev'], text=True),
    'scope': 'gtest direto, sem ROS/catkin; binários regeneráveis pelos comandos preservados'
}, indent=2, ensure_ascii=False) + '\n')
(root / 'SHA256SUMS').write_text(''.join(
    hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(root)) + '\n'
    for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps({k: {'cases': len(v['cases']), 'passed': sum(c['passed'] for c in v['cases'])}
                  for k, v in results.items()}))
