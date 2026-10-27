"""Regression: completed last task must exit even when admission falls to zero."""
import sys,time,shutil,json
from pathlib import Path
from types import SimpleNamespace
META=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(META));sys.path.insert(0,str(META/'engineering/throughput'))
import dispatch
from common import atomic
fixture=META/'engineering/queue_tail_fixture';fixture.mkdir(exist_ok=True);(fixture/'progress').mkdir(exist_ok=True)
shutil.copyfile(META/'dynamic_worker_resources_v2.py',fixture/'dynamic_worker_resources_v2.py')
original_root=dispatch.ROOT;original_vm=dispatch.psutil.virtual_memory
dispatch.ROOT=fixture;floor=1610612736;available={'value':floor+64*2**20}
dispatch.psutil.virtual_memory=lambda:SimpleNamespace(available=available['value'],total=16*2**30)
start=time.monotonic()
try:
    def last_job(_):available['value']=floor-1;return 'completed'
    result=dispatch.execute([0],last_job,'QUEUE_TAIL_TEST',cpu=True)
    assert result==['completed'] and available['value']<floor and time.monotonic()-start<5
    assert dispatch.execute([],last_job,'EMPTY_QUEUE_TEST',cpu=True)==[]
    assert json.loads((fixture/'progress/QUEUE_TAIL_TEST_PROGRESS.json').read_text())['status']=='DONE'
finally:dispatch.ROOT=original_root;dispatch.psutil.virtual_memory=original_vm
atomic(META/'engineering/QUEUE_TAIL_REGRESSION.json',dict(status='PASS',optimizer_steps=0,last_result_finishes_under_below_floor_ram=True,empty_queue_finishes=True,fixture_only_no_real_resource_measurement=True,wall_seconds=time.monotonic()-start))
print('Queue tail completion below RAM floor: PASS')
