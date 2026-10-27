#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Real enactor, controlled EngineRequest/DataAccessRequest doubles; Python 2/3."""
from __future__ import print_function
import argparse, os, sys, json, time, tempfile, datetime, shutil, hashlib, subprocess, signal, socket, threading
from validar_hub_controlado import now
CASES=[('degradacao',.5),('acima_referencia',.95),('erro_zero',.8),('dentro_margem',.79)]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ros',choices=['1','2'],required=True)
    ap.add_argument('--output',default='campanhas_fechamento')
    args=ap.parse_args()
    if not os.path.isdir(args.output):os.makedirs(args.output)
    out=tempfile.mkdtemp(prefix='adaptacao_ros'+args.ros+'_'+datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')+'_',dir=args.output)
    for f in [__file__,os.path.join(os.path.dirname(__file__),'validar_hub_controlado.py')]:shutil.copy2(f,out)
    result={'ros':args.ros,'boundary':'real enactor, controlled service responses -> log_adapt','frequency_hz':10,'kp':50,'reference':.8,'margin':.02,'cases':[],'complete':False}
    processes=[];handles=[];node=None;lock=threading.RLock(); commands=[];requests=[];active=[None];trace=open(os.path.join(out,'trace.jsonl'),'w')
    def log(r):
        with lock:trace.write(json.dumps(r)+'\n');trace.flush()
    def spawn(cmd):
        log({'event':'process','argv':cmd});f=open(os.path.join(out,'process_%d.log'%len(processes)),'w');handles.append(f)
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,preexec_fn=os.setsid);processes.append(p);return p
    def snapshot(path):
        path=os.path.realpath(path);digest=hashlib.sha256(open(path,'rb').read()).hexdigest()
        result.setdefault('source_sha256',{})[path]=digest
        if path.endswith(('.py','.cpp','.hpp')):shutil.copy2(path,os.path.join(out,digest+'_'+os.path.basename(path)))
    def response_content(req):
        with lock:
            a=active[0];content=('%s:%.12g;'%(a[0],a[1])) if a else ''
            r={'event':'data_response','monotonic':now(),'name':req.name,'query':req.query,'content':content};requests.append(r);log(r)
        return content
    def command(msg):
        r={'event':'command','monotonic':now(),'source':msg.source,'target':msg.target,'action':msg.action}
        with lock:commands.append(r);log(r)
    try:
        if args.ros=='1':
            import rospy,rosgraph,rospkg,roslib.packages
            from archlib.msg import Event,Strategy,AdaptationCommand
            from archlib.srv import EngineRequest,EngineRequestResponse,DataAccessRequest,DataAccessRequestResponse
            rp=rospkg.RosPack();base=rp.get_path('enactor')
            for f in ['src/Controller.cpp','src/Enactor.cpp']:snapshot(os.path.join(base,f))
            binaries=roslib.packages.find_node('enactor','enactor') or []
            if not binaries:raise RuntimeError('enactor executable unavailable; source the compiled ROS 1 workspace')
            for f in binaries:snapshot(f)
            s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close();os.environ['ROS_MASTER_URI']='http://127.0.0.1:%d'%port
            spawn(['roscore','-p',str(port)]);deadline=now()+60
            while True:
                try:rosgraph.Master('/adaptation_probe').getPid();break
                except Exception:
                    if now()>deadline:raise RuntimeError('master not ready')
                    time.sleep(.1)
            rospy.init_node('adaptation_probe',disable_signals=True)
            for k,v in [('frequency',10.0),('kp',50.0),('adaptation_parameter','reliability')]:rospy.set_param('/'+k,v)
            engine=rospy.Service('EngineRequest',EngineRequest,lambda req:EngineRequestResponse(content='reliability'))
            data=rospy.Service('DataAccessRequest',DataAccessRequest,lambda req:DataAccessRequestResponse(content=response_content(req)))
            ep=rospy.Publisher('/event',Event,queue_size=10);sp=rospy.Publisher('/strategy',Strategy,queue_size=10)
            sub=rospy.Subscriber('/log_adapt',AdaptationCommand,command,queue_size=100)
            process=spawn(['rosrun','enactor','enactor'])
            def spin(dt):time.sleep(dt)
            def ready():return ep.get_num_connections()>0 and sp.get_num_connections()>0 and sub.get_num_connections()>0
        else:
            os.environ['ROS_DOMAIN_ID']='92'
            import rclpy,importlib
            from rclpy.node import Node
            from bsn_interfaces.msg import Event,Strategy,AdaptationCommand
            from bsn_interfaces.srv import EngineRequest,DataAccessRequest
            for m in ['adaptation.enactor.controller','adaptation.enactor.enactor']:snapshot(importlib.import_module(m).__file__)
            rclpy.init(args=[]);node=Node('adaptation_probe')
            def engine_cb(req,res):res.content='reliability';return res
            def data_cb(req,res):res.content=response_content(req);return res
            engine=node.create_service(EngineRequest,'EngineRequest',engine_cb);data=node.create_service(DataAccessRequest,'DataAccessRequest',data_cb)
            ep=node.create_publisher(Event,'event',10);sp=node.create_publisher(Strategy,'strategy',10)
            sub=node.create_subscription(AdaptationCommand,'log_adapt',command,100)
            process=spawn(['ros2','run','adaptation','enactor','--ros-args','-p','frequency:=10.0','-p','kp:=50.0','-p','stability_margin:=0.02'])
            def spin(dt):rclpy.spin_once(node,timeout_sec=dt)
            def ready():return ep.get_subscription_count()>0 and sp.get_subscription_count()>0 and node.count_publishers('/log_adapt')>0
        def pump(seconds):
            deadline=now()+seconds
            while now()<deadline:
                if process.poll() is not None:raise RuntimeError('enactor exited; see process log')
                spin(min(.05,max(0,deadline-now())))
        deadline=now()+90
        while not ready() or not requests:
            if now()>deadline:raise RuntimeError('enactor connections/service activity not ready')
            pump(.05)
        log({'event':'ready','monotonic':now()})
        for i,(name,current) in enumerate(CASES):
            target='/test_adapt_%d'%i
            ev=Event();ev.source=target;ev.content='activate';ev.freq=10.0;ep.publish(ev);pump(.5)
            st=Strategy();st.source='/controlled_engine';st.target='/enactor';st.content=target+':0.8;';sp.publish(st);pump(.5)
            start=now()
            with lock:active[0]=(target,current)
            pump(4.0)
            with lock:active[0]=None
            pump(.5)
            rr=[r for r in requests if r['content'].startswith(target+':')];cc=[c for c in commands if c['target']==target]
            # A late response is drained before the next case. Distinct targets
            # ensure no frequency state is reused between cases.
            error=.8-current;delta=.5*error
            policy_emits=(error!=.02*.8) if args.ros=='1' else abs(error)>.02*.8
            expected=[10+(j+1)*delta for j in range(len(rr))] if policy_emits else []
            expected_wire=[float(('%.6f' if args.ros=='1' else '%.2f')%x) for x in expected]
            actual=[float(c['action'].split('=',1)[1]) for c in cc if c['action'].startswith('freq=')]
            passed=bool(rr) and len(actual)==len(cc)==len(expected_wire) and all(abs(a-b)<=1e-6 for a,b in zip(actual,expected_wire))
            row={'case':name,'target':target,'current':current,'start':start,'responses':len(rr),'commands':cc,'expected_wire_characterization':expected_wire,'characterization_matches':passed}
            result['cases'].append(row);log(dict(row,event='case_result'))
        result['complete']=True;result['characterization_matches']=all(c['characterization_matches'] for c in result['cases'])
    except Exception as exc:result['error']=repr(exc);result['characterization_matches']=False
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGINT);deadline=now()+5
                while p.poll() is None and now()<deadline:time.sleep(.1)
                if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
                p.wait()
        if node is not None:node.destroy_node();rclpy.shutdown()
        trace.close()
        for f in handles:f.close()
        result['python']=sys.version
        result['limits']=['Characterization of each implementation, not a common acceptance oracle or migration approval.','DataAccess and Engine services are doubles; no real reliability estimation, planning, logger, adapter or sensor effect.','No commands is interpreted only with positive-control commands and recorded service activity.']
        with open(os.path.join(out,'resultados.json'),'w') as f:json.dump(result,f,indent=2)
    print(out);print('complete=%s characterization_matches=%s'%(result['complete'],result['characterization_matches']))
    return 0 if result['complete'] and result['characterization_matches'] else 1
if __name__=='__main__':sys.exit(main())
