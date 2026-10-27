"""One shot idle tool working-set reclaim; never terminate a process."""
from pathlib import Path
import psutil,ctypes,json,time
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[1]
def sample(p):return (p.create_time(),sum(p.cpu_times()[:2]),tuple(p.io_counters())[:4])
first={}
for p in psutil.process_iter(['name']):
    try:
        if p.info['name'].lower() not in ('node.exe','node_repl.exe') or p.children() or time.time()-p.create_time()<300:continue
        cwd=p.cwd().lower();cmd=p.cmdline()
        if not (cwd.endswith('\\.codex\\code-review-plugin') or '\\codex-app-tools\\' in cwd or p.info['name'].lower()=='node_repl.exe'):continue
        first[p.pid]=dict(identity=sample(p),rss=p.memory_info().rss)
    except psutil.Error:pass
before=psutil.virtual_memory().available
print(json.dumps(dict(idle_candidates=len(first),available_before=before)),flush=True)
time.sleep(30)
k=ctypes.WinDLL('kernel32',use_last_error=True);a=ctypes.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE];a.EmptyWorkingSet.argtypes=[wintypes.HANDLE];a.EmptyWorkingSet.restype=wintypes.BOOL
actions=[]
for pid,s in first.items():
    h=None
    try:
        p=psutil.Process(pid)
        if sample(p)!=s['identity'] or p.children():continue
        h=k.OpenProcess(0x0100|0x0400,False,pid)
        if h and a.EmptyWorkingSet(h):actions.append(dict(pid=pid,created=s['identity'][0],rss_before=s['rss'],rss_after=p.memory_info().rss))
    except psutil.Error:pass
    finally:
        if h:k.CloseHandle(h)
receipt=dict(method='EmptyWorkingSet only',terminated_processes=[],idle_sample_seconds=30,actions=actions,available_before=before,available_after=psutil.virtual_memory().available,at_unix=time.time())
(ROOT/'process/IDLE_WORKING_SET_RECLAIM.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(dict(reclaimed_instances=len(actions),available_after=receipt['available_after'])),flush=True)
