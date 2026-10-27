#!/usr/bin/env python3
"""Compare actual reliability-policy method bodies with controlled state.
Dependencies for logging/publication are doubles, not a running ROS system.
"""
import ast,hashlib,json,subprocess,tempfile,shutil
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
CASES=[('degradacao',.8,.5),('recuperacao_acima_referencia',.8,.95),('erro_zero',.8,.8),('dentro_margem',.8,.79)]
outroot=ROOT/'campanhas_fechamento';outroot.mkdir(exist_ok=True)
out=Path(tempfile.mkdtemp(prefix='controlador_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_',dir=outroot))
cpp=ROOT/'bsn2/src/sa-bsn/system_manager/enactor/src/Controller.cpp'
py=ROOT/'bsn_ros2/adaptation/adaptation/enactor/controller.py'
for p,n in [(cpp,'Controller.cpp'),(py,'controller.py'),(Path(__file__),'runner_used.py')]:shutil.copy2(p,out/n)
s=cpp.read_text();a=s.index('void Controller::apply_reli_strategy(');b=s.index('void Controller::apply_cost_strategy(',a);method=s[a:b]
pre='''#include <map>
#include <string>
#include <vector>
#include <cmath>
#include <iostream>
#include <iomanip>
#define ROS_DEBUG(...) ((void)0)
namespace ros {namespace this_node {std::string getName(){return "/enactor";}}}
namespace archlib {struct AdaptationCommand{std::string source,target,action;};struct Exception{std::string source,target,content;};}
struct AdaptPub {std::vector<std::string> actions;void publish(const archlib::AdaptationCommand&m){actions.push_back(m.action);}};
struct ExceptPub {void publish(const archlib::Exception&) {}};
class Controller {public:
std::map<std::string,double> r_ref,r_curr,kp,freq;
std::map<std::string,int> exception_buffer,replicate_task;
std::map<std::string,std::vector<int>> invocations;
double stability_margin=.05;std::string adaptation_parameter="reliability";
AdaptPub adapt;ExceptPub except;
void apply_reli_strategy(const std::string&);
};
'''
main='''int main(){double ref,cur;while(std::cin>>ref>>cur){Controller c;std::string k="/g3t1_1";c.r_ref[k]=ref;c.r_curr[k]=cur;c.kp[k]=50;c.freq[k]=10;c.apply_reli_strategy(k);std::cout<<std::setprecision(17)<<c.freq[k]<<" "<<c.adapt.actions.size();for(auto a:c.adapt.actions)std::cout<<" "<<a;std::cout<<"\\n";}}
'''
(out/'harness.cpp').write_text(pre+method+main)
cmd=['g++','-std=c++11','-O0',str(out/'harness.cpp'),'-o',str(out/'policy')]
build=subprocess.run(cmd,capture_output=True,text=True);(out/'build.log').write_text(build.stdout+build.stderr);build.check_returncode()
run=subprocess.run([str(out/'policy')],input=''.join(f'{ref} {cur}\n' for _,ref,cur in CASES),capture_output=True,text=True,check=True);(out/'cpp.txt').write_text(run.stdout)
tree=ast.parse(py.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controller');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='apply_reli_strategy')
namespace={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(py),'exec'),namespace)
rows=[]
for (name,ref,cur),line in zip(CASES,run.stdout.splitlines()):
 actions=[];k='/g3t1_1'
 obj=SimpleNamespace(r_ref={k:ref},r_curr={k:cur},freq={k:10.},stability_margin=.05,kp_individual={k:50.},kp=50.,exception_buffer={k:0},invocations={k:[]},
 _send_adaptation_command=lambda target,action:actions.append(action),_publish_exception=lambda *args:None,get_logger=lambda:SimpleNamespace(debug=lambda *args:None))
 namespace['apply_reli_strategy'](obj,k)
 parts=line.split();cppf=float(parts[0]);cpactions=parts[2:]
 rows.append(dict(case=name,reference=ref,current=cur,initial_frequency=10,kp=50,margin=.05,cpp_frequency=cppf,cpp_commands=cpactions,python_frequency=obj.freq[k],python_commands=actions,equal_frequency=abs(cppf-obj.freq[k])<=1e-9,equal_command_presence=bool(cpactions)==bool(actions)))
result=dict(boundary='isolated_actual_method_bodies_with_publication_doubles',source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [cpp,py]},rows=rows,command=cmd,limitations=['Not a runtime reliability recovery experiment.','Outputs recorded including disagreements; not all are intended requirements.','No C++/Python production source modified.'])
(out/'resultados.json').write_text(json.dumps(result,indent=2)+'\n');print(out);print(json.dumps(rows,indent=2))
