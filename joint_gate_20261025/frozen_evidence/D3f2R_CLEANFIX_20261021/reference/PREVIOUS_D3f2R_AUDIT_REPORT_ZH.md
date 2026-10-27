# D3f2R 阶段A只读风险归因报告

## Material Passport

原回传包 `6c0c2038b714fe03508bb0daf8f8da23560ed333fa02921dd06f52d264cfea08`；原执行锁 `93dcfcbe22ace30989c611ca38aa3654257e4c088d7ca03f2d5327de420ad9d9`；原DevCal选型锁 `eb3ff207b5290305c95f0fc28910455e3685d49ed0ee6da3d0e04c122855600c`。独立本地进程重新前向计算全部432轨迹/10,368阶段；逐行CSV、模型身份、24阶段状态继承、动作封存、签名和Service先后顺序全部核实。使用原认证库；这不等于外部第三方或现场审计。

## 原值复算

Joint平衡MSE 0.0038761651506117939；MWU g04 0.0040661031778452322；RecentMean g12 0.0038771130025452294。数值来自原STAGE_RECORDS.csv，且全部逐行与原JSON及重新计算前向结果对齐。

| 流 | 有害/机会 | harm | downside | 5%允许次数 | 超额次数 | 资格 |
|---|---:|---:|---:|---:|---:|---|
| clean | 11/576 | 1.909722222% | 5.27693636185e-06 | 28 | 0 | True |
| mixed | 22/576 | 3.819444444% | 1.0848379639e-05 | 28 | 0 | True |
| coherent_sticky | 29/576 | 5.034722222% | 2.00712765945e-05 | 28 | 1 | False |

coherent_sticky中576×5%=28.8，整数资格最多28次，实际29次，精确超额1次（0.034722个百分点）。原STOP_CONFIRM绝不追溯更改。三个流downside均未超预算。

## 风险事件与状态分叉

全部Joint有害提交62次，逐事件见RISK_ATTRIBUTION_ALL_EVENTS.csv；完整1728机会见results/JOINT_ALL_OPPORTUNITIES_AUDIT_ONLY.csv，包含父/候选文件及状态哈希、近期均值、MWU p、原联合评分和动作条件。Service差值均标记AUDIT_ONLY。

严格同状态要求父与候选的state_hash及file_sha256均一致；仅这些行可比较单阶段动作。其他行只报告独立部署轨迹及首次分叉位置，不解释为同状态因果作用。

与RecentMean同状态关系计数：`{"strict_same_parent_and_candidate": 542, "reduced_harmful_commit_same_state": 16, "missed_beneficial_commit_same_state": 21, "added_harmful_commit_same_state": 5, "added_beneficial_commit_same_state": 25}`。与MWU同状态关系计数：`{"strict_same_parent_and_candidate": 536, "reduced_harmful_commit_same_state": 0, "missed_beneficial_commit_same_state": 0, "added_harmful_commit_same_state": 20, "added_beneficial_commit_same_state": 45}`。具体减少哪些有害更新、错过哪些有益更新见REDUCED_OR_MISSED_MATCHED_EVENTS.csv。若轨迹已分叉，后续损失差不能归因给本阶段门控。

中心/阶段/流/工况的全部机会分母与事件份额见HARM_CONCENTRATION.csv；时间窗1–3、4–6、7–12、13–18、19–24仅用于描述，不构成新阈值或显著性检验。

center_id有害次数最高三项：60018=20次，占32.26%; 60015=8次，占12.90%; 60019=8次，占12.90%。
stage有害次数最高三项：3=8次，占12.90%; 7=6次，占9.68%; 11=6次，占9.68%。
clean流中心有害次数最高三项：60018=7/72; 60016=2/72; 60015=1/72。全部中心及分母公开，集中程度只作描述。
mixed流中心有害次数最高三项：60018=6/72; 60015=4/72; 60019=4/72。全部中心及分母公开，集中程度只作描述。
coherent_sticky流中心有害次数最高三项：60018=7/72; 60017=4/72; 60019=4/72。全部中心及分母公开，集中程度只作描述。

冷启动1–3阶段有害13/216；其余各窗公开于CSV。无排除中心、阶段或种子。

## 风险合格MWU的效用对照

Joint相对MWU改善4.671254%，配对中心差-0.000189938027233，95%区间[-0.000345672293036, -7.09975128201e-05]；8/8中心改善。4000次固定种子20261020中心簇bootstrap；三个模型种子不当独立中心。
逐一剔除单中心的改善范围3.859429%—5.003358%，仅作少数中心依赖诊断，不重选中心或改变GO。完整中心数据见A_CENTER_UTILITY_VS_MWU.csv。

## 审计与科研边界

当前复核未发现配置、身份、状态继承、当前Service提前访问、动作封存或基线不公平的阻断；具体证据以A_ORIGINAL_REAUDIT.json为准。原始模拟提供器和本地签名构成受信执行审计，不宣称OS级恶意代码隔离。A阶段没有SGD，没有重新训练旧Confirm。

统计谬误11/11检查：分流报告避免合并掩盖；中心与事件单位区分；无筛掉高风险中心或完成者偏差；不以事后风险筛选当独立确认；无碰撞变量回归；harm分母为全部机会而非提交数；不把极端中心回归均值当改进；全部对照和负结果公开；归因均为事后探索；不同状态禁止单阶段因果解释；动作先于Service且不倒置因果。次级中心/阶段分解不作多重比较显著性声明。

阶段A只为资源授权。是否启动阶段B由audit_go_no_go.py逐项机械判定；不能据此声称联合规则通过原Confirm。若获GO，阶段B是观察旧Confirm后单独锁定的新中心前瞻性开发研究，不是未见Final。
