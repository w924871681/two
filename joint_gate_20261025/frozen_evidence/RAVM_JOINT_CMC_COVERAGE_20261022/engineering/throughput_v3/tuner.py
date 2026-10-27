"""Choose the fastest measured concurrency using only naturally completed real work."""
import statistics

class ThroughputTuner:
    def __init__(self, maximum, start=1, window_seconds=60., min_stages=72., max_window_seconds=180.):
        self.maximum=max(1,int(maximum));self.target=min(self.maximum,max(1,int(start)))
        self.window_seconds=window_seconds;self.min_stages=min_stages;self.max_window_seconds=max_window_seconds
        self.samples={};self.history=[];self.origin=None;self.reason='MEASURE_BASELINE'
        self.exploit_until=0.;self.failures={};self.retry_after={};self.last_event=None

    def best(self,funded):
        scores={k:statistics.median(x['weighted_per_second'] for x in v[-3:])
                for k,v in self.samples.items() if k<=funded and v}
        if not scores:return None,None
        fastest=max(scores.values())
        k=min(k for k,r in scores.items() if r>=fastest*.97)
        return k,scores[k]

    def choose(self,funded,now):
        available=[k for k in range(1,min(self.maximum,funded)+1) if now>=self.retry_after.get(k,0)]
        untested=[k for k in available if k not in self.samples]
        # Coarse extremes first, then fill every feasible integer; no fixed worker cap.
        anchors=[self.maximum,max(1,(self.maximum+1)//2),max(1,self.maximum//4),1]
        for k in anchors:
            if k in untested:return k,'PROBE_UNMEASURED'
        if untested:return min(untested,key=lambda k:abs(k-(self.best(funded)[0] or self.target))),'PROBE_UNMEASURED'
        best,_=self.best(funded)
        if best is None:return min(self.target,funded),'MEASURE_BASELINE'
        if now>=self.exploit_until:
            challengers=[k for k in available if k!=best]
            if challengers:
                self.exploit_until=now+300
                return min(challengers,key=lambda k:self.samples.get(k,[{'at':0}])[-1]['at']),'RECHECK_AFTER_COOLDOWN'
        return best,'USE_FASTEST_MEASURED'

    def tick(self,active,completed,weighted,stages,funded,now):
        self.last_event=None;funded=max(0,min(self.maximum,int(funded)))
        if funded==0:
            self.origin=None;self.reason='WAIT_FOR_RESOURCE';return 0
        if self.target>funded:
            self.target=funded;self.origin=None;self.reason='RESOURCE_DRAIN'
        if self.target<1:self.target=1;self.origin=None
        if active!=self.target:
            self.origin=None;self.reason='DRAIN_TO_TARGET' if active>self.target else 'FILL_TARGET'
            return self.target
        if self.origin is None:self.origin=(now,completed,weighted,stages);return self.target
        elapsed=now-self.origin[0];delta=stages-self.origin[3]
        if elapsed<self.window_seconds or (delta<self.min_stages and elapsed<self.max_window_seconds):return self.target
        if elapsed<=0 or weighted<=self.origin[2] or delta<1:self.origin=None;return self.target
        row=dict(at=now,workers=self.target,completed=completed-self.origin[1],seconds=elapsed,
                 stages=delta,weighted_work=weighted-self.origin[2],weighted_per_second=(weighted-self.origin[2])/elapsed,
                 trajectories_per_second=(completed-self.origin[1])/elapsed,settled=True)
        old_best,old_rate=self.best(funded)
        self.samples.setdefault(self.target,[]).append(row);self.history.append(row);self.history=self.history[-120:]
        if old_best is not None and self.target!=old_best and row['weighted_per_second']<old_rate*.95:
            n=self.failures.get(self.target,0)+1;self.failures[self.target]=n
            self.retry_after[self.target]=now+min(1800,300*2**min(n-1,3))
            self.target=old_best;self.reason='ROLLBACK_SLOWER_PROBE';self.exploit_until=now+300
        else:
            tested=row['workers'];self.failures[tested]=0;self.retry_after.pop(tested,None)
            self.target,self.reason=self.choose(funded,now)
            if self.reason=='USE_FASTEST_MEASURED' and not self.exploit_until:self.exploit_until=now+300
        self.origin=None;self.last_event={'measurement':row,'next_target':self.target,'reason':self.reason}
        return self.target

    def metadata(self,funded,now):
        best,rate=self.best(funded)
        return dict(policy_reason=self.reason,policy_target=self.target,best_measured_workers=best,
                    best_measured_weighted_per_second=rate,measured_concurrencies=sorted(self.samples),
                    unmeasured_concurrencies=[k for k in range(1,min(self.maximum,funded)+1) if k not in self.samples],
                    throughput_history=self.history[-12:],tie_tolerance_fraction=.03,
                    next_recheck_seconds=max(0,self.exploit_until-now),objective='fixed-timing-weighted completed stage work / settled wall time',
                    selection_scope='fastest measured; not proof of a global optimum')
