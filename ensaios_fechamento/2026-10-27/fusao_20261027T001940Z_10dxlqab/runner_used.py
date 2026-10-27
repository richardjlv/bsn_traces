#!/usr/bin/env python3
"""Exercise original C++/Python fusion with fixed oracles; no ROS graph."""
import argparse, hashlib, importlib.util, json, math, shutil, subprocess, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ('termometro_baixo', [10,20,20,20,20,20], 20.0),
    ('termometro_alto', [90,20,20,20,20,20], 90.0),
    ('retorno_baixo', [10,20,20,20,20,20], 20.0),
    ('misto', [10,20,30,40,60,80], 60.0),
]
TYPES = ['thermometer','ecg','oximeter','abps','abpd','glucosemeter']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT/'campanhas_fechamento')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='fusao_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_',dir=args.output))
    files={'Processor.cpp': ROOT/'bsn2/src/libbsn/src/processor/Processor.cpp',
           'include/libbsn/processor/Processor.hpp':ROOT/'bsn2/src/libbsn/include/libbsn/processor/Processor.hpp',
           'data_fusion.py':ROOT/'bsn_ros2/central_hub/central_hub/components/data_fusion.py',
           'shared_components/enums.py': ROOT/'bsn_ros2/shared_components/shared_components/enums.py'}
    hashes={}
    for dest,src in files.items():
        p=out/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,p)
        hashes[dest]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'shared_components/__init__.py').write_text('')
    shutil.copy2(__file__,out/'runner_used.py')
    (out/'harness.cpp').write_text('''#include "libbsn/processor/Processor.hpp"
#include <iomanip>
int main(){std::vector<double> v(6);while(std::cin>>v[0]>>v[1]>>v[2]>>v[3]>>v[4]>>v[5])std::cout<<std::setprecision(17)<<bsn::processor::data_fuse(v)<<"\\n";}
''')
    cpp=(out/'Processor.cpp').read_text()
    anchor='double data_fuse(vector<double> packetsReceived) {'
    assert cpp.count(anchor)==1
    (out/'Processor_mutant.cpp').write_text(cpp.replace(anchor,anchor+'\n packetsReceived[0] = 0.0; // synthetic ignored thermometer'))
    py=(out/'data_fusion.py').read_text();anchor='            # Calculation variables'
    assert py.count(anchor)==1
    (out/'data_fusion_mutant.py').write_text(py.replace(anchor,'            packets_received[0] = 0.0 # synthetic ignored thermometer\n'+anchor))
    sys.path.insert(0,str(out))
    observations=[];commands=[]
    inputs=''.join(' '.join(map(str,v))+'\n' for _,v,_ in CASES)
    for mutation in [False,True]:
        source='Processor_mutant.cpp' if mutation else 'Processor.cpp'
        exe=out/('cpp_mutant' if mutation else 'cpp_original')
        command=['g++','-std=c++11','-O0','-I'+str(out/'include'),str(out/'harness.cpp'),str(out/source),'-o',str(exe)]
        commands.append(command);build=subprocess.run(command,capture_output=True,text=True)
        (out/(exe.name+'_build.log')).write_text(build.stdout+build.stderr);build.check_returncode()
        run=subprocess.run([str(exe)],input=inputs,capture_output=True,text=True,check=True)
        (out/(exe.name+'.txt')).write_text(run.stdout)
        values=list(map(float,run.stdout.splitlines()));assert len(values)==len(CASES)
        spec=importlib.util.spec_from_file_location('fusion_mutant' if mutation else 'fusion',out/('data_fusion_mutant.py' if mutation else 'data_fusion.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for (name,vector,expected),cppvalue in zip(CASES,values):
            errors=[]
            node=SimpleNamespace(active=True,sensor_handler=SimpleNamespace(latest_risk=dict(zip(TYPES,vector))),
                battery_manager=SimpleNamespace(consume=lambda _:None),publisher_manager=SimpleNamespace(publish_status=lambda *args:None),
                get_logger=lambda:SimpleNamespace(error=errors.append))
            pyvalue=module.DataFusionEngine(node).fuse_data()
            for language,value in [('cpp',cppvalue),('python',pyvalue)]:
                observations.append(dict(case=name,inputs=vector,expected=expected,observed=value,variant=language+('_mutant' if mutation else '_original'),
                   passed=math.isfinite(value) and math.isclose(value,expected,rel_tol=0,abs_tol=1e-9),errors=errors if language=='python' else []))
    originals=[r for r in observations if r['variant'].endswith('_original')]
    detections=[r for r in observations if r['case']=='termometro_alto' and r['variant'].endswith('_mutant')]
    ok=all(r['passed'] and not r['errors'] for r in originals) and all(not r['passed'] and not r['errors'] for r in detections)
    manifest=dict(boundary='fusion_functions_without_ROS',absolute_tolerance=1e-9,source_sha256=hashes,
                  cases=observations,commands=commands,validation_passed=ok,
                  compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],python=sys.version,
                  limitations=['Synthetic mutation designed after examining code; not efficacy on unknown faults.',
                               'No node, communication, buffering, timing or durable storage exercised.'])
    (out/'resultados.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(out);print('validation_passed=',ok)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
