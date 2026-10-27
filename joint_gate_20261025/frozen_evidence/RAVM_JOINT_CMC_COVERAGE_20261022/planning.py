"""Protocol-facing provenance and reviewer mapping, without scientific results."""
from common import *
import re
text=(ROOT/'assets/ORIGINAL_REVIEWER_COMMENTS.md').read_text(encoding='utf-8-sig')
sections={name:body for name,body in re.findall(r'## (Reviewer[123])\s*\n(.*?)(?=\n## |\Z)',text,re.S)}
r1=[x.strip() for x in re.findall(r'^- (.*?)(?=\n- |\Z)',sections['Reviewer1'],re.M|re.S)][1:]
r2=[x.strip() for x in re.findall(r'^\d+\. (.*?)(?=\n\d+\. |\Z)',sections['Reviewer2'],re.M|re.S)]
r3=[x.strip() for x in re.findall(r'^\d+\. (.*?)(?=\n\d+\. |\Z)',sections['Reviewer3'],re.M|re.S)]
assert [len(r1),len(r2),len(r3)]==[2,12,2]
comments=[(f'R1.{i+1}',x)for i,x in enumerate(r1)]+[(f'R2.{i+1}',x)for i,x in enumerate(r2)]+[(f'R3.{i+1}',x)for i,x in enumerate(r3)]
mapping={'R1.1':'E3/E4及适用边界','R1.2':'E0既有ValidationCommit冻结回退与全部基线结果',
    'R2.1':'E0同状态门控行为；方法贡献边界','R2.2':'E0及E3的完整12方法比较','R2.3':'E0/E5冻结DevCal 16配置及阈值来源',
    'R2.4':'E1污染强度/类型；E3原始外部数据；不得推导现场发生率','R2.5':'E3/E4时序、Service成熟与监督角色说明',
    'R2.6':'E0-E4经验风险与总体保证的区别','R2.7':'E3真实外部结果与负结果','R2.8':'E0-E5风险—效用—活动性与成本',
    'R2.9':'全部协议、源码哈希、权重索引、实际账本和复算代码','R2.10':'跨任务结果与COVERAGE裁决，收窄泛化边界',
    'R2.11':'E5开发敏感性；不使用Final选参','R2.12':'最终图表与符号检查，仅输出修改位置建议','R3.1':'原稿Fig.5引文位置建议；本轮不修改稿件','R3.2':'原稿[32]数据引用身份与完整性核对；本轮不改文献'}
lines=['# 原始16条英文审稿意见证据矩阵','',f'原文来源：assets/ORIGINAL_REVIEWER_COMMENTS.md；SHA256 `{sha(ROOT/"assets/ORIGINAL_REVIEWER_COMMENTS.md")}`。',
    '原稿概述不另算问题；R1两项、R2十二项、R3两项，共16项。以下是待逐阶段更新的证据映射，不代表审稿人接受。','',
    '| Reviewer ID | 原文意见 | 现有证据 | 新补充证据 | 论文修改位置建议 | 是否真正解决 | 未解问题 |',
    '|---|---|---|---|---|---|---|']
records=[]
for id,comment in comments:
    record=dict(reviewer_id=id,original_comment=comment,evidence_plan=mapping[id],status='PENDING_EVIDENCE_NOT_ACCEPTANCE')
    records.append(record)
    lines.append('| '+id+' | '+comment.replace('|','\\|').replace('\n',' ')+' | 已完成Main Final，仅按适用范围使用 | '+mapping[id]+' | 完成后给出段落级建议 | 待核验 | 新Joint扩展/外域尚未执行，不能用旧方法结果冒充 |')
(ROOT/'06_REVIEWER_16_EVIDENCE_MATRIX.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
atomic(ROOT/'assets/REVIEWER_16_SOURCE.json',dict(source_sha256=sha(ROOT/'assets/ORIGINAL_REVIEWER_COMMENTS.md'),count=16,rows=records))
(ROOT/'04_DATA_ROLE_AND_CAUSAL_AUDIT.md').write_text('''# 数据角色与因果审核边界

状态：PREFLIGHT_IN_PROGRESS；本文件为执行前约束，不是新实验已通过的声明。

Update只用于合法候选适配；Verification只用当前可见监测数据；Service必须在部署动作持久Seal之后开放。上阶段Service成熟后可以成为后续Update；不得误要求所有阶段原始行完全不重叠。在线Gate不得访问当前未来Service、污染真值、工况真值或事后有害标签。

合成原处理器spans(t)：v=1400+(t-1)*640；第一Update=[1000,1400)，以后=[v-400,v)，Verification=[v,v+240)，Service=[v+240,v+640)。24阶段最后Service结束于16760。Warmup=[0,800)，初始Verification历史=[800,1000)。H4窗口仍按原96步lookback和4步目标生成，边界依原block_indices处理，不把重叠窗口视作独立中心。

E1污染入口必须复用原attack，Mixed作用于Update+Verification，Persistent bias与Replay按原严重度工程的verification_only语义认证。Service保持独立封存后的评价来源。Replay必须来自已过去的warmup原始序列并核对来源时间。

E2每个中心/种子/架构/H只初始化一次M0，并由全部比较方法独立继承；不能共享后续候选或部署状态。H1/H4的分数按同一冻结公式计算，不按新结果改lambda、margin、窗口权重或MWU方向。

E3先核验原始Alibaba归档、40机器身份与原预处理输出，保持不规则原时间、七遥测值和mask、缺失值规则与单位；24阶段只是原接口待认证的值，不在认证前当已通过事实。该批原外部机器已在历史论文中使用，应标明既有外域暴露，不冒充新的盲测现场验证。

E4单住宅与两个实验屋按原真实时间切分、通道、标准化及checkpoint身份核验。窗口、房间与种子不当作新的独立住宅/实验站。原source缺失即BLOCKED_ASSET，不重新编造权重。

E0/E5同状态决策分歧只在相同父模型、候选和Verification证据上计算；不同部署链的结果只作各自生命周期比较。成本重复测量若需候选适配，单独封存预算并计入成本测量账本，不冒充新Main科学样本，不覆盖原训练记录。
''',encoding='utf8')
(ROOT/'07_EXECUTION_PLAN_ZH.md').write_text('''# Joint Gate 补充实验执行计划

本轮由独立本地Python Owner及吞吐调度器驱动，无十五分钟模型监督，也不创建定时LLM任务。最新状态每秒持久化，网页每2秒读取；每个完成任务单元产生可恢复回执。

1. 全局只读Preflight：登记ZIP身份、全部CAS权重、14页原稿及26/27/8页历史返修基线、原16条意见、源码、数据处理器、18个模型/H checkpoint和新中心历史身份。身份不匹配阻断依赖读取。
2. E0只读复用主Final与DevCal：新表、良性工况活动率/recall、全部基线正负结果、同状态门控分歧和图表替换映射，训练步数0。
3. 认证并封存E1/E2/E3/E4扩展执行器及各项实际预算。缺失接口不得仅因有文件就标PASS。E3外部数据认证优先。
4. 工程Smoke使用事前指定的小子集，并计入完整矩阵；仅以身份、因果、形状、完成性判定。MSE或风险差不得停止其余合法条件。
5. 完成E1/E2/E3/E4各自合法独立矩阵；已完成且回执匹配的轨迹跳过。未封存/部分优化器调用不得盲重试。BLOCKED/INVALID只影响依赖项，其余继续。
6. E5使用冻结开发敏感性、同状态决策行为和独立预算的成本重复测量；不根据Final重选参数。
7. 原样保留全部不利结果，最终裁决COVERAGE_COMPLETE、COVERAGE_COMPLETE_WITH_NEGATIVE_FINDINGS或COVERAGE_BLOCKED；不自动修改或上传论文。
8. 全阶段的输入哈希、训练、审计、统计分组、模型索引、压缩、CRC/成员SHA、整包SHA接入同一资源/实测吞吐调度器。有序验证拆成单项任务并明确显示，不能用增加worker伪称其并行。

资源：启动前工程检查默认保留2 GiB可用RAM；worker准入/保留1.5 GiB，叠加每worker RAM/VRAM实测上界。吞吐只用真实完成工作，不用MSE/风险选并发；>5%退化回滚，按5/10/20/30分钟重新探测，无永久低并发封顶。

D盘只保留协议、代码、表和索引；新增大产物在E:/RAVM_JOINT_CMC_COVERAGE_20261022_storage，至少保留2 GiB磁盘余量。既有Main、旧论文和历史P0/DevCal/Confirm不覆盖。

交付包括完整回传包与小于512,000,000字节的GPT审阅包。外置CAS提供精确字节/哈希/成员清单，不宣称轻量包含全部模型。可缺失项目必须明确列为缺口，不能补造通过。
''',encoding='utf8')
print('Prepared 16 original reviewer mappings and explicit causal/execution constraints; no training')
