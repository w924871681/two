import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import itertools,json
from core.protocol import ROOT
from core.freeze import require_frozen
from scripts.pretrain import pretrain
from scripts.run_heldout import case,METHODS
from scripts.run_calibration_parallel import main as calibrate

def main():
    require_frozen();manifest=json.loads((ROOT/'alibaba_pool_manifest.json').read_text())
    assert len(manifest['machines'])==100
    cfg={}
    for f in ['frozen_candidate_config.yaml','frozen_commit_config.yaml','frozen_baseline_config.yaml']:cfg.update(json.loads((ROOT/'configs'/f).read_text()))
    for seed in [7311,7312,7313]:pretrain(seed,domain='alibaba')
    for seed,c,(kind,alpha),method in itertools.product([7311,7312,7313],range(20060,20100),[('clean',0.),('mixed',.1)],METHODS):
        case('q6_alibaba',c,seed,method,kind,alpha,'both',cfg,key='direct_transfer')
    calibrate('alibaba',2)
    commit=json.loads((ROOT/'configs/alibaba_frozen_commit_config.yaml').read_text())
    # Explicitly clear synthetic fallback flags before applying independent domain calibration.
    cfg.update({'retain_all':False,'validation_retain_all':False});cfg.update(commit)
    for seed,c,(kind,alpha),method in itertools.product([7311,7312,7313],range(20060,20100),[('clean',0.),('mixed',.1)],['ValidationCommit','Proposed']):
        case('q6_alibaba',c,seed,method,kind,alpha,'both',cfg,key='domain_calibration_diagnostic')

if __name__=='__main__':main()
