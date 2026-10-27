"""Loopback-only read-only coverage dashboard, sampled continuously."""
from common import *
from collections import deque
from urllib.parse import urlsplit
import argparse,http.server,psutil,threading,shutil
HISTORY={};MUTEX=threading.RLock()
def optional(name):
    try:return read(ROOT/name)
    except (OSError,ValueError):return {}
def snapshot():
    now=time.time();s=optional('progress/progress_state.json');w=optional('progress/WORKER_STATUS.json');stages=optional('progress/STAGES.json')
    vm=psutil.virtual_memory();identity=optional('process/OWNER_IDENTITY.json');alive=False
    try:
        p=psutil.Process(identity['pid']);alive=p.is_running() and abs(p.create_time()-identity['create_time'])<.02
    except (psutil.Error,KeyError):pass
    count=s.get('completed',0);total=s.get('total',0);key=(s.get('phase'),s.get('work'))
    samples=ROOT/'progress/RATE_SAMPLES.jsonl';events=[]
    if samples.exists():
        with samples.open('rb') as f:
            size=f.seek(0,2);f.seek(max(0,size-256*1024));tail=f.read().splitlines()
        for line in tail:
            try:
                row=json.loads(line)
                if (row.get('phase'),row.get('work'))==key and row['at']>=now-305:events.append((row['at'],row['completed']))
            except (ValueError,KeyError):pass
    with MUTEX:
        points=HISTORY.setdefault(key,deque());points.append((now,count))
        while points and points[0][0]<now-305:points.popleft()
        history=events if events else list(points)
        # Never label an hour-long polling gap as a five-minute window.
        span=now-history[0][0] if history else 0;delta=max(0,count-history[0][1]) if history else 0
        rate=delta/span if span>=20 and span<=305 else None
    live=alive and now-s.get('updated_unix',0)<30
    eta=(total-count)/rate if live and rate and total>count else None
    if total>0 and count>=total:eta=0
    passport=optional('00_ASSET_PASSPORT.json')
    counters=[optional(str(p.relative_to(ROOT)))for p in(ROOT/'process').glob('*_OPTIMIZER_PROGRESS.json')]
    actual=sum(sum(x.get('actual',{}).values())for x in counters);seal=optional('SCIENCE_EXECUTION.lock.json');budget=sum(x['total_steps']for x in seal.get('budgets',{}).values())
    if now-w.get('updated_unix',0)>10:w=dict(w,active_workers=0,worker_snapshot_stale=True)
    return dict(updated_unix=now,state=s,workers=w,stages=stages,owner=dict(**identity,alive=alive),
        recent_progress=dict(window_seconds=300,coverage_seconds=min(span,300),full_window=span>=300,
            rate_per_minute=rate*60 if rate is not None else None,eta_seconds=eta,completed=count,total=total,unit=s.get('unit','项'),
            live=live,estimate_scope='current work only; all later stages excluded'),
        memory=dict(available=vm.available,total=vm.total,percent=vm.percent,worker_floor=1610612736),
        assets=dict(status=passport.get('status'),external_CAS=passport.get('external_CAS'),models=len(passport.get('interfaces',{}).get('rows',{}))),
        main_final=dict(decision='FINAL_MAIN_PASS',previous_delivery_pass=True,zip_bytes=502660696,main_rerun=False),
        optimizer=dict(actual_latest_snapshot_steps=actual,registered_budget=budget,remaining_budget=max(0,budget-actual),uncertainty='latest durable worker snapshots; final accounting reconciles open optimizer scopes'),
        delivery=optional('delivery/PACKAGE_VERIFICATION.json'),storage_wait=optional('progress/STORAGE_WAIT.json'),
        no_periodic_llm_supervision=True)
class Server(http.server.ThreadingHTTPServer):allow_reuse_address=False
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/download/'):
            receipt=optional('delivery/PACKAGE_VERIFICATION.json');kind=path.rsplit('/',1)[-1]
            if receipt.get('status')!='PASS' or kind not in('review','full','report'):self.send_error(404,'No verified delivery');return
            if kind=='report':
                file=ROOT/'RAVM_JOINT_ALL_EXPERIMENTS_REPORT_ZH.md'
                if sha(file)!=receipt['report_sha256']:self.send_error(409,'Report changed after verification');return
            else:
                item=receipt[kind];file=Path(item['path'])
                if not file.is_file() or file.stat().st_size!=item['bytes']or file.stat().st_mtime_ns!=item['archive_mtime_ns']:self.send_error(409,'Package changed after verification');return
            self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Disposition','attachment; filename="'+file.name+'"');self.send_header('Content-Length',str(file.stat().st_size));self.end_headers()
            with file.open('rb')as f:shutil.copyfileobj(f,self.wfile,2**20)
            return
        if path=='/api/status':wire=json.dumps(snapshot(),ensure_ascii=False).encode('utf8');mime='application/json; charset=utf-8'
        elif path in ('/','/index.html'):wire=(ROOT/'dashboard.html').read_bytes();mime='text/html; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(wire)));self.end_headers();self.wfile.write(wire)
    def log_message(self,*a):pass
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8769);args=p.parse_args()
    me=psutil.Process();atomic(ROOT/f'process/DASHBOARD_{args.port}_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time(),port=args.port))
    Server(('127.0.0.1',args.port),Handler).serve_forever()
