from common import *
import psutil,traceback,sys
sys.path.insert(0,str(ROOT/'engineering/throughput'))
from dispatch import execute
me=psutil.Process();atomic(ROOT/'process/ASSET_OWNER_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time(),kind='READONLY_EXTERNAL_AUTH'))
atomic(ROOT/'process/OWNER_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time(),kind='READONLY_EXTERNAL_AUTH'))
for name in ('E3','E4'):
    try:
        if name=='E3':
            from external_auth import authenticate
        else:
            # Torch startup obeys the separate experiment startup floor.
            while psutil.virtual_memory().available<2*2**30:
                state(status='WAITING_FOR_STARTUP_RAM',phase='ASSET_AUTH',work='温度模型身份认证等待2 GiB启动内存',completed=0,total=1,unit='资产组');time.sleep(3)
            from e4_assets import authenticate
        execute([name],lambda _:authenticate(),name+'_AUTHENTICATION',cpu=True)
    except BaseException:
        atomic(ROOT/f'assets/{name}_AUTH_FAILURE.json',dict(status='BLOCKED_AUTHENTICATION',error=traceback.format_exc(),optimizer_steps=0,at_unix=time.time()))
        stage(name,'BLOCKED_AUTHENTICATION',detail=traceback.format_exc())
atomic(ROOT/'process/ASSET_OWNER_COMPLETE.json',dict(at_unix=time.time(),optimizer_steps=0))
