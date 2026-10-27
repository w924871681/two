"""Zero-optimizer authentication of original models, horizons, and historical PDFs."""
from common import *
import sys
import psutil
while psutil.virtual_memory().available<2*2**30:
    state(status='WAITING_FOR_STARTUP_RAM',phase='PREFLIGHT',work='接口认证启动等待2 GiB可用内存',completed=0,total=18,unit='份 checkpoint',active_workers=0,eta_seconds=None)
    time.sleep(3)
state(status='RUNNING',phase='PREFLIGHT',work='跨架构源checkpoint身份与输出形状认证',completed=0,total=18,unit='份 checkpoint')
sys.path.insert(0,'D:/dt-trustworthy-maintenance')
import torch
from core.models import Forecast,state_hash
torch.set_num_threads(1)
def forbidden(*a,**k):raise PermissionError('No optimizer in interface authentication')
torch.optim.SGD.step=forbidden
results={}
old_provenance=read(Path('D:/dt-trustworthy-maintenance/audits_v2_generality/checkpoint_provenance_audit.json'))
expected_sources={}
for record in old_provenance['records']:
    key=(record['backbone'],record['horizon'],record['seed']);value=record['sidecar']['source_checkpoint_hash']
    assert key not in expected_sources or expected_sources[key]==value
    expected_sources[key]=value
for seed,record in read(PRIOR/'ASSET_IDENTITY.json')['sources'].items():expected_sources[('GRU',1,int(seed))]=record['sha256']
for arch in ('MLP','TCN','GRU'):
    for h in (1,4):
        for seed in (7311,7312,7313):
            path=Path(f'D:/dt-trustworthy-maintenance/checkpoints/source_{arch}_H{h}_{seed}.pt');meta=read(path.with_suffix('.json'))
            assert meta['backbone']==arch and meta['horizon']==h and meta['seed']==seed
            assert sha(path)==expected_sources[(arch,h,seed)],'Historical source provenance mismatch'
            assert meta['source_centers']==list(range(10000,10020))
            model=Forecast(arch,H=h).cpu();model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True))
            assert state_hash(model)==meta['source_state_hash']
            with torch.no_grad():out=model(torch.zeros(2,96,24))
            assert list(out.shape)==[2,h]
            results[f'{arch}_H{h}_{seed}']=dict(path=str(path),sha256=sha(path),sidecar_sha256=sha(path.with_suffix('.json')),state_hash=state_hash(model),shape=list(out.shape),metadata=meta)
atomic(ROOT/'assets/INTERFACE_AUTH.json',dict(status='PASS_MODEL_IDENTITY_AND_SHAPE_ONLY',rows=results,optimizer_steps=0,joint_lifecycle_port_verified=False))
from pypdf import PdfReader
pdfs={}
for path in sorted((ROOT/'assets').rglob('*.pdf')):
    if 'Definitions' in path.parts or 'figures' in path.parts:continue
    reader=PdfReader(path);pages=[page.extract_text() or '' for page in reader.pages]
    assert pages and all(text.strip() for text in pages)
    target=ROOT/'assets'/('PDF_TEXT_'+path.stem+'.txt')
    target.write_text('\n\n'.join(f'PAGE {i+1}\n{text}' for i,text in enumerate(pages)),encoding='utf8')
    pdfs[str(path)]=dict(sha256=sha(path),pages=len(pages),full_text_path=str(target),full_text_sha256=sha(target),all_pages_extracted=True,visual_qa_performed=False)
atomic(ROOT/'assets/PDF_READ_RECEIPT.json',pdfs)
print(json.dumps(dict(model_interfaces=len(results),pdf_count=len(pdfs),optimizer_steps=0)))
