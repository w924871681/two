"""Successful optimizer-call accounting, block reservations and no blind replay."""
from common import *
import contextlib,threading
class Meter:
    def __init__(self,group,budget):
        import torch
        self.group=group;self.budget=budget;self.path=ROOT/'process'/f'{group}_SGD_CALL_ACCOUNTING.jsonl'
        self.lock=threading.RLock();self.tls=threading.local();self.calls={};self.actual={'warmup':0,'candidate':0};self.reserved={'warmup':0,'candidate':0}
        if self.path.exists():
            for line in self.path.read_text(encoding='utf8').splitlines():
                e=json.loads(line);key=e['call_id']
                if e['event']=='BEGIN':
                    assert key not in self.calls;self.calls[key]=dict(kind=e['kind'],count=0,closed=False);self.reserved[e['kind']]+=50
                elif e['event'] in ('DONE','FAILED_SCOPE'):
                    call=self.calls[key];assert not call['closed'];call.update(count=e['successful_steps'],closed=True);self.actual[call['kind']]+=call['count']
        self.uncertain=[k for k,v in self.calls.items() if not v['closed']]
        self.original=torch.optim.SGD.step;owner=self
        def step(optimizer,*args,**kwargs):
            import bridge
            kind=owner.tls.kind;identity=dict(owner.tls.identity,kind=kind,stage=0 if kind=='warmup' else bridge.TLS.science_stage)
            key=json.dumps(identity,sort_keys=True,separators=(',',':'))
            with owner.lock:
                if key not in owner.calls:
                    limit=owner.budget['warmup_steps' if kind=='warmup' else 'candidate_steps']
                    assert owner.reserved[kind]+50<=limit,'Budget exceeded before optimizer'
                    owner.append(dict(event='BEGIN',call_id=key,kind=kind,reserved_steps=50,identity=identity))
                    owner.calls[key]=dict(kind=kind,count=0,closed=False);owner.reserved[kind]+=50
                call=owner.calls[key];assert not call['closed'] and key not in owner.uncertain and call['count']<50,'No duplicate/unknown optimizer scope'
                owner.tls.active_key=key
            result=owner.original(optimizer,*args,**kwargs)
            with owner.lock:
                call['count']+=1;owner.actual[kind]+=1
                if call['count']==50:
                    owner.append(dict(event='DONE',call_id=key,kind=kind,successful_steps=50));call['closed']=True
            return result
        torch.optim.SGD.step=step
    def append(self,event):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a',encoding='utf8') as f:f.write(json.dumps(dict(**event,at_unix=time.time()))+'\n');f.flush();os.fsync(f.fileno())
    @contextlib.contextmanager
    def scope(self,kind,identity):
        self.tls.kind=kind;self.tls.identity=dict(identity,group=self.group);self.tls.active_key=None
        try:yield
        except BaseException:
            with self.lock:
                key=self.tls.active_key
                if key and key in self.calls and not self.calls[key]['closed']:
                    call=self.calls[key];self.append(dict(event='FAILED_SCOPE',call_id=key,kind=kind,successful_steps=call['count']));call['closed']=True
            raise
        finally:self.tls.kind=None
