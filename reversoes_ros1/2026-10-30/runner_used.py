#!/usr/bin/env python3
"""Controlled reversions in an isolated ROS 1 workspace. Requires Python >=3.6."""
import argparse, datetime, difflib, hashlib, json, os, re, shutil, signal, subprocess, tarfile, tempfile, time
from pathlib import Path
import xml.etree.ElementTree as ET

ENGINE='sa-bsn/system_manager/adaptation_engine/src/Engine.cpp'
RELI='sa-bsn/system_manager/adaptation_engine/src/ReliabilityEngine.cpp'
SENSOR='libbsn/src/configuration/SensorConfiguration.cpp'
ROUNDS=['baseline','sem_B2','sem_B3','sem_B4','sem_B5','sem_B7','baseline_final']

def swap(s,a,b):
    if s.count(a)!=1:raise ValueError('Expected one matching patch anchor: '+a[:80])
    return s.replace(a,b,1)

def variants(base):
    result={}
    for name in ROUNDS:
        files=dict(base)
        if name=='sem_B2':
            s=files[ENGINE];start=s.index('void Engine::body()');s=s[:start]+swap(s[start:],'while (ros::ok())','while (ros::ok)');files[ENGINE]=s
        elif name=='sem_B3':
            s=files[ENGINE];start=s.index('bool Engine::sendAdaptationParameter(');end=s.index('void Engine::receiveException',start)
            body=s[start:end];body=swap(body,'        return true;\n','');body=swap(body,'        return false;\n','');files[ENGINE]=s[:start]+body+s[end:]
        elif name=='sem_B4':files[RELI]=swap(files[RELI],', cycles(0)', '')
        elif name=='sem_B5':
            s=files[ENGINE];start=s.index('    // Antes da alteração');end=s.index('    setUp_formula(formula_str);',start)
            files[ENGINE]=s[:start]+'''    std::string formula_str = "";
    do {
        formula_str = fetch_formula(qos_attribute);
        ros::Duration(1.0).sleep();
    } while (formula_str == "");

'''+s[end:]
        elif name=='sem_B7':
            s=swap(files[SENSOR],'return lowPercentage.in_range(val);','return lowRisk.in_range(val);')
            s=swap(s,'return midPercentage.in_range(val);','return (mediumRisk[0].in_range(val) || mediumRisk[1].in_range(val));')
            files[SENSOR]=swap(s,'return highPercentage.in_range(val);','return (highRisk[0].in_range(val) || highRisk[1].in_range(val));')
        result[name]=files
    return result

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def hashes(root):return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}

def xml_summary(folder):
    cases=[];errors=[]
    for p in sorted(folder.rglob('*.xml')):
        try:tree=ET.parse(str(p))
        except ET.ParseError as exc:errors.append({'file':str(p),'error':str(exc)});continue
        for c in tree.iter('testcase'):
            status='passed'
            for tag in ['skipped','failure','error']:
                child=c.find(tag)
                if child is not None:
                    status=tag
                    if tag=='skipped' and 'xfail' in (str(child.attrib)+str(child.text)).lower():status='xfail'
            cases.append({'file':str(p.relative_to(folder)),'class':c.get('classname'),'name':c.get('name'),'status':status})
    return {'cases':cases,'parse_errors':errors,'note':'XML entries include wrappers. Do not sum as independent scenarios.'}

def clean_env():
    env=dict(os.environ)
    for key in list(env):
        if key.startswith(('ROS_','AMENT_','COLCON_','CMAKE_PREFIX_PATH','CATKIN_')) or key in ['PYTHONPATH','LD_LIBRARY_PATH','PKG_CONFIG_PATH','LLVM_PROFILE_FILE']:env.pop(key,None)
    env['PATH']='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    return env

def run(cmd,log,env,cwd,timeout):
    started=time.monotonic();timed_out=False
    with log.open('w') as f:
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,cwd=str(cwd),start_new_session=True)
        try:
            try:rc=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(p.pid,signal.SIGINT)
                try:rc=p.wait(timeout=20)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
        finally:
            # Only descendants of this launch, never other ROS sessions.
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait()
    return {'argv':cmd,'returncode':rc,'timeout':timed_out,'duration_s':time.monotonic()-started}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--scope',choices=['all','engine'],default='all')
    ap.add_argument('--jobs',type=int,default=2)
    ap.add_argument('--test-timeout',type=int,default=900)
    args=ap.parse_args();original=args.workspace.resolve();source=original/'src'
    base={n:(source/n).read_text() for n in [ENGINE,RELI,SENSOR]};states=variants(base)
    if args.check:
        for name,files in states.items():print(name,','.join(p for p in files if files[p]!=base[p]) or 'unchanged')
        return 0
    setup=Path('/opt/ros/melodic/setup.bash')
    if not setup.is_file():ap.error('Execute in ROS 1/Melodic; use --check for patch validation only.')
    if args.jobs<1 or args.test_timeout<1:ap.error('jobs and timeout must be positive')
    if not shutil.which('clang') or not shutil.which('clang++'):ap.error('Clang and clang++ are required')
    output=(args.output or original/'reversoes_novas').resolve();output.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(str(output)).free<8*1024**3:ap.error('At least 8 GiB free required for isolated build; original workspace remains untouched.')
    campaign=Path(tempfile.mkdtemp(prefix='reversoes_'+datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')+'_',dir=str(output)))
    print('Campaign: '+str(campaign),flush=True)
    shutil.copy2(__file__,str(campaign/'runner_used.py'))
    work=campaign/'workspace';work.mkdir();dest=work/'src'
    ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','*.profraw','*.profdata','*.log','build','devel','install','campanhas_fechamento','reversoes_novas')
    shutil.copytree(str(source),str(dest),ignore=ignore,symlinks=True)
    # Use the Melodic catkin toplevel rather than an absolute link from another host.
    top=dest/'CMakeLists.txt'
    if top.exists() or top.is_symlink():top.unlink()
    top.symlink_to('/opt/ros/melodic/share/catkin/cmake/toplevel.cmake')
    for p in dest.rglob('*'):
        if p.is_symlink() and p!=top and not str(p.resolve()).startswith(str(dest)+os.sep):
            raise RuntimeError('External source symlink requires review: '+str(p))
    snapshots=hashes(dest);save(campaign/'source_sha256.json',snapshots)
    with tarfile.open(str(campaign/'sources_baseline.tar.gz'),'w:gz') as tar:tar.add(str(dest),arcname='src')
    for cmd,name in [(['git','-C',str(original),'rev-parse','HEAD'],'git_head.txt'),(['git','-C',str(original),'status','--short'],'git_status.txt'),(['git','-C',str(original),'diff','--binary'],'git_diff.patch')]:
        with (campaign/name).open('wb') as f:subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT)
    if args.scope=='engine':
        launches=[dest/('sa-bsn/target_system/components/component/test/test_bdd/test_'+n+'.launch') for n in ['injector','managing_system','target_system','check_bsn']]
    else:
        launches=[]
        for p in sorted(dest.rglob('test_*.launch')):
            try:
                if any(True for _ in ET.parse(str(p)).iter('test')):launches.append(p)
            except ET.ParseError:raise RuntimeError('Invalid launch XML: '+str(p))
    if not launches:raise RuntimeError('No rostest launches selected')
    env=clean_env()
    build_script=campaign/'build.sh'
    build_script.write_text('''#!/bin/bash
set -eo pipefail
source /opt/ros/melodic/setup.bash
clang --version
clang++ --version
python2 --version
catkin_make -j"$1" -l"$1" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER="$(command -v clang)" -DCMAKE_CXX_COMPILER="$(command -v clang++)" -DCATKIN_ENABLE_TESTING=ON '-DCMAKE_CXX_FLAGS=-fprofile-instr-generate -fcoverage-mapping -O0 -fno-inline' '-DCMAKE_EXE_LINKER_FLAGS=-fprofile-instr-generate -fcoverage-mapping' '-DCMAKE_SHARED_LINKER_FLAGS=-fprofile-instr-generate -fcoverage-mapping'
catkin_make tests -j"$1" -l"$1"
source devel/setup.bash
export PYTHONPATH="$PWD/src/ros_pytest/src${PYTHONPATH:+:$PYTHONPATH}"
python2 -c 'import ros_pytest, pytest, pytest_bdd'
rospack find component
''')
    test_script=campaign/'test.sh'
    test_script.write_text('''#!/bin/bash
set -eo pipefail
source /opt/ros/melodic/setup.bash
source "$1/devel/setup.bash"
export PYTHONPATH="$1/src/ros_pytest/src${PYTHONPATH:+:$PYTHONPATH}"
exec rostest --results-base-dir "$2" --results-filename wrapper.xml "$3"
''')
    summary={'campaign':str(campaign),'scope':args.scope,'rounds':[],'complete':False,'launches':[str(p.relative_to(dest)) for p in launches],
             'method':'corrected baseline; single reversion per round; final corrected baseline',
             'limits':['New campaign on current tests, not reconstruction of historic R1-R6.','B3/B4 include undefined behavior; lack of failure is not proof of correctness.','Raw XML contains wrappers and internal cases; no aggregate pass claim.']}
    save(campaign/'manifest.json',summary)
    for name in ROUNDS:
        print('Starting '+name,flush=True);rd=campaign/name;rd.mkdir();(rd/'profiles').mkdir()
        for rel,text in states[name].items():
            (dest/rel).write_text(text)
            target=rd/'sources'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        diff=''.join(''.join(difflib.unified_diff(base[p].splitlines(True),states[name][p].splitlines(True),fromfile='baseline/'+p,tofile=name+'/'+p)) for p in base)
        (rd/'change.patch').write_text(diff)
        # Recreate only generated directories inside this new campaign.
        for folder in ['build','devel']:
            if (work/folder).exists():shutil.rmtree(str(work/folder))
        roundenv=dict(env);roundenv['LLVM_PROFILE_FILE']=str(rd/'profiles/%m.profraw')
        build=run(['bash',str(build_script),str(args.jobs)],rd/'build.log',roundenv,work,7200)
        row={'name':name,'build':build,'tests':[]};summary['rounds'].append(row);save(campaign/'manifest.json',summary)
        if build['returncode']!=0 or build['timeout']:
            row['status']='build_failed';save(campaign/'manifest.json',summary);print('Build failed: '+str(rd/'build.log'),flush=True);return 1
        shutil.copy2(str(work/'build/CMakeCache.txt'),str(rd/'CMakeCache.txt'))
        save(rd/'executables_sha256.json',hashes(work/'devel/lib'))
        for number,launch in enumerate(launches):
            if shutil.disk_usage(str(campaign)).free<1024**3:
                row['status']='stopped_low_disk';save(campaign/'manifest.json',summary)
                print('Stopped with less than 1 GiB free; preserved '+str(campaign),flush=True);return 1
            td=rd/('%03d_'%number+launch.stem);td.mkdir();(td/'roslog').mkdir();(td/'ros_home').mkdir()
            te=dict(roundenv);te['ROS_LOG_DIR']=str(td/'roslog');te['ROS_HOME']=str(td/'ros_home');te['ROS_TEST_RESULTS_DIR']=str(td/'xml')
            outcome=run(['bash',str(test_script),str(work),str(td/'xml'),str(launch)],td/'rostest.log',te,work,args.test_timeout)
            outcome['launch']=str(launch.relative_to(dest));outcome['xml']=xml_summary(td/'xml');row['tests'].append(outcome)
            outcome['xml_available']=bool(outcome['xml']['cases'])
            save(td/'result.json',outcome);save(campaign/'manifest.json',summary)
            print(name+' '+launch.stem+' rc='+str(outcome['returncode']),flush=True)
        row['status']='executed';save(campaign/'manifest.json',summary)
    for rel,text in base.items():(dest/rel).write_text(text)
    summary['complete']=True;summary['original_production_unchanged']=all((source/p).read_text()==base[p] for p in base)
    save(campaign/'manifest.json',summary)
    files=[p for p in sorted(campaign.rglob('*')) if p.is_file() and work not in p.parents]
    (campaign/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(campaign))+'\n' for p in files))
    print('Complete; results require case-level review: '+str(campaign),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
