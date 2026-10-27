"""Chinese evidence reports; scientific coverage and package integrity are separate."""
from common import *
import csv,collections
def rows(p):
    if not Path(p).exists():return []
    with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def write(name,text):(ROOT/name).write_text(text,encoding='utf8')
def run():
    seal=read(ROOT/'SCIENCE_EXECUTION.lock.json');stats=read(ROOT/'STATISTICS_RECEIPT.json');groups=stats['groups'];specs={p.stem:read(p)for p in (ROOT/'registered_groups').glob('*.json')};matrix=[];negative=[];actual=[]
    for name,spec in specs.items():
        r=next((x for x in groups if x['group']==name),{});summary=rows(STORAGE/'statistics'/name/'METHOD_STREAM.csv')
        joint=[x for x in summary if x['arm']=='JOINT__l3__m0'];risk_bad=[x['stream']for x in joint if x['source_empirical_risk_pass']!='True'];inactive=[x['stream']for x in joint if float(x['commit_rate'])==0]
        if risk_bad or inactive:negative.append(dict(group=name,risk_exceedance_streams=risk_bad,inactive_streams=inactive))
        matrix.append(dict(stage=spec['stage'],group=name,domain=spec['domain'],status=r.get('status','NOT_EXECUTED'),expected_trajectories=len(__import__('stage_specs').jobs(spec)),validated_trajectories=r.get('actual_scientific_trajectories',0),cost_only_replicas=r.get('cost_timing_replicas',0),verified_stage_rows=r.get('validated_stage_rows',0),risk_exceedance=';'.join(risk_bad),zero_activity=';'.join(inactive),physical_cluster=spec['physical_cluster'],statistics=str(STORAGE/'statistics'/name)))
        ledger=ROOT/'process'/f'{name}_SGD_CALL_ACCOUNTING.jsonl';begins={};known=0;uncertain=[]
        if ledger.exists():
            for line in ledger.read_text(encoding='utf8').splitlines():
                e=json.loads(line)
                if e['event']=='BEGIN':begins[e['call_id']]=e
                elif e['event'] in ('DONE','FAILED_SCOPE'):known+=e['successful_steps'];begins.pop(e['call_id'],None)
            uncertain=list(begins)
        actual.append(dict(group=name,successful_steps_durably_closed=known,open_optimizer_scopes=len(uncertain),uncertain_additional_steps_upper=len(uncertain)*50,registered_budget=seal['budgets'][name],ledger_sha256=sha(ledger)if ledger.exists()else None))
    dev=rows(ROOT/'E0_MAIN_TABLES/DEVCAL_JOINT_RESULTS_BY_ARM.csv')
    for row in dev:
        point=tuple(float(row[k])for k in('balanced_mse','worst_harmful','worst_downside'))
        row['pareto_dev_mse_harm_downside']=not any(all(float(other[k])<=value for k,value in zip(('balanced_mse','worst_harmful','worst_downside'),point))and any(float(other[k])<value for k,value in zip(('balanced_mse','worst_harmful','worst_downside'),point))for other in dev)
        row['frozen_selected']=row['arm']=='JOINT__l3__m0';row['new_final_reselection']=False
    save_csv(ROOT/'E5_DEV_PARETO.csv',dev)
    blocked=seal.get('blocked_groups',[]);complete=not blocked and all(r['status']=='PASS'for r in groups) and len(groups)==len(specs) and all(not x['open_optimizer_scopes']for x in actual)
    # Statistical failure against any registered baseline is retained independently of risk failure.
    primary=[]
    for name,spec in specs.items():
        if spec.get('cost_only'):continue
        scope='BALANCED_CLEAN_MIXED' if set(spec['stream_ids'])=={'clean','mixed'}else 'EQUAL_CONDITION_MEAN'
        for row in rows(STORAGE/'statistics'/name/'PAIRED_ALL_BASELINES.csv'):
            if row['metric']=='mse' and row['stream']==scope and float(row['delta_joint_minus_baseline'])>0:negative.append(dict(group=name,comparison='Joint minus '+row['baseline'],finding='Joint raw MSE higher; preserve comparator risk qualification separately',delta=row['delta_joint_minus_baseline']))
            if row['baseline']=='DUAL_MEAN__g12' and row['metric']=='mse' and row['stream']==scope:
                positive=bool(row['ci_high'])and float(row['ci_high'])<0
                primary.append(dict(group=name,delta=row['delta_joint_minus_baseline'],ci_low=row['ci_low'],ci_high=row['ci_high'],supports_cluster_mse_improvement=positive,scope=row['uncertainty']))
                if not positive:negative.append(dict(group=name,comparison='Joint vs fixed Main DUAL',finding='negative or inconclusive primary MSE contrast; no retuning'))
    verdict='COVERAGE_BLOCKED' if not complete else 'COVERAGE_COMPLETE_WITH_NEGATIVE_FINDINGS' if negative else 'COVERAGE_COMPLETE'
    go=dict(status=verdict,main_final_status='FINAL_MAIN_PASS',main_final_rerun=False,coverage_complete=complete,new_science_optimizer_accounting=actual,negative_or_inconclusive_findings=negative,primary_comparisons=primary,blocked_groups=blocked,
        core_method_supported_by_passed_main=True,risk_utility_claim='retain only the frozen Main qualified-comparator empirical claim; inspect all unadjusted supplementary contrasts and risk streams',
        universal_generalization_supported=False,independent_field_safety_supported=False,novelty='candidate whole mechanism combining current mean margin, parent loss scale and MWU soft penalty with causal deployment; known components alone neither prove nor refute whole-mechanism novelty; no originality certification',
        ready_for_clean_tracked_rebuttal_reconstruction=False,evidence_ready_for_human_academic_review=complete,reconstruction_recommendation='Review all outcomes and scope/novelty concerns with the user and GPT before deciding full revision; not publication GO',manuscripts_modified=False,journal_uploaded=False,figure_visual_review='machine-rendered drafts require visual academic review; no automatic publication',
        statistical_limits=['center/machine clusters; seeds, stages and windows not independent','supplements:4000 percentile bootstrap draws seed20261022; reused Main intervals retain original seed20261020; all baselines retained; no multiplicity correction','Main primary chosen among observed eligible Final baselines; original selection uncertainty persists','Alibaba previously exposed40 machines at one trace setting, not fresh blind field confirmation','UCI one home and three rooms; ThermBuild two houses at one site; no population confidence interval','empirical source risk thresholds are descriptive outside source domain, not universal guarantees'],at_unix=time.time())
    atomic(ROOT/'SCIENTIFIC_GO_NO_GO.json',go);save_csv(ROOT/'EXPERIMENT_COVERAGE_MATRIX.csv',matrix);atomic(ROOT/'ACTUAL_OPTIMIZER_ACCOUNTING.json',dict(groups=actual,reported_steps_not_planned_counts=True))
    titles={'E1':'E1_ROBUSTNESS_REPORT_ZH.md','E2':'E2_ARCH_HORIZON_REPORT_ZH.md','E3':'E3_ALIBABA_REPORT_ZH.md','E4':'E4_CROSS_TASK_REPORT_ZH.md','E5':'E5_COST_AND_SENSITIVITY_REPORT_ZH.md'}
    for stage_name,file in titles.items():
        content=[f'# {stage_name} 科研结果与边界',f'总体覆盖裁决：`{verdict}`。下表只汇总独立审计通过的数据；未完成/未验证对象在覆盖矩阵中列明。','', '|组别|状态|有效轨迹/计时复本|方法阶段|风险超标流|零活动流|','|---|---|---:|---:|---|---|']
        for item in matrix:
            if item['stage']==stage_name:content.append(f"|{item['group']}|{item['status']}|{item['validated_trajectories']+item['cost_only_replicas']}|{item['verified_stage_rows']}|{item['risk_exceedance'] or '无/未获得完整结果'}|{item['zero_activity'] or '无/未获得完整结果'}|")
        for name,spec in specs.items():
            if spec['stage']!=stage_name:continue
            content.extend(['',f'## {name}',f"独立单位：{spec['physical_cluster']}；种子 {spec['seeds']}；阶段数 {spec['stages']}。原始指标为该任务目标的平方单位；温度另提供 °C²，不跨尺度合并。",f"完整数据：`{STORAGE/'statistics'/name}`。",'','|流|Joint MSE|harm/机会|harm频率|downside|commit|有益提交recall|','|---|---:|---:|---:|---:|---:|---:|'])
            for z in rows(STORAGE/'statistics'/name/'METHOD_STREAM.csv'):
                if z['arm']=='JOINT__l3__m0':content.append(f"|{z['stream']}|{float(z['mse']):.9g}|{z['harmful_count']}/{z['opportunities']}|{float(z['harm_frequency']):.6%}|{float(z['mean_downside']):.9g}|{float(z['commit_rate']):.6%}|{z['beneficial_recall'] or '无有益候选分母'}|")
            content.extend(['','所有方法的正负比较见 METHOD_STREAM.csv、CENTERS.csv、PAIRED_ALL_BASELINES.csv，不能只引用上表。成本来自实际墙钟；Service评价另列，审计不调用优化器。'])
        if stage_name=='E1':content.append('\n9类污染条件全部预先注册；压力测试不是现场故障概率估计。Frozen零候选训练解释了预算上界和实际步数的差别。')
        if stage_name=='E2':content.append('\n三架构×两跨度使用真实兼容source，目标跨度块边界保持互不重叠；Joint阈值不按架构重校准。')
        if stage_name=='E3':content.append('\n原始40机器和17,000合法排序观测经认证，7遥测值/7mask与填零布局保留；第24段Service终点为16760。过去Service成熟后才允许后续Update复用。原机器在历史返修中暴露过，不能称作新的盲法外部确认。')
        if stage_name=='E4':content.append('\nUCI三个房间属于一栋住宅；ThermBuild两屋同一实验站。保留缺失目标，不插值，按原始时序分块后剔除无效目标窗口。只能报告小样本跨任务边界，不能据房间/种子数声称大量独立样本。这里验证预测维护任务，未验证闭环控制或完整物理数字孪生系统。')
        if stage_name=='E5':content.extend(['\n16个开发配置敏感性见 E0_MAIN_TABLES/DEVCAL_JOINT_RESULTS_BY_ARM.csv 和 BY_STREAM.csv；未用新Final选参。同状态合法分歧见 E0_FIGURE_SOURCE_DATA。',f'开发三指标MSE/harm/downside的非支配配置为 {sum(x["pareto_dev_mse_harm_downside"]for x in dev)}/16，完整表E5_DEV_PARETO.csv；冻结所选配置的Pareto状态不改变本轮方法锁。','重复成本固定同一Main输入、同一初始模型、三个复本、12方法；这是明确计入新增预算的计时复本，不计入新增科学样本。每个ready集合只有一个生命周期以统一计时边界，仍经动态资源准入。统一组件计时文件 COST_UNIFIED_*.json 包含准备/适配、Verification和门控、模型持久化、其余封存、维护总耗时、独立Service评价、CPU RSS端点、GPU进程峰值与原生缓冲字节。共享主机墙钟不证明能耗或普遍复杂度。'])
        write(file,'\n'.join(content)+'\n')
    write('MAIN_FINAL_REUSE_AUDIT.md',(ROOT/'E0_READONLY_REPORT_ZH.md').read_text(encoding='utf8')+'\n\n本轮未重训Main；原ZIP身份与外置87,696模型的核验回执见Preflight与资产护照。')
    reviewer=read(ROOT/'assets/REVIEWER_16_SOURCE.json')['rows'];md=['# 原16项审稿证据矩阵','','本矩阵提供实际证据与修改建议，不代表审稿人接受，也未自动修改稿件。','', '|ID|原文|现有证据|新增证据|建议位置|真正解决|未解问题|','|---|---|---|---|---|---|---|']
    unresolved={'R1.1':'跨任务独立房屋数有限，通用DT/控制安全仍无证据','R1.2':'ValidationCommit冻结retain-all的零活动不能当作充分强主动对照；保留活跃近邻','R2.1':'需要文献与机制层面的原创性论证，实验本身不能认证新颖性','R2.2':'ValCommit回退行为不能重选门槛补造活跃性','R2.3':'开发敏感性不是新的独立泛化证据','R2.4':'受控污染强度不等于真实发生率，缺少现场故障频率调查','R2.5':'Service为动作后未人工污染的离线参考，仍可能有原生缺失或测量偏差','R2.6':'只保留经验界，不具有概率/物理控制安全保证','R2.7':'必须根据E3全部真实结果收窄外域表述','R2.8':'不得隐藏风险不合格但MSE更低的基线','R2.9':'外置CAS不在ZIP内，复现依赖原始数据、硬件与完整路径重定位','R2.10':'少中心、旧外域暴露与多比较限制须明确','R2.11':'开发网格不能用Final重新挑选','R2.12':'图稿需视觉复核、符号检查与人工返修','R3.1':'建议在第5节良性适应分析正文补Fig.5引用；本轮未改稿','R3.2':'离线已定位原[32]团体作者被排成Group A、缺URL；建议团体作者双花括号和数据版本/来源链接。在线原仓库访问失败，不能宣称已完整核实；见R3_REFERENCE32_OFFLINE_CHECK.md；未改稿'}
    for r in reviewer:
        rid=r['reviewer_id'];md.append('|'+ '|'.join([rid,r['original_comment'].replace('|','/').replace('\n',' '),'E0/Main已通过的冻结证据',r['evidence_plan']+'；实际状态见覆盖矩阵','方法、实验第5节、Limitations或对应回复段','证据补充完成；学术回应待审' if complete else '未完全解决：覆盖仍有阻塞',unresolved[rid]])+'|')
    write('REVIEWER_16_EVIDENCE_MATRIX.md','\n'.join(md)+'\n')
    topics=['Main lifecycle performance','Harmful transition risk','Harmful downside','Commit activity and recall','Corruption severity','Benign regime comparison','Joint decision behavior','Parameter sensitivity','Architecture/horizon generality','Maintenance cost','Alibaba external comparison','Cross-task boundaries']
    mapping=['# 论文图表数据映射','','图稿是机器生成草稿，视觉和学术复核通过后再用于论文。原Fig.6双证据消融不再支持新版Joint。','', '|图意|来源|复算与统计|限制|','|---|---|---|---|']
    for t in topics:mapping.append(f'|{t}|E0_MAIN_TABLES、E0_FIGURE_SOURCE_DATA或statistics/对应组全部CSV|coverage_statistics.py；Main保留原4000次bootstrap/种子20261020；补充中心/机器4000次配对bootstrap/种子20261022；render_figures.py；每图SIDECAR含单位/n/来源|保留负结果；温度不虚构独立n；多比较未校正；图稿待视觉复核|')
    write('PAPER_FIGURE_TABLE_SOURCE_MAP.md','\n'.join(mapping)+'\n')
    report=['# Joint Gate / CMC 全部必要实验中文报告',f'\n当前裁决：`{verdict}`。Main保持 `FINAL_MAIN_PASS`，未重复训练。',f'\n已验证新科学轨迹：{sum(x["validated_trajectories"]for x in matrix)}；计时复本：{sum(x["cost_only_replicas"]for x in matrix)}；已持久封闭的真实新增优化器成功步数：{sum(x["successful_steps_durably_closed"]for x in actual)}。开放账本范围另列不确定上界，不伪称为零或按计划填数。','\nE0–E5逐项结果见分报告、覆盖矩阵和完整统计CSV。所有负结果、无效/阻塞轨迹及其尝试保留。','\n主Final支持冻结合成协议下相对原风险合格比较对象的经验效用改善；不支持所有基线MSE占优、普遍概率安全、任意数字孪生任务泛化或现场独立确认。新补充结果必须按组、数据单位和风险状态解释。','\n新增中心/机器配对区间固定4000次bootstrap、随机种子20261022；只读复用的Main原区间保留原种子20261020。不将窗口/阶段/种子冒充独立中心，多比较未校正。UCI一栋住宅、ThermBuild两屋同一站点只作任务描述。','\n创新性应评价完整合法部署机制、组件关系与效果证据；不能因组件已知就否认整体机制，也不能因性能改善就认证新颖性。','\n16项意见的证据补充不等于编辑/审稿正式接受。当前交付供用户与GPT最终学术审查，再决定Clean/Tracked/Rebuttal重构；本轮未修改稿件或上传期刊。','\nZIP完整性、外置模型与可复现范围见delivery/PACKAGE_VERIFICATION.json。包核验通过也不等于科学效果通过；审阅包小于512,000,000字节；全部外置CAS权重有真实字节、路径和SHA清单，ZIP不声称包含其权重字节；包含部分source/M0初始化文件时另行计数。']
    report.extend(['\n## 只读复用的Main完整方法结果','\nMSE为clean/mixed平衡指标；最大harm/downside取原三个流。不能把风险不合格但MSE更低的结果隐去。','\n|方法|平衡MSE|最大流harm|最大流downside|平衡commit|风险资格|','|---|---:|---:|---:|---:|---|'])
    for z in rows(ROOT/'E0_MAIN_TABLES/RESULTS_BY_ARM.csv'):report.append(f"|{z['arm']}|{float(z['balanced_mse']):.10g}|{float(z['worst_harmful']):.6%}|{float(z['worst_downside']):.9g}|{float(z['balanced_commit']):.6%}|{z['feasible']}|")
    pair=next(z for z in rows(ROOT/'E0_MAIN_TABLES/PAIRED_MSE_ALL_BASELINES.csv')if z['baseline']=='DUAL_MEAN__g12')
    report.append(f"\n原Main相对已观测合格主动对照Dual的改善为{float(pair['relative_improvement']):.6%}，中心配对差区间[{pair['lower95']},{pair['upper95']}]，{pair['center_wins']}/{pair['centers']}中心胜出。比较对象来自原Final合格池的选择，未解决选择不确定性或多比较问题。")
    write('RAVM_JOINT_ALL_EXPERIMENTS_REPORT_ZH.md','\n'.join(report)+'\n');return go
if __name__=='__main__':run()
