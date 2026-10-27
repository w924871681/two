"""Prepare isolated engineering and explicit experiment matrices before data generation."""
from common import *
import shutil,ast

def main():
    assert not (ROOT/'BOOTSTRAP_RECEIPT.json').exists()
    for d in ('progress','process','engineering/throughput','engineering/throughput_v3','assets','reports','E0_MAIN_TABLES','E0_FIGURE_SOURCE_DATA'):(ROOT/d).mkdir(parents=True,exist_ok=True)
    STORAGE.mkdir(exist_ok=True)
    task=Path('C:/Users/LOCAL_USER/.codex/attachments/0f78323c-192f-438a-8972-710c5b5422d6/已粘贴的文本.txt')
    shutil.copyfile(task,ROOT/'TASKBOOK_ZH.txt')
    shutil.copyfile(PRIOR/'engineering/resource_floor_v6/dispatch.py',ROOT/'engineering/throughput/dispatch.py')
    shutil.copyfile(PRIOR/'engineering/resource_floor_v6/RESOURCE_POLICY.json',ROOT/'engineering/throughput/RESOURCE_POLICY.json')
    shutil.copyfile(PRIOR/'engineering/throughput_v3/tuner.py',ROOT/'engineering/throughput_v3/tuner.py')
    shutil.copyfile(PRIOR/'dynamic_worker_resources_v2.py',ROOT/'dynamic_worker_resources_v2.py')
    (ROOT/'r_common.py').write_text('from common import *\n',encoding='utf8')
    dispatch=ROOT/'engineering/throughput/dispatch.py'
    src=dispatch.read_text(encoding='utf8').replace("runtime_dispatch='RESOURCE_FLOOR_V6'","runtime_dispatch='COVERAGE_THROUGHPUT_V1'")
    # If a worker raises, stop submission and preserve all naturally finishing jobs.
    dispatch.write_text(src,encoding='utf8');ast.parse(src)
    atomic(ROOT/'STORAGE_POLICY.json',dict(metadata_root=str(ROOT),large_artifact_root=str(STORAGE),disk_reserve_bytes=2*2**30,original_assets_readonly=True))
    rows=[]
    E1=['JOINT__l3__m0','RECENT_MEAN__g12','MWU_MEAN__g04','DUAL_MEAN__g12','RAVM_ORIGINAL','ALWAYS_FT','HUBER_FT','FROZEN']
    E2=E1[:6]
    for kind in ('mixed','persistent_bias','replay'):
        for alpha in (.05,.10,.20):rows.append(dict(stage='E1',condition=f'{kind}_a{alpha:.2f}',centers='64000-64023',seeds='7311,7312,7313',architecture='GRU',horizon=1,methods=','.join(E1),streams='corrupted',trajectories=576,stages=13824,location='both' if kind=='mixed' else 'verification_only',status='PREFLIGHT_PENDING'))
    for arch in ('MLP','TCN','GRU'):
        for h in (1,4):
            for stream in ('clean','mixed'):rows.append(dict(stage='E2',condition=f'{arch}_H{h}_{stream}',centers='64100-64123',seeds='7311,7312,7313',architecture=arch,horizon=h,methods=','.join(E2),streams=stream,trajectories=432,stages=10368,location='both',status='PREFLIGHT_PENDING'))
    save_csv(ROOT/'02_EXPERIMENT_MATRIX.csv',rows)
    candidate=read(PRIOR/'DEVCAL_SELECTED_LOCK.json')['candidate']
    atomic(ROOT/'01_COVERAGE_PROTOCOL_LOCK.json',dict(status='PREFLIGHT_SPECIFICATION_NOT_SCIENCE_EXECUTION_SEAL',taskbook_sha256=sha(task),
        candidate=candidate,gate_formula='d < 0 AND d + lambda * max(parent_recent_verification_mean_loss,1e-12) * (p-0.2) <= -margin',
        lambda_value=candidate['weight'],margin=candidate['threshold'],recalibration=False,replay_main_final=False,
        E1=dict(centers=list(range(64000,64024)),seeds=[7311,7312,7313],trajectories=5184,stage_rows=124416,candidate_upper=6220800,warmup_upper=3600,total_upper=6224400),
        E2=dict(centers=list(range(64100,64124)),seeds=[7311,7312,7313],trajectories=5184,stage_rows=124416,candidate_upper=6220800,warmup_upper=21600,total_upper=6242400),
        E3=dict(priority='highest',stages_and_budget='LOCK_AFTER_ORIGINAL_PROCESSOR_AUTHENTICATION'),
        E4=dict(missing_asset_behavior='BLOCKED_ASSET; no invented weights'),
        startup_ram_bytes=2*2**30,worker_ram_floor_bytes=1610612736,negative_result_stops_other_independent_stages=False,
        no_periodic_llm_supervision=True,progress_publish_seconds=1,checkpoint='on completed work unit; no 15-minute logger',
        matrix_sha256=sha(ROOT/'02_EXPERIMENT_MATRIX.csv')))
    atomic(ROOT/'05_BUDGET_PRECHECK.json',dict(status='PARTIAL_PRECHECK',E1_candidate_max=6220800,E1_warmup_max=3600,E1_actual_expected_with_frozen_zero=5446800,
        E2_candidate_max=6220800,E2_warmup_max=21600,E3='NOT_YET_AUTHENTICATED',E4='NOT_YET_AUTHENTICATED',E5_cost_repeat_budget='NOT_YET_LOCKED',
        note='E1 Frozen consumes zero candidate SGD; stated budget is an upper bound, not fictitious actual cost. No optimizer update before execution seal.'))
    for name in ('PREFLIGHT','E0','E1','E2','E3','E4','E5','DELIVERY'):stage(name,'PENDING')
    state(status='PREPARED',phase='PREFLIGHT',work='资产与协议核验',completed=0,total=0,unit='项',actual_sgd_steps=0,no_periodic_llm_supervision=True)
    atomic(ROOT/'BOOTSTRAP_RECEIPT.json',dict(status='PREPARED',at_unix=time.time(),taskbook_sha256=sha(task),prior_root=str(PRIOR),old_assets_modified=False,
        engineering_files_sha256={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.py')}))
    print(json.dumps(dict(root=str(ROOT),storage=str(STORAGE),status='PREPARED'),ensure_ascii=False))
if __name__=='__main__':main()
