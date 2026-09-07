import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.pretrain import pretrain
from core.engine import run
from core.protocol import ROOT,save_json

if __name__=='__main__':
    pretrain(smoke=True);rows=[]
    for c in [11000,11001]:
        for kind,alpha in [('clean',0),('mixed',.1)]:
            for method in ['Frozen','Always-FT','ER','EWC','Huber-FT','ValidationCommit','Proposed','OracleCommit']:
                r=run(c,7311,method,kind,alpha,stages=3,smoke=True,run_id='smoke_not_formal')
                rows+=r;print('smoke',c,kind,method,sum(x['deployed_service_mse'] for x in r)/3,flush=True)
                pd.DataFrame(rows).to_csv(ROOT/'results/smoke/raw_episode_results.csv',index=False,na_rep='NA')
    save_json(ROOT/'audits/smoke_status.json',{'status':'completed','rows':len(rows),'formal_evidence':False})
