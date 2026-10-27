from pathlib import Path
import argparse,json,hashlib,csv
import pandas as pd
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
manifest=json.loads((B/'PUBLIC_FIELD_DOWNLOAD_RECEIPT.json').read_text('utf-8'));rows=[]
for r in manifest['files']:
 f=B/r['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
 if f.suffix!='.csv':continue
 d=pd.read_csv(f,low_memory=False);mask=d['labeling'].isin(['Return air temperature fault','Supply air temperature fault'])
 rows.append(dict(file=f.name,released_rows=len(d),temperature_fault_label_rows=int(mask.sum()),temperature_label_row_percent=100*float(mask.mean())))
expected=list(csv.DictReader((B/'PUBLIC_FIELD_CALIBRATION_AUDIT.csv').open(encoding='utf-8-sig')))
for r in rows:
 e=next(e for e in expected if e['file']==r['file']);assert r['released_rows']==int(e['released_rows'])and r['temperature_fault_label_rows']==int(e['temperature_fault_label_rows']);assert abs(r['temperature_label_row_percent']-float(e['temperature_label_row_percent']))<1e-12
(a.output/'PUBLIC_FIELD_RECONSTRUCTION_RECEIPT.json').write_text(json.dumps(dict(status='PASS_READONLY_PUBLIC_FIELD_COUNTS',rows=rows,training_steps=0,denominator='Released curated hourly records; not independent fault events')),encoding='utf-8')
print('Public field label counts PASS; zero training')
