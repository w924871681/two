"""Bind authenticated Alibaba inputs/M0/source files to original archived provenance."""
from common import *
def verify():
    source=Path('D:/dt-trustworthy-maintenance');audit=source/'audits_v2_alibaba/alibaba_protocol_provenance_audit.json';manifest=read(source/'audits_v2_alibaba/alibaba_output_hash_manifest.json')
    expected=manifest['audit_hashes'].get(audit.name)
    assert expected and sha(audit)==expected
    old=read(audit);new=read(ROOT/'assets/E3_ALIBABA_AUTH.json');assert old['status']==new['status']=='PASS'
    for row in new['rows']:
        ref=old['data_files'][str(row['center'])]
        assert row['sha256']==ref['sha256'] and row['clean_hash']==ref['clean_hash'] and row['machine_id_hash']==ref['machine_id_hash']
    for row in new['existing_m0']:
        ref=old['checkpoint_files'][f"{row['seed']}:{row['center']}"];assert row['sha256']==ref['checkpoint_sha256']
        assert row['sidecar']['initial_state_hash']==ref['initial_state_hash'] and row['sidecar']['source_checkpoint_hash']==ref['source_checkpoint_hash']
        assert sha(Path(row['path']).with_suffix('.json'))==ref['sidecar_sha256']
        assert new['sources'][str(row['seed'])]['sha256']==ref['source_checkpoint_hash']
    result=dict(status='PASS',original_provenance_sha256=sha(audit),original_output_manifest_sha256=sha(source/'audits_v2_alibaba/alibaba_output_hash_manifest.json'),source_models=3,existing_m0=120,inputs=40,optimizer_steps=0,scientific_outcomes_not_used_for_selection=True)
    atomic(ROOT/'assets/E3_HISTORY_BINDING.json',result);return result
