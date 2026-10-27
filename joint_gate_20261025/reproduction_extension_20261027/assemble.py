"""Assemble a fresh portable copy of the frozen base plus the public extension.

This performs no training and never edits the base. The output must not exist.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys

here=Path(__file__).resolve().parent
default_base=here.parent/'reproducibility/08_Reproduction/training_bundle'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=default_base)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--alibaba-assets',type=Path,help='Optional authorized local directory containing assets/<sha> files for E3.')
    args=p.parse_args();base=args.base.resolve();out=args.output.resolve()
    assert base.is_dir() and (base/'ASSET_MANIFEST.json').is_file(),'Base bundle is missing'
    if out.exists() or out==base or base in out.parents:
        raise SystemExit('Use a new output directory outside the immutable base bundle.')
    ext=json.loads((here/'EXTENSION_MANIFEST.json').read_text('utf8'))
    if digest(base/'ASSET_MANIFEST.json')!=ext['base_asset_manifest_sha256']:
        raise SystemExit('Base bundle version differs from the required input.')
    for row in ext['files']:
        path=here/row['file']
        if not path.is_file() or path.stat().st_size!=row['bytes'] or digest(path)!=row['sha256']:
            raise SystemExit('Extension file mismatch: '+row['file'])
    # Verify the published base before creating anything in the destination.
    before=json.loads((base/'ASSET_MANIFEST.json').read_text('utf8'))
    for row in before['files']:
        f=base/row['file']
        if not f.is_file() or f.stat().st_size!=row['bytes'] or digest(f)!=row['sha256']:
            raise SystemExit('Base file mismatch: '+row['file'])
    e3_rows=[]
    if args.alibaba_assets:
        e3_root=args.alibaba_assets.resolve()
        index_path=here/'E3_UNDISTRIBUTED_ASSET_INDEX.json'
        spec_path=here/'E3_GROUP_UNDISTRIBUTED.json'
        if digest(index_path)!=ext['e3_asset_index_sha256'] or digest(spec_path)!=ext['e3_group_sha256']:
            raise SystemExit('E3 index or group specification mismatch.')
        e3_rows=json.loads(index_path.read_text('utf8'))['missing_assets']
        for row in e3_rows:
            name=Path(row['file'])
            if len(name.parts)!=2 or name.parts[0]!='assets':raise SystemExit('Invalid E3 asset path.')
            path=e3_root/name
            if not path.is_file() or path.stat().st_size!=row['bytes'] or digest(path)!=row['sha256']:
                raise SystemExit('Missing or mismatched E3 asset: '+row['file'])
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(base,out)
    records={row['file']:dict(row) for row in before['files']}
    for row in ext['files']:
        rel=Path(row['file']);target=out/rel
        if rel.parts[0] not in ('groups','assets'):
            raise SystemExit('Unexpected extension file: '+row['file'])
        if target.exists():raise SystemExit('Extension would overwrite base file: '+row['file'])
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(here/rel,target)
        records[row['file']]={'file':row['file'],'bytes':row['bytes'],'sha256':row['sha256']}
    if e3_rows:
        for row in e3_rows:
            target=out/row['file']
            if target.exists():raise SystemExit('E3 asset would overwrite a base asset: '+row['file'])
            shutil.copy2(e3_root/row['file'],target)
            records[row['file']]=dict(row)
        dest=out/'groups/E3.json';shutil.copy2(spec_path,dest)
        records['groups/E3.json']={'file':'groups/E3.json','bytes':dest.stat().st_size,'sha256':digest(dest)}
    group_paths=sorted((out/'groups').glob('*.json'))
    assert len(group_paths)==(17 if e3_rows else 16)
    for g in group_paths:
        spec=json.loads(g.read_text('utf8'))
        assert spec['domain'] in ('synthetic','uci','thermbuild') or (e3_rows and spec['domain']=='alibaba')
        for asset in list(spec['input_mapping'].values())+[s['path'] for s in spec['sources'].values()]:
            if asset not in records or not (out/asset).is_file():
                raise SystemExit('Missing '+asset+' for '+g.name)
    before['files']=[records[k] for k in sorted(records)]
    before['groups']=len(group_paths)
    before['total_bytes']=sum(r['bytes'] for r in before['files'])
    before['scope']='Frozen Main, E1, six E2 groups, five E4 groups, three E5 cost groups'+('; E3 added from reader-provided assets.' if e3_rows else '; E3 remains unavailable.')
    (out/'ASSET_MANIFEST.json').write_text(json.dumps(before,indent=2,ensure_ascii=False),'utf8')
    shutil.copy2(here/'ATTRIBUTION_AND_LICENSE.md',out/'EXTENSION_ATTRIBUTION_AND_LICENSE.md')
    v=subprocess.run([sys.executable,str(out/'run.py'),'verify'],capture_output=True,text=True)
    if v.returncode:raise SystemExit('Bundle verify failed: '+v.stdout+'\n'+v.stderr)
    print(json.dumps({'status':'PASS_ASSEMBLY_AND_FILE_VERIFY','groups':[p.stem for p in group_paths],
                      'manifest_files':len(before['files']),'output':str(out),'training_steps':0},indent=2))
if __name__=='__main__':main()
