"""Resume the audited queue after a completed P6/P7 without rerunning calibration."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,json,os,traceback
from core.protocol import ROOT,POOLS,save_json
from core.freeze import hash_file
from scripts.run_all_final import command,code_manifest,git_sha,update_report

def main():
    lock=ROOT/'logs/runner.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    (ROOT/'runner.pid').write_text(str(os.getpid()))
    try:
        assert not (ROOT/'results/heldout').exists(),'heldout boundary already opened'
        assert sum(1 for _ in (ROOT/'results/calibration').glob('policy*.csv'))==405*20*3*2
        frozen=ROOT/'configs/frozen_commit_config.yaml';assert frozen.exists() and hash_file(frozen)==frozen.with_suffix('.sha256').read_text().strip()
        provenance=json.loads((ROOT/'audits/calibration_selection_provenance.json').read_text());assert provenance['status']=='passed' and provenance['frozen_config_sha256']==hash_file(frozen)
        old=ROOT/'logs/execution_failure.json'
        if old.exists():old.replace(ROOT/'logs'/f'execution_failure_pre_resume_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        update_report('P7 后恢复：补齐 Alibaba source-only 前置资产并重跑 pre-heldout audit','P6/P7 结果与冻结哈希已复核；不会重跑 calibration，也不会在审计通过前读取 heldout。')
        command('verify_repository.py');command('audit_preheldout.py')
        readiness=json.loads((ROOT/'audits/heldout_readiness.json').read_text());assert readiness['status']=='approved_by_implementation_audit'
        files=code_manifest()
        for p in (ROOT/'configs').glob('*'):
            if p.is_file():files[str(p.relative_to(ROOT)).replace('\\','/')]=hash_file(p)
        files['pool_manifest.json']=hash_file(ROOT/'pool_manifest.json')
        save_json(ROOT/'audits/final_freeze.json',{'status':'ready_for_heldout','created_at':datetime.datetime.now().isoformat(),'git_sha':git_sha(),
            'formal_p6_git_sha':provenance['formal_p6_git_sha'],'files':files})
        update_report('P7 全部审计 PASS，P8 heldout 已获准启动','Final freeze 已生成；后续严格按冻结配置自动执行 P8–P16。')
        command('run_heldout.py');update_report('P8–P12 synthetic heldout 完成','Q1–Q5 原始结果完成，继续执行 Alibaba Q6。')
        command('run_alibaba.py');update_report('P13 Alibaba Q6 完成','直接迁移、域内 calibration 与诊断完成，继续执行 bootstrap 与最终输出。')
        command('summarize.py');command('derived_metrics.py');command('finalize_outputs.py');command('finalize_report.py');command('final_reproducibility_audit.py');command('finalize_report.py')
        save_json(ROOT/'logs/execution_status.json',{'phase':'P16 complete','heldout_started':True,'git_sha':git_sha(),'remaining':[],'completed_at':datetime.datetime.now().isoformat()})
        update_report('P16 完成','完整正式实验、图表、4,000 次中心聚类 bootstrap 与最终复现审计均已完成。')
    except Exception:
        error=traceback.format_exc();print(error,flush=True);save_json(ROOT/'logs/execution_failure.json',{'time':datetime.datetime.now().isoformat(),'error':error,'status':'STOPPED_NO_AUTOMATIC_RETRY'});raise
    finally:
        lock.unlink(missing_ok=True);(ROOT/'runner.pid').unlink(missing_ok=True)

if __name__=='__main__':main()
