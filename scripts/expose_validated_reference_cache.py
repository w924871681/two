"""Hard-link strictly validated archived cache assets for reference comparisons."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,os
from core.protocol import ROOT,save_json

def main():
    audit=json.loads((ROOT/'audits/cache_migration.json').read_text());assert audit['status']=='passed'
    archives=[Path(x) for x in audit['archives_scanned']];targets={'calibration_candidates':ROOT/'checkpoints/calibration_candidates','calibration_evidence':ROOT/'checkpoints/calibration_evidence'}
    linked={k:0 for k in targets};duplicates={k:0 for k in targets}
    for name,target in targets.items():
        target.mkdir(parents=True,exist_ok=True)
        for archive in archives:
            source=archive/'checkpoints'/name
            if not source.exists():continue
            for path in source.iterdir():
                dst=target/path.name
                if dst.exists():duplicates[name]+=1
                else:os.link(path,dst);linked[name]+=1
    report={'status':'passed','validation_basis':'audits/cache_migration.json','hard_links_created':linked,'already_present_or_duplicate':duplicates,'source_modified':False}
    save_json(ROOT/'audits/reference_cache_exposure.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
