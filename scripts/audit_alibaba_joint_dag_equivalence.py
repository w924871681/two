"""Post-P7, pre-heldout equivalence and timing gate for Alibaba joint-DAG reuse."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,subprocess,time
import pandas as pd
from core.protocol import ROOT,save_json
from core.freeze import hash_file
from core.engine import run
from core.joint_dag import run_joint,CacheBundle
from scripts.run_calibration import calibration_definition
from scripts.audit_joint_dag_equivalence import history_catalog,enrich_reference,compare_frames

CASES=[('five_clean','clean',0.,[0,1,24,199,399]),('twenty_mixed','mixed',.1,list(range(0,400,20)))]

def main():
    assert not (ROOT/'results/heldout').exists(),'Alibaba reuse gate must finish before heldout generation/access'
    candidate,_,_,centers,jobs=calibration_definition('alibaba');center=centers[0];records=[];total_ref=0.;total_dag=0.
    for name,kind,alpha,policies in CASES:
        catalog=history_catalog(center,kind,alpha);refs=[];start=time.perf_counter()
        for policy in policies:
            method,settings=jobs[policy]
            d=pd.DataFrame(run(center,7311,method,kind,alpha,cfg={**candidate,**settings,'calibration_candidate_cache':True,'calibration_evidence_cache':True},
                run_id=f'alibaba_equivalence_reference_{name}_{policy}'))
            refs.append(enrich_reference(d,policy,catalog))
        reference=pd.concat(refs,ignore_index=True);ref_s=time.perf_counter()-start;plist=[{'policy':p,**jobs[p][1]} for p in policies]
        start=time.perf_counter();result,metrics,stages=run_joint(center,7311,plist,kind,alpha,cache=CacheBundle(),use_l1=True,use_l2=True,
            run_id=f'alibaba_equivalence_dag_{name}');dag_s=time.perf_counter()-start
        dag=pd.concat([pd.DataFrame(result[p]) for p in policies],ignore_index=True);comparison=compare_frames(reference,dag)
        records.append({'name':name,'center':center,'policies':len(policies),'reference_wall_s':ref_s,'joint_dag_wall_s':dag_s,
            'speedup':ref_s/dag_s,'comparison':comparison,'cache_metrics':metrics});total_ref+=ref_s;total_dag+=dag_s
    speedup=total_ref/total_dag;assert speedup>=1.3,'Alibaba joint DAG did not clear the 30% adoption threshold'
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();impl={'status':'approved_for_formal_p6','git_sha':sha,
        'joint_dag_sha256':hash_file(ROOT/'core/joint_dag.py'),'workers':2,'partition':'complete center x condition x seed workload',
        'domain':'alibaba','created_at':datetime.datetime.now().isoformat(),'heldout_started':False}
    save_json(ROOT/'audits/alibaba_joint_dag_implementation.json',impl)
    save_json(ROOT/'audits/alibaba_joint_dag_equivalence.json',{'status':'passed','cases':records,'aggregate_speedup':speedup,
        'scientific_structure':'same lifecycle executor with domain-local Timeline data and cache keys','adoption_threshold':1.3,'heldout_accessed':False})
    print(f'Alibaba joint-DAG equivalence PASS; aggregate speedup {speedup:.2f}x',flush=True)

if __name__=='__main__':main()
