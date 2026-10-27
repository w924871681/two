"""Read-only descriptive pairing, not a fault detector or learned calibrator."""
from pathlib import Path
import argparse, json, hashlib
import pandas as pd
import numpy as np

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def extract(raw, out):
    out.mkdir(parents=True,exist_ok=True)
    offset=0; parts=[]
    for c in pd.read_csv(raw/'QUANT_SensorSystems_hourly.csv',chunksize=200000):
        c['provider_row']=np.arange(offset+1,offset+len(c)+1);offset+=len(c)
        z=c[c.measurand.eq('NO2')].drop(columns='measurand')
        if len(z):parts.append(z)
    s=pd.concat(parts,ignore_index=True)
    ref=pd.read_csv(raw/'QUANT_Reference_hourly.csv')
    ref['provider_row']=np.arange(1,len(ref)+1)
    f=ref[ref.measurand.eq('NO2') & ref.version.eq('Ratified')].drop(columns=['measurand','version'])
    assert not f.duplicated(['time','location']).any(), 'Ambiguous ratified references'
    s.to_csv(out/'QUANT_NO2_ALL_PRODUCTS.csv',index=False)
    f.to_csv(out/'QUANT_NO2_RATIFIED_REFERENCE.csv',index=False)
    p={'status':'PASS','sensor_rows_scanned':offset,'selected_sensor_rows':len(s),'selected_reference_rows':len(f),'selection':'NO2 all released products/systems; Ratified reference only','original_sha256':{p.name:sha(p) for p in [raw/'QUANT_SensorSystems_hourly.csv',raw/'QUANT_Reference_hourly.csv']},'derivative_sha256':{p.name:sha(p) for p in out.glob('*.csv')},'provider_row':'1-based data row, excluding header and blank lines','optimizer_steps':0}
    (out/'EXTRACTION_RECEIPT.json').write_text(json.dumps(p,indent=2),'utf-8')

def profile(inp,out):
    out.mkdir(parents=True,exist_ok=True)
    x=json.loads((inp/'EXTRACTION_RECEIPT.json').read_text('utf-8'))
    for n,h in x['derivative_sha256'].items():assert sha(inp/n)==h,n
    s=pd.read_csv(inp/'QUANT_NO2_ALL_PRODUCTS.csv');r=pd.read_csv(inp/'QUANT_NO2_RATIFIED_REFERENCE.csv')
    assert not r.duplicated(['time','location']).any()
    ids=['location','instrument','sensornumber','version'];assert not s.duplicated(ids+['time']).any(),'Duplicated sensor hour'
    s['time']=pd.to_datetime(s.time);r['time']=pd.to_datetime(r.time)
    assert (s.time.dt.minute==0).all() and (r.time.dt.minute==0).all()
    z=s.merge(r[['time','location','measurement']],on=['time','location'],how='left',validate='many_to_one',suffixes=('_sensor','_reference'))
    rows=[]
    for key,g in z.groupby(ids,dropna=False,sort=True):
        finite=np.isfinite(g.measurement_sensor)&np.isfinite(g.measurement_reference)
        e=(g.loc[finite,'measurement_sensor']-g.loc[finite,'measurement_reference']).to_numpy()
        idx=pd.date_range(g.time.min(),g.time.max(),freq='h')
        observed=g.set_index('time').measurement_sensor.reindex(idx)
        missing=~np.isfinite(observed.to_numpy())
        edges=np.diff(np.r_[False,missing,False].astype(int));runs=np.flatnonzero(edges==-1)-np.flatnonzero(edges==1)
        d=dict(zip(ids,key));d.update(released_rows=len(g),finite_sensor_rows=int(np.isfinite(g.measurement_sensor).sum()),finite_reference_at_released_rows=int(np.isfinite(g.measurement_reference).sum()),paired_hours=len(e),observed_bounds_hour_slots=len(idx),missing_sensor_hour_slots=int(missing.sum()),missing_hour_runs=len(runs),max_missing_hour_run=int(runs.max())if len(runs)else 0,median_signed_error_ppb=float(np.median(e))if len(e)else None,median_abs_error_ppb=float(np.median(np.abs(e)))if len(e)else None,p95_abs_error_ppb=float(np.quantile(np.abs(e),.95))if len(e)else None,flagged_finite_pairs=int((finite & g.flag.notna()).sum()))
        rows.append(d)
    table=pd.DataFrame(rows);table.to_csv(out/'QUANT_NO2_SYSTEM_PRODUCT_METRICS.csv',index=False)
    summaries=[]
    for version,g in table.groupby('version',sort=True):
        valid=g[g.paired_hours.gt(0)]
        summaries.append(dict(version=version,system_products=len(g),products_with_pairs=len(valid),paired_sensor_hours=int(g.paired_hours.sum()),signed_median_min_ppb=float(valid.median_signed_error_ppb.min()),signed_median_max_ppb=float(valid.median_signed_error_ppb.max()),median_abs_error_min_ppb=float(valid.median_abs_error_ppb.min()),median_abs_error_max_ppb=float(valid.median_abs_error_ppb.max()),p95_abs_error_min_ppb=float(valid.p95_abs_error_ppb.min()),p95_abs_error_max_ppb=float(valid.p95_abs_error_ppb.max())))
    pd.DataFrame(summaries).to_csv(out/'QUANT_NO2_PRODUCT_SUMMARY.csv',index=False)
    receipt={'status':'PASS_READONLY_PAIRED_FIELD_PROFILE','optimizer_steps':0,'sensor_rows':len(s),'ratified_reference_rows':len(r),'systems':int(s[ids[:-1]].drop_duplicates().shape[0]),'system_products':len(table),'cities':sorted(s.location.unique().tolist()),'versions':summaries,'paired_sensor_hours':int(table.paired_hours.sum()),'zero_pair_system_products':int(table.paired_hours.eq(0).sum()),'flagged_finite_pairs_retained':int(table.flagged_finite_pairs.sum()),'units':'NO2 ppb, sensor minus co-located Ratified reference; reference has finite uncertainty','not_fault_rate':True,'not_target_DT_site_calibration':True,'not_independent_replicates':'Hours within device and product versions sharing device/reference are dependent; no inferential confidence interval or pooling as independent trials','availability_boundary':'All observed first-to-last hourly slots per system/product, including absent rows and explicit missing measurements; deployment gaps/maintenance are not distinguished from faults','input_sha256':{n:sha(inp/n)for n in x['derivative_sha256']}}
    (out/'QUANT_PROFILE_RECEIPT.json').write_text(json.dumps(receipt,indent=2),'utf-8')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path);p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.raw:extract(a.raw,a.output);profile(a.output,a.output)
    else:profile(a.input,a.output)
