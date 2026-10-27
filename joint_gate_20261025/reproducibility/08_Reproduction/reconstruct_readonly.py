"""Recompute published summaries/plots from delivered CSVs, never train models."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'05_Scientific_Traceability/data';O=Path(__file__).parent/'reconstructed';O.mkdir(exist_ok=True)
J='JOINT__l3__m0';DU='DUAL_MEAN__g12';eta=5.6036475532487204e-5
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
main=rows(D/'E0_MAIN_TABLES/RESULTS_BY_ARM.csv');cent=rows(D/'E0_MAIN_TABLES/RESULTS_BY_CENTER.csv')
for r in main:
 v=[float(c['balanced_clean_mixed_mse'])for c in cent if c['arm']==r['arm']];assert len(v)==32 and abs(np.mean(v)-float(r['balanced_mse']))<1e-14
joint=next(r for r in main if r['arm']==J);dual=next(r for r in main if r['arm']==DU)
improvement=100*(1-float(joint['balanced_mse'])/float(dual['balanced_mse']))
jc={r['center']:float(r['balanced_clean_mixed_mse'])for r in cent if r['arm']==J};dc={r['center']:float(r['balanced_clean_mixed_mse'])for r in cent if r['arm']==DU}
wins=sum(jc[k]<dc[k]for k in jc);assert wins==29 and abs(improvement-4.850042866956949)<1e-9
verified=0
for group in sorted(D.iterdir()):
 if not(group/'METHOD_STREAM.csv').exists():continue
 for r in rows(group/'METHOD_STREAM.csv'):
  assert abs(float(r['harm_frequency'])-int(r['harmful_count'])/int(r['opportunities']))<1e-14
  qual=float(r['harm_frequency'])<=.05 and float(r['mean_downside'])<=eta
  assert qual==(r['source_empirical_risk_pass']=='True');verified+=1
 # Trajectory summary contains sufficient statistics; independently rebuild count-based estimates.
 tr=rows(group/'TRAJECTORIES.csv')
 for r in rows(group/'METHOD_STREAM.csv'):
  ts=[x for x in tr if x['arm']==r['arm']and x['stream']==r['stream']]
  assert sum(int(x['harmful_count'])for x in ts)==int(r['harmful_count'])
  assert sum(int(x['opportunities'])for x in ts)==int(r['opportunities'])
  assert abs(np.mean([float(x['mse'])for x in ts])-float(r['mse']))<1e-12
  assert abs(np.mean([float(x['mean_downside'])for x in ts])-float(r['mean_downside']))<1e-12
e3=rows(D/'E3/METHOD_STREAM.csv');cc=rows(D/'E3/CENTERS.csv');vals={}
for arm in [J,DU]:
 vals[arm]={c:np.mean([float(r['mse'])for r in cc if r['center']==c and r['arm']==arm and r['stream']in ['clean','mixed']])for c in sorted({r['center']for r in cc})}
delta=np.array([vals[J][k]-vals[DU][k]for k in vals[J]]);rng=np.random.default_rng(20261022);boots=delta[rng.integers(40,size=(4000,40))].mean(axis=1);ci=np.quantile(boots,[.025,.975])
stored=next(r for r in rows(D/'E3/PAIRED_ALL_BASELINES.csv')if r['baseline']==DU and r['metric']=='mse'and r['stream']=='BALANCED_CLEAN_MIXED')
assert abs(delta.mean()-float(stored['delta_joint_minus_baseline']))<1e-14
assert np.allclose(ci,[float(stored['ci_low']),float(stored['ci_high'])],rtol=0,atol=1e-14),(ci,stored)
assert {r['stream']:int(r['harmful_count'])for r in e3 if r['arm']==J}=={'clean':16,'mixed':114}
assert {r['stream']:int(r['harmful_count'])for r in e3 if r['arm']==DU}=={'clean':4,'mixed':43}
with(O/'E3_recomputed.csv').open('w',newline='',encoding='utf-8')as f:
 w=csv.DictWriter(f,fieldnames=list(e3[0]));w.writeheader();w.writerows(e3)
cost=[]
for i in [1,2,3]:
 rr=rows(D/f'E5_COST_R{i}/UNIFIED_COST.csv')
 for arm in sorted({r['arm']for r in rr}):
  ts=[r for r in rr if r['arm']==arm];assert len(ts)==24
  total=sum(float(r['maintenance_common_seconds'])for r in ts)
  parts=sum(sum(float(r[k])for k in ['training_seconds','verification_and_gate_seconds','model_persistence_seconds','remaining_preparation_seal_and_bookkeeping_seconds'])for r in ts)
  assert abs(total-parts)<1e-9;cost.append({'arm':arm,'repetition':i,'seconds_per_24_stage_lifecycle':total})
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
pair=rows(D/'E0_MAIN_TABLES/PAIRED_MSE_ALL_BASELINES.csv');fig,ax=plt.subplots(figsize=(8,5.4))
x=np.array([float(r['mse_delta'])for r in pair])*1e3;lo=np.array([float(r['lower95'])for r in pair])*1e3;hi=np.array([float(r['upper95'])for r in pair])*1e3
ax.errorbar(x,np.arange(len(pair)),xerr=[x-lo,hi-x],fmt='o',capsize=3,color='#0072B2');ax.axvline(0,color='.3',ls='--');ax.set_yticks(np.arange(len(pair)),[r['baseline']for r in pair],fontsize=8);ax.invert_yaxis();ax.set_xlabel('Joint minus comparator MSE (x 1e-3), unadjusted 95% CI');fig.tight_layout();fig.savefig(O/'main_contrasts_recomputed.pdf');plt.close(fig)
report={'status':'PASS_READ_ONLY_AGGREGATE_RECONSTRUCTION','training_steps_added':0,'main_improvement_percent':improvement,'main_center_wins':wins,'all_method_stream_rows_checked':verified,'e3_machine_paired_delta':float(delta.mean()),'e3_unadjusted_ci_recomputed':ci.tolist(),'cost_replicas':cost,'scope_limit':'No full independent model-training replication; raw assets/checkpoints are indexed separately.'}
(O/'RECONSTRUCTION_RECEIPT.json').write_text(json.dumps(report,indent=2),'utf-8');print(json.dumps({k:v for k,v in report.items()if k!='cost_replicas'}))
