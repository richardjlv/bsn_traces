#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Persist messages -> real DataAccess -> reopened status file. Python 2/3."""
from __future__ import print_function
import argparse,os,sys,json,csv,glob,time,socket,tempfile,datetime,shutil,hashlib,subprocess,signal
from validar_hub_controlado import now

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ros',choices=['1','2'],required=True);ap.add_argument('--output',default='campanhas_fechamento');args=ap.parse_args()
    root=os.path.abspath(args.output)
    if not os.path.isdir(root):os.makedirs(root)
    out=tempfile.mkdtemp(prefix='persistencia_ros'+args.ros+'_'+datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')+'_',dir=root)
    for f in [__file__,os.path.join(os.path.dirname(__file__),'validar_hub_controlado.py')]:shutil.copy2(f,out)
    result={'ros':args.ros,'boundary':'Persist Status -> real DataAccess -> reopened file','complete':False,'passed':False};processes=[];handles=[];node=None;logdir=None;before=set();expected=[]
    trace=open(os.path.join(out,'trace.jsonl'),'w')
    def log(r):trace.write(json.dumps(r)+'\n');trace.flush()
    def snapshot(f):
        f=os.path.realpath(f);h=hashlib.sha256(open(f,'rb').read()).hexdigest();result.setdefault('source_sha256',{})[f]=h
        if f.endswith(('.py','.cpp','.hpp')):shutil.copy2(f,os.path.join(out,h+'_'+os.path.basename(f)))
    def spawn(cmd,cwd=None):
        log({'event':'process','argv':cmd,'cwd':cwd});h=open(os.path.join(out,'process_%d.log'%len(processes)),'w');handles.append(h)
        p=subprocess.Popen(cmd,cwd=cwd,stdout=h,stderr=subprocess.STDOUT,preexec_fn=os.setsid);processes.append(p);return p
    def stop():
        for p in reversed(processes):
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGINT);deadline=now()+5
                while p.poll() is None and now()<deadline:time.sleep(.1)
                if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
                p.wait()
    def records():
        rows=[]
        for f in sorted(set(glob.glob(os.path.join(logdir,'status_*.log')))-before):
            with open(f,'r') as h:
                rows.extend(row for row in csv.reader(h) if len(row)==6 and row[3]==source)
        return rows
    try:
        if args.ros=='1':
            import rospy,rosgraph,rospkg,roslib.packages
            from archlib.msg import Persist
            base=rospkg.RosPack().get_path('repository');snapshot(os.path.join(base,'src/DataAccess.cpp'))
            binaries=roslib.packages.find_node('repository','data_access') or []
            if not binaries:raise RuntimeError('data_access executable unavailable; source compiled workspace')
            for f in binaries:snapshot(f)
            logdir=os.path.abspath(os.path.join(base,'../resource/logs'))
            if not os.path.isdir(logdir):os.makedirs(logdir)
            before=set(glob.glob(os.path.join(logdir,'status_*.log')))
            s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close();os.environ['ROS_MASTER_URI']='http://127.0.0.1:%d'%port
            spawn(['roscore','-p',str(port)]);deadline=now()+60
            while True:
                try:rosgraph.Master('/persistence_probe').getPid();break
                except Exception:
                    if now()>deadline:raise RuntimeError('master not ready')
                    time.sleep(.1)
            rospy.init_node('persistence_probe',disable_signals=True);rospy.set_param('/frequency',10.0)
            pub=rospy.Publisher('/persist',Persist,queue_size=100)
            process=spawn([binaries[0]])
            def spin(dt):time.sleep(dt)
            def ready():return pub.get_num_connections()>0
        else:
            os.environ['ROS_DOMAIN_ID']='93'
            import rclpy,importlib
            from rclpy.node import Node
            from bsn_interfaces.msg import Persist
            snapshot(importlib.import_module('adaptation.data_access.data_access').__file__)
            rclpy.init(args=[]);node=Node('persistence_probe');pub=node.create_publisher(Persist,'persist',100)
            logdir=os.path.join(out,'src/adaptation/resource/log')
            process=spawn(['ros2','run','adaptation','data_access','--ros-args','-p','frequency:=10.0'],cwd=out)
            def spin(dt):rclpy.spin_once(node,timeout_sec=dt)
            def ready():return pub.get_subscription_count()>0
        def pump(seconds):
            deadline=now()+seconds
            while now()<deadline:
                if process.poll() is not None:raise RuntimeError('DataAccess exited; see process log')
                spin(min(.05,max(0,deadline-now())))
        deadline=now()+60
        while not ready():
            if now()>deadline:raise RuntimeError('persist subscriber not ready')
            pump(.05)
        source='/probe_'+os.path.basename(out)
        for i in range(30):
            m=Persist();m.type='Status';m.source=source;m.target='/audit_%02d'%i;m.timestamp=100000+i;m.content='success' if i%2==0 else 'fail'
            row=['Status',str(i+1),str(m.timestamp),m.source,m.target,m.content];expected.append(row)
            log({'event':'input','monotonic':now(),'record':row});pub.publish(m);pump(.05)
        deadline=now()+15
        while len(records())<30 and now()<deadline:pump(.1)
        result['records_before_stop']=records();stop()
        actual=records();result.update(complete=True,passed=actual==expected,expected=expected,recovered=actual)
        log({'event':'reopened_after_stop','records':actual,'passed':result['passed']})
        dest=os.path.join(out,'recovered_logs');os.makedirs(dest)
        for f in sorted(set(glob.glob(os.path.join(logdir,'status_*.log')))-before):shutil.copy2(f,dest)
    except Exception as exc:result['error']=repr(exc)
    finally:
        stop()
        if node is not None:node.destroy_node();rclpy.shutdown()
        for h in handles:h.close()
        trace.close();result['python']=sys.version;result['log_directory']=logdir
        result['limits']=['Operational Status records, not physiological readings.','Direct Persist input bypasses logger and sensors.','Reopened filesystem file after process stop; no power-loss or fsync durability claim.','30 records exercise the configured flush threshold; partial buffers not assessed.']
        with open(os.path.join(out,'resultados.json'),'w') as h:json.dump(result,h,indent=2)
    print(out);print('complete=%s passed=%s'%(result['complete'],result['passed']))
    return 0 if result['complete'] and result['passed'] else 1
if __name__=='__main__':sys.exit(main())
