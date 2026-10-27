"""Single durable owner; no LLM scheduler or periodic model wakeups."""
from common import *
import psutil,traceback
def main():
    me=psutil.Process();atomic(ROOT/'process/OWNER_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time()))
    from preflight import run
    if not (ROOT/'PREFLIGHT_RECEIPT.json').exists():run()
    from readonly_e0 import run as e0
    if not (ROOT/'E0_RECEIPT.json').exists():e0()
    # Only a sealed, authenticated extension is admitted. Never import a half-written runner.
    if not (ROOT/'EXECUTION_READY.json').exists():
        state(status='AWAITING_IMPLEMENTATION_SEAL',phase='ENGINEERING',work='等待扩展接口一致性审计与执行封存',active_workers=0)
        atomic(ROOT/'process/READONLY_PHASE_COMPLETE.json',dict(status='READONLY_PHASE_COMPLETE',at_unix=time.time(),optimizer_steps=0))
        return
    from coverage_execution import run as execute
    execute()
if __name__=='__main__':
    try:main()
    except BaseException:
        atomic(ROOT/'process/OWNER_FAILURE.json',dict(error=traceback.format_exc(),at_unix=time.time(),automatic_training_retry=False))
        state(status='FAILED',error=traceback.format_exc(),active_workers=0);raise
