import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest,json
import numpy as np
import pandas as pd
from core.protocol import ROOT,POOLS,Timeline,windows,spans,attack,block_indices,save_json

class ProtocolTests(unittest.TestCase):
    def test_no_future_service_leakage(self):
        t=Timeline(11000)
        with self.assertRaises(AssertionError):t.service(1)
        t.record_decision(1,False);self.assertLess(t.maintenance(1)[1].ts[-1],t.service(1).ts[0])
    def test_raw_segment_disjointness(self):
        for t in range(1,25):
            u,v,s=spans(t);self.assertLessEqual(u[1],v[0]);self.assertEqual(v[1],s[0])
            if t>1:self.assertEqual(u,spans(t-1)[2])
    def test_window_no_cross_boundary(self):
        seg=Timeline(11000).warmup()
        for H in [1,4]:
            x,y,ts=windows(seg,H=H);self.assertEqual(len(x),800-96-H+1)
            self.assertEqual(ts[0,0],seg.ts[96]);self.assertEqual(ts[-1,-1],seg.ts[-1])
            blocks=block_indices(len(x),10,H)
            for a,b in zip(blocks,blocks[1:]):self.assertLess(ts[a][-1,-1],ts[b][0,0])
    def test_attack_fraction_bound(self):
        u,v=Timeline(11000).maintenance(1)
        for s in [u,v]:
            for a in [0,.05,.1,.2]:
                for kind in ['random','persistent_bias','burst','replay']:
                    z,m,ts,_=attack(s,11000,1,kind,a,'both')
                    for b in np.array_split(np.arange(len(m)),10):self.assertLessEqual(m[b].sum(),np.floor(len(b)*a+1e-8))
                    self.assertTrue(np.array_equal(z.x[~m],s.x[~m]));self.assertTrue(np.array_equal(z.y[~m],s.y[~m]))
                    self.assertTrue(((z.x>=0)&(z.x<=1)).all())
    def test_attack_masks_paired_across_methods(self):
        u,_=Timeline(11000).maintenance(1)
        a=attack(u,11000,1,'mixed',.1,'both');b=attack(u,11000,1,'mixed',.1,'both')
        np.testing.assert_array_equal(a[1],b[1]);self.assertEqual(a[0].hash,b[0].hash)
    def test_service_data_immutable(self):
        t=Timeline(11000);t.record_decision(1,False);s=t.service(1);h=s.hash;s.y[:]=0
        self.assertEqual(t.service(1).hash,h)
    def test_calibration_heldout_disjoint_centers(self):
        groups=list(POOLS.values())
        for i,a in enumerate(groups):
            for b in groups[i+1:]:self.assertFalse(set(a)&set(b))
    def test_same_initial_state_across_methods(self):
        p=ROOT/'results/smoke/raw_episode_results.csv'
        if not p.exists():self.skipTest('P2/P3 not run yet')
        df=pd.read_csv(p);self.assertTrue((df.groupby('center_id').initial_state_hash.nunique()==1).all())
    def test_controlled_update_budget(self):
        p=ROOT/'results/smoke/raw_episode_results.csv'
        if not p.exists():self.skipTest('P2/P3 not run yet')
        df=pd.read_csv(p);self.assertTrue((df[df.method!='Frozen'].number_of_backward_updates==50).all())
    def test_rejected_candidate_does_not_modify_deployed_state(self):
        p=ROOT/'results/smoke/raw_episode_results.csv'
        if not p.exists():self.skipTest('P2/P3 not run yet')
        df=pd.read_csv(p)
        for _,g in df.groupby(['center_id','method','attack_type']):
            g=g.sort_values('stage')
            for i in range(len(g)-1):
                a,b=g.iloc[i],g.iloc[i+1]
                self.assertEqual(b.parent_state_hash,a.candidate_state_hash if a.commit else a.parent_state_hash)
    def test_verification_not_used_for_candidate_gradients(self):
        from core.models import Forecast,DEVICE,tensors,adapt
        _,v=Timeline(11000).maintenance(1)
        with self.assertRaises(AssertionError):adapt(Forecast().to(DEVICE),tensors(windows(v)),steps=1)
    def test_historical_buffer_not_used_for_training(self):
        from core.models import Forecast,DEVICE,tensors,adapt
        h=Timeline(11000).initial_history()
        with self.assertRaises(AssertionError):adapt(Forecast().to(DEVICE),tensors(windows(h)),steps=1)
    def test_final_config_hash_frozen_before_heldout(self):
        from core.freeze import require_frozen
        with self.assertRaises((FileNotFoundError,AssertionError)):require_frozen(ROOT/'audits/nonexistent_test_freeze.json')
    def test_bootstrap_clusters_by_center(self):
        from core.statistics import cluster_bootstrap
        d=pd.DataFrame({'center_id':[1,2,3],'v':[0.,1.,4.]})
        doubled=pd.concat([d,d[d.center_id==1]]*12,ignore_index=True)
        self.assertEqual(cluster_bootstrap(d,'v'),cluster_bootstrap(doubled,'v'))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProtocolTests);result=unittest.TextTestRunner(verbosity=2).run(suite)
    save_json(ROOT/'audits/protocol_tests.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':[str(t) for t,_ in result.skipped],'status':'passed' if result.wasSuccessful() else 'FAILED','complete_mandatory_audit_suite':False})
    sys.exit(0 if result.wasSuccessful() else 1)
