"""Populate the final scientific-result section from generated tables and audits."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,json,subprocess
import pandas as pd
from core.protocol import ROOT
from core.freeze import hash_file

def verdict(lo,hi,lower_better=True):
    if pd.isna(lo) or pd.isna(hi):return 'inconclusive'
    if lower_better:return 'supported' if hi<0 else 'contradicted' if lo>0 else 'inconclusive'
    return 'supported' if lo>0 else 'contradicted' if hi<0 else 'inconclusive'

def markdown_table(frame):
    def cell(value):
        if pd.isna(value):return 'NA'
        if isinstance(value,float):return f'{value:.6g}'
        return str(value).replace('|','\\|')
    head='| '+' | '.join(frame.columns)+' |';rule='|'+'|'.join(['---']*len(frame.columns))+'|'
    return '\n'.join([head,rule]+['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)])

def main():
    summaries=pd.read_csv(ROOT/'results/tables/all_summaries.csv');pairs=pd.read_csv(ROOT/'results/tables/all_paired_comparisons.csv');q1=summaries[summaries.question=='q1_overall'].copy()
    columns=['attack_type','method','lifecycle_mse','lifecycle_mse_ci_low','lifecycle_mse_ci_high','harmful_commit_rate','harmful_commit_rate_ci_low','harmful_commit_rate_ci_high','average_downside','average_downside_ci_low','average_downside_ci_high','commit_rate']
    main_table=markdown_table(q1[columns].sort_values(['attack_type','lifecycle_mse']))
    key=pairs[(pairs.question=='q1_overall')&(pairs.reference.isin(['Always-FT','ValidationCommit']))];findings=[]
    for r in key.itertuples():findings.append({'condition':r.attack_type,'reference':r.reference,'metric':r.metric,'difference':r.difference,'ci':[r.ci_low,r.ci_high],'verdict':verdict(r.ci_low,r.ci_high)})
    negative=[f for f in findings if f['verdict']!='supported'];freeze=json.loads((ROOT/'configs/frozen_commit_config.yaml').read_text());audit_path=ROOT/'audits/final_reproducibility_audit.json';audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'status':'pending'}
    env=json.loads((ROOT/'audits/environment.json').read_text());sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();baseline=json.loads((ROOT/'configs/frozen_baseline_config.yaml').read_text())
    scientific=f'''<!-- FINAL_SCIENTIFIC_RESULTS_START -->\n## Final scientific results\n\nGenerated: {datetime.datetime.now().isoformat()}\n\n- Exact final git commit: `{sha}`\n- Environment: Python {env.get('python_version')}, PyTorch {env.get('torch')}, GPU {env.get('gpu')}\n- Frozen candidate config SHA-256: `{hash_file(ROOT/'configs/frozen_candidate_config.yaml')}`\n- Frozen commit config SHA-256: `{hash_file(ROOT/'configs/frozen_commit_config.yaml')}`\n- Frozen baseline config SHA-256: `{hash_file(ROOT/'configs/frozen_baseline_config.yaml')}`\n- Frozen commit configuration: `{json.dumps(freeze,sort_keys=True)}`\n- No-leakage/pre-heldout audit: `{json.loads((ROOT/'audits/heldout_readiness.json').read_text())['status']}`\n- Final reproduction status: `{audit.get('status')}`\n\n### Q1 main metrics with 95% center-cluster confidence intervals\n\n{main_table}\n\n### Contribution assessment\n\n```json\n{json.dumps(findings,indent=2)}\n```\n\n### Negative and inconclusive findings\n\nValidationCommit calibration used the preregistered retain-all fallback. Comparisons whose confidence interval crosses zero, or favors the reference, are retained below without suppression.\n\n```json\n{json.dumps(negative,indent=2)}\n```\n\n### Baseline fidelity notes\n\n- Frozen, Always-FT, ER, EWC, Huber-FT, ValidationCommit and Proposed were executed under their frozen configurations.\n- CLeaR-Predictor is a declared predictor-only framework adaptation: `{json.dumps(baseline,sort_keys=True)}`.\n- MER-Reg-2026 remains `implementation_unavailable_or_nonfaithful` and is not represented by a proxy.\n- OracleCommit is an offline diagnostic and is excluded from deployable rankings.\n\n### Outputs\n\nQ1–Q6 tables, 4,000-replicate center-cluster bootstrap comparisons, figure-ready CSVs, publication figures, runtime/cost data and audit manifests are under `results/` and `audits/`.\n<!-- FINAL_SCIENTIFIC_RESULTS_END -->'''
    path=ROOT/'FINAL_EXPERIMENT_REPORT.md';text=path.read_text(encoding='utf-8');start='<!-- FINAL_SCIENTIFIC_RESULTS_START -->';end='<!-- FINAL_SCIENTIFIC_RESULTS_END -->'
    if start in text:text=text[:text.index(start)]+scientific+text[text.index(end)+len(end):]
    else:text=text.rstrip()+'\n\n'+scientific+'\n'
    path.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':main()
