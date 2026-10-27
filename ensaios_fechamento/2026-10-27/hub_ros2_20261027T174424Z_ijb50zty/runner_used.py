#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Controlled hub-only experiment. Python 2.7 (Melodic) or Python 3 (Jazzy).
No patient or real sensor node may share the isolated graph.
"""
from __future__ import print_function
import argparse, ctypes, datetime, hashlib, json, math, os, signal, socket, subprocess, sys, tempfile, time, threading, shutil

class Timespec(ctypes.Structure):
    _fields_=[('seconds',ctypes.c_long),('nanoseconds',ctypes.c_long)]
libc=ctypes.CDLL(None, use_errno=True)
def now():
    t=Timespec()
    if libc.clock_gettime(1,ctypes.byref(t)) != 0: raise OSError('clock_gettime')
    return t.seconds+t.nanoseconds/1e9
TYPES=['thermometer','ecg','oximeter','abps','abpd','glucosemeter']
FIELDS=['trm','ecg','oxi','abps','abpd','glc']
PHASES=[('baixo',[10,20,20,20,20,20],20.0),('alto',[90,20,20,20,20,20],90.0),('recuperado',[10,20,20,20,20,20],20.0)]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ros',choices=['1','2'],required=True)
    ap.add_argument('--output',default='campanhas_fechamento')
    ap.add_argument('--repeticoes',type=int,default=3)
    args=ap.parse_args()
    if args.repeticoes<1:ap.error('repeticoes must be positive')
    if not os.path.isdir(args.output):os.makedirs(args.output)
    out=tempfile.mkdtemp(prefix='hub_ros'+args.ros+'_'+datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')+'_',dir=args.output)
    shutil.copy2(__file__,os.path.join(out,'runner_used.py'))
    processes=[]; handles=[]; rows=[]; lock=threading.Lock(); node=None; result={'ros':args.ros,'boundary':'six synthetic sensor topics -> hub output','frequency_hz':6,'repetitions':args.repeticoes,'phases':[],'complete':False}
    trace=open(os.path.join(out,'trace.jsonl'),'w')
    def log(record):
        with lock:
            trace.write(json.dumps(record)+'\n');trace.flush()
    def snapshot(path):
        path=os.path.realpath(path)
        if not os.path.isfile(path):raise RuntimeError('Missing source '+path)
        digest=hashlib.sha256(open(path,'rb').read()).hexdigest()
        result.setdefault('source_sha256',{})[path]=digest
        if path.endswith(('.py','.cpp','.hpp')):
            dest=os.path.join(out,'sources');
            if not os.path.isdir(dest):os.makedirs(dest)
            shutil.copy2(path,os.path.join(dest,digest+'_'+os.path.basename(path)))
    def spawn(command):
        log({'event':'command','argv':command})
        f=open(os.path.join(out,'process_%d.log'%len(processes)),'w');handles.append(f)
        p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,preexec_fn=os.setsid);processes.append(p);return p
    def callback(msg):
        r={'event':'output','monotonic':now(),'state':float(msg.patient_status),'data':[float(getattr(msg,f+'_data')) for f in FIELDS],'risk':[float(getattr(msg,f+'_risk')) for f in FIELDS]}
        with lock:rows.append(r)
        log(r)
    try:
        if args.ros=='1':
            import rospy,rosgraph,rospkg,roslib.packages
            rp=rospkg.RosPack()
            result['ros_environment']={key:os.environ.get(key) for key in
                ['ROS_DISTRO','ROS_PACKAGE_PATH','CMAKE_PREFIX_PATH','PYTHONPATH']}
            try:
                component_path=rp.get_path('component')
                library_path=rp.get_path('libbsn')
            except rospkg.ResourceNotFound as exc:
                raise RuntimeError('ROS 1 workspace package unavailable: %s. Source /opt/ros/melodic/setup.bash and the compiled bsn2/devel/setup.bash in this terminal; verify rospack find component.' % exc)
            executables=roslib.packages.find_node('component','g4t1') or []
            if not executables:
                raise RuntimeError('Package component found, but executable g4t1 unavailable. Check the compiled workspace overlay.')
            from messages.msg import SensorData,TargetSystemData
            from archlib.msg import Event, Status, EnergyStatus
            # A fresh master prevents interference with other campaigns.
            s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
            os.environ['ROS_MASTER_URI']='http://127.0.0.1:%d'%port
            spawn(['roscore','-p',str(port)])
            for rel in ['src/g4t1/G4T1.cpp','src/CentralHub.cpp']:
                snapshot(os.path.join(component_path,rel))
            snapshot(os.path.join(library_path,'src/processor/Processor.cpp'))
            for executable in executables:snapshot(executable)
            deadline=now()+60
            while True:
                try:rosgraph.Master('/controlled_probe').getPid();break
                except Exception:
                    if now()>deadline:raise RuntimeError('ROS master not ready')
                    time.sleep(.1)
            rospy.init_node('controlled_probe',anonymous=True,disable_signals=True)
            rospy.set_param('/frequency',6.0)
            # The legacy component waits for diagnostic subscribers in setUp.
            # These observers do not produce sensor inputs or adaptation commands.
            diagnostics=[rospy.Subscriber(topic,kind,lambda msg:None,queue_size=100)
                for topic,kind in [('/collect_event',Event),('/collect_status',Status),('/collect_energy_status',EnergyStatus)]]
            output_sub=rospy.Subscriber('/TargetSystemData',TargetSystemData,callback,queue_size=100)
            pubs=[rospy.Publisher('/'+t+'_data',SensorData,queue_size=10) for t in TYPES]
            spawn(['rosrun','component','g4t1'])
            def spin(dt):time.sleep(dt)
            def connected():return all(p.get_num_connections()>0 for p in pubs) and output_sub.get_num_connections()>0
            def message(t,value,risk):
                m=SensorData();m.type=t;m.data=value;m.risk=float(risk);m.batt=100.0;return m
        else:
            os.environ['ROS_DOMAIN_ID']='91'
            import rclpy
            import importlib
            for name in ['central_hub.central_hub','central_hub.components.data_fusion','central_hub.components.sensor_data_handler','central_hub.components.publishers','shared_components.core.config_manager_base']:
                snapshot(importlib.import_module(name).__file__)
            from rclpy.node import Node
            from bsn_interfaces.msg import SensorData,TargetSystemData
            rclpy.init(args=[]);node=Node('controlled_probe')
            node.create_subscription(TargetSystemData,'/target_system_data',callback,100)
            pubs=[node.create_publisher(SensorData,'/sensor_data/'+t,10) for t in TYPES]
            spawn(['ros2','run','central_hub','emergency_detection','--ros-args','-p','frequency:="6.0"','-p','component:=central_hub','-p','enable_adaptation:=false'])
            def spin(dt):rclpy.spin_once(node,timeout_sec=dt)
            def connected():return all(p.get_subscription_count()>0 for p in pubs) and node.count_publishers('/target_system_data')>0
            def message(t,value,risk):
                m=SensorData();m.sensor_id=t;m.sensor_type=t;m.sensor_datapoint=value;m.risk=float(risk);m.risk_level='high' if risk>=66 else 'low';m.battery_level=100.0;return m
        deadline=now()+90
        # ROS 1 does not publish before receiving its first input. Readiness
        # therefore requires connected interfaces, not a spontaneous output.
        while not connected():
            if processes[-1].poll() is not None:raise RuntimeError('Hub exited during readiness; see process log')
            if now()>deadline:raise RuntimeError('Hub input connections/output not ready')
            spin(.05)
        log({'event':'ready','criterion':'six input connections and output publisher connected','monotonic':now()})
        # Require our six inputs to have no competing producer.
        if args.ros=='2':
            assert all(node.count_publishers('/sensor_data/'+t)==1 for t in TYPES),'Competing sensor publisher'
            endpoints=node.get_publishers_info_by_topic('/target_system_data')
            owners=[(e.node_namespace,e.node_name) for e in endpoints]
            log({'event':'hub_publisher_endpoints','owners':owners})
            # The hub creates publishers during construction and configuration.
            # Multiple endpoints owned by the same launched node are not another producer.
            assert owners and set(owners)=={('/','central_hub_node')},'Unexpected hub publisher owners: '+repr(owners)
        else:
            published=dict(rosgraph.Master(rospy.get_name()).getSystemState()[0])
            assert all(published.get('/'+t+'_data')==[rospy.get_name()] for t in TYPES),'Competing sensor publisher'
            assert len(published.get('/TargetSystemData',[]))==1,'Competing hub publisher'
        for repeat in range(args.repeticoes):
            for phase,(name,risks,expected) in enumerate(PHASES):
                marker=1000.0+repeat*100+phase*10
                data=[marker+i for i in range(6)]
                start=now();record={'repeat':repeat,'phase':name,'risks':risks,'data_markers':data,'expected':expected,'start':start}
                log(dict(record,event='input_batch'))
                for t,p,v,r in zip(TYPES,pubs,data,risks):p.publish(message(t,v,r))
                # No retry: retain every output and every missed response.
                deadline=start+5.0
                while now()<deadline:spin(min(.05,max(0,deadline-now())))
                with lock:captured=[r for r in rows if start<=r['monotonic']<=deadline]
                matched=[r for r in captured if r['data']==data and r['risk']==list(map(float,risks))]
                correct=[r for r in matched if math.isfinite(r['state']) and abs(r['state']-expected)<=1e-9] if hasattr(math,'isfinite') else [r for r in matched if not math.isnan(r['state']) and not math.isinf(r['state']) and abs(r['state']-expected)<=1e-9]
                stable=[r for r in captured if r['monotonic']>=start+2.0]
                passed=len(stable)>=3 and all(r['data']==data and r['risk']==list(map(float,risks)) and abs(r['state']-expected)<=1e-9 for r in stable)
                latency=correct[0]['monotonic']-start if correct else None
                record.update(passed=passed,samples=len(captured),stable_samples=len(stable),latency_s=latency,within_250ms=latency is not None and 0<=latency<=.250)
                result['phases'].append(record);log(dict(record,event='phase_result'))
        result['complete']=True;result['passed']=all(p['passed'] for p in result['phases'])
    except Exception as e:
        result['error']=repr(e);result['passed']=False
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGINT);deadline=now()+5
                while p.poll() is None and now()<deadline:time.sleep(.1)
                if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
                p.wait()
        if node is not None:node.destroy_node();rclpy.shutdown()
        for f in handles:f.close()
        trace.close()
        result['script_sha256']=hashlib.sha256(open(os.path.join(out,'runner_used.py'),'rb').read()).hexdigest()
        result['python']=sys.version;result['command']=sys.argv
        result['limits']=['No physical sensor/patient chain. Latency is batch-publication to correlated hub output.', '2s settling and 5s window are test protocol, not system requirements.','No retries; 250ms is reported separately, not included in functional pass.']
        with open(os.path.join(out,'resultados.json'),'w') as f:json.dump(result,f,indent=2)
    print(out);print('complete=%s passed=%s'%(result['complete'],result['passed']))
    return 0 if result['complete'] and result['passed'] else 1
if __name__=='__main__':sys.exit(main())
