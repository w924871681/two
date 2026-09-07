"""Fail-closed, resumable execution queue. Logs exceptions without silently retrying."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,subprocess,traceback,datetime,hashlib,os,time
from core.protocol import ROOT,save_json
from core.freeze import hash_file

def command(script):
    print('START',script,datetime.datetime.now().isoformat(),flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)

def code_manifest():
    return {str(p.relative_to(ROOT)).replace('\\','/'):hash_file(p) for directory in ['core','scripts','vendor'] for p in sorted((ROOT/directory).glob('*.py'))}

def main():
    lock=ROOT/'logs/runner.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    try:
        files=code_manifest();manifest=ROOT/'audits/execution_code_manifest.json'
        if manifest.exists():assert json.loads(manifest.read_text())['files']==files,'code changed since execution; audit provenance before resuming'
        else:save_json(manifest,{'files':files,'created_at':datetime.datetime.now().isoformat()})
        command('verify_repository.py')
        command('audit_legacy_pools.py')
        from scripts.run_development import main as development
        development()
        from scripts.run_calibration import main as calibration
        calibration()
        command('verify_repository.py')
        command('audit_preheldout.py')
        # A formal freeze may only be created after the complete preregistration and audits.
        readiness=json.loads((ROOT/'audits/heldout_readiness.json').read_text())
        assert readiness['status']=='approved_by_implementation_audit',readiness
        files=code_manifest()
        for p in (ROOT/'configs').glob('*'):
            if p.is_file():files[str(p.relative_to(ROOT)).replace('\\','/')]=hash_file(p)
        files['pool_manifest.json']=hash_file(ROOT/'pool_manifest.json')
        save_json(ROOT/'audits/final_freeze.json',{'status':'ready_for_heldout','created_at':datetime.datetime.now().isoformat(),'files':files})
        command('run_heldout.py')
        command('run_alibaba.py')
        command('summarize.py')
        command('derived_metrics.py')
        save_json(ROOT/'logs/execution_status.json',{'phase':'P14 tables generated','heldout_started':True,'remaining':['P15 figure QA','P16 final reproducibility audit']})
    except Exception:
        error=traceback.format_exc();print(error,flush=True)
        save_json(ROOT/'logs/execution_failure.json',{'time':datetime.datetime.now().isoformat(),'error':error,'status':'STOPPED_NO_AUTOMATIC_RETRY'})
        raise
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
