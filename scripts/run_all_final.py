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

def git_sha():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def update_report(phase,details):
    path=ROOT/'FINAL_EXPERIMENT_REPORT.md';text=path.read_text(encoding='utf-8');start='<!-- FORMAL_EXECUTION_STATUS_START -->';end='<!-- FORMAL_EXECUTION_STATUS_END -->'
    block=f'''{start}\n## 正式执行状态\n\n更新时间：{datetime.datetime.now().isoformat()}\n\n阶段：**{phase}**\n\n{details}\n{end}'''
    if start in text:text=text[:text.index(start)]+block+text[text.index(end)+len(end):]
    else:text=text.rstrip()+'\n\n'+block+'\n'
    path.write_text(text,encoding='utf-8')

def assert_p0_p5_reuse():
    dev=list((ROOT/'results/development').glob('*.csv'));trajectories=[p for p in dev if p.name!='development_summary.csv']
    assert len(trajectories)==1560 and (ROOT/'results/development/development_summary.csv').exists()
    for name in ['frozen_candidate_config.yaml','frozen_baseline_config.yaml','calibration_protocol.yaml']:
        p=ROOT/'configs'/name;assert p.exists() and hash_file(p)==p.with_suffix('.sha256').read_text().strip(),name
    from core.protocol import POOLS
    for seed in [7311,7312,7313]:
        assert (ROOT/f'checkpoints/source_GRU_H1_{seed}.pt').exists()
        for center in POOLS['calibration']:
            assert (ROOT/f'checkpoints/M0_GRU_H1_{seed}_{center}.pt').exists()

def main():
    lock=ROOT/'logs/runner.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    (ROOT/'runner.pid').write_text(str(os.getpid()))
    try:
        files=code_manifest();manifest=ROOT/'audits/execution_code_manifest.json'
        if manifest.exists():assert json.loads(manifest.read_text())['files']==files,'code changed since execution; audit provenance before resuming'
        else:save_json(manifest,{'files':files,'created_at':datetime.datetime.now().isoformat()})
        command('verify_repository.py')
        command('audit_legacy_pools.py')
        assert_p0_p5_reuse()
        identity={'status':'approved_for_formal_p6','git_sha':git_sha(),'joint_dag_sha256':hash_file(ROOT/'core/joint_dag.py'),
            'execution_code_manifest_sha256':hash_file(manifest),'workers':2,'partition':'complete center x condition x seed workload',
            'created_at':datetime.datetime.now().isoformat(),'heldout_started':False}
        save_json(ROOT/'audits/formal_p6_implementation.json',identity)
        update_report('P6 正式 joint-policy DAG 已启动',f"实现提交：`{identity['git_sha']}`；joint DAG SHA-256：`{identity['joint_dag_sha256']}`；2 个完整 workload worker；P0–P5 仅复用。")
        from scripts.run_calibration_joint_dag_parallel import main as calibration
        calibration('synthetic',2)
        update_report('P7 calibration aggregation 与 commit configuration 冻结完成','正式 P6 的 48,600 条完整轨迹已生成；正在执行 heldout 前科学、泄漏与配置审计。')
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
        update_report('P7 全部审计 PASS，P8 heldout 已获准启动','`heldout_readiness.json` 已通过，正式冻结清单已生成；随后只按冻结配置执行 heldout。')
        command('run_heldout.py')
        update_report('P8 synthetic heldout 完成','已完成冻结配置下的 synthetic heldout，继续执行后续预注册队列。')
        command('run_alibaba.py')
        command('summarize.py')
        command('derived_metrics.py')
        save_json(ROOT/'logs/execution_status.json',{'phase':'P14 tables generated','heldout_started':True,'remaining':['P15 figure QA','P16 final reproducibility audit']})
    except Exception:
        error=traceback.format_exc();print(error,flush=True)
        save_json(ROOT/'logs/execution_failure.json',{'time':datetime.datetime.now().isoformat(),'error':error,'status':'STOPPED_NO_AUTOMATIC_RETRY'})
        raise
    finally:lock.unlink(missing_ok=True);(ROOT/'runner.pid').unlink(missing_ok=True)

if __name__=='__main__':main()
