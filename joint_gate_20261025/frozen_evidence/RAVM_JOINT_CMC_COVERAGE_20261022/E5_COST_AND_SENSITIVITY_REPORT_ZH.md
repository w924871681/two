# E5 科研结果与边界
总体覆盖裁决：`COVERAGE_COMPLETE_WITH_NEGATIVE_FINDINGS`。下表只汇总独立审计通过的数据；未完成/未验证对象在覆盖矩阵中列明。

|组别|状态|有效轨迹/计时复本|方法阶段|风险超标流|零活动流|
|---|---|---:|---:|---|---|
|E5_COST_R1|PASS|12|288|无/未获得完整结果|无/未获得完整结果|
|E5_COST_R2|PASS|12|288|无/未获得完整结果|无/未获得完整结果|
|E5_COST_R3|PASS|12|288|无/未获得完整结果|无/未获得完整结果|

## E5_COST_R1
独立单位：center；种子 [7311]；阶段数 24。原始指标为该任务目标的平方单位；温度另提供 °C²，不跨尺度合并。
完整数据：`E:\RAVM_JOINT_CMC_COVERAGE_20261022_storage\statistics\E5_COST_R1`。

|流|Joint MSE|harm/机会|harm频率|downside|commit|有益提交recall|
|---|---:|---:|---:|---:|---:|---:|
|clean|0.00339984265|0/24|0.000000%|0|16.666667%|0.16666666666666666|

所有方法的正负比较见 METHOD_STREAM.csv、CENTERS.csv、PAIRED_ALL_BASELINES.csv，不能只引用上表。成本来自实际墙钟；Service评价另列，审计不调用优化器。

## E5_COST_R2
独立单位：center；种子 [7311]；阶段数 24。原始指标为该任务目标的平方单位；温度另提供 °C²，不跨尺度合并。
完整数据：`E:\RAVM_JOINT_CMC_COVERAGE_20261022_storage\statistics\E5_COST_R2`。

|流|Joint MSE|harm/机会|harm频率|downside|commit|有益提交recall|
|---|---:|---:|---:|---:|---:|---:|
|clean|0.00339984265|0/24|0.000000%|0|16.666667%|0.16666666666666666|

所有方法的正负比较见 METHOD_STREAM.csv、CENTERS.csv、PAIRED_ALL_BASELINES.csv，不能只引用上表。成本来自实际墙钟；Service评价另列，审计不调用优化器。

## E5_COST_R3
独立单位：center；种子 [7311]；阶段数 24。原始指标为该任务目标的平方单位；温度另提供 °C²，不跨尺度合并。
完整数据：`E:\RAVM_JOINT_CMC_COVERAGE_20261022_storage\statistics\E5_COST_R3`。

|流|Joint MSE|harm/机会|harm频率|downside|commit|有益提交recall|
|---|---:|---:|---:|---:|---:|---:|
|clean|0.00339984265|0/24|0.000000%|0|16.666667%|0.16666666666666666|

所有方法的正负比较见 METHOD_STREAM.csv、CENTERS.csv、PAIRED_ALL_BASELINES.csv，不能只引用上表。成本来自实际墙钟；Service评价另列，审计不调用优化器。

16个开发配置敏感性见 E0_MAIN_TABLES/DEVCAL_JOINT_RESULTS_BY_ARM.csv 和 BY_STREAM.csv；未用新Final选参。同状态合法分歧见 E0_FIGURE_SOURCE_DATA。
开发三指标MSE/harm/downside的非支配配置为 9/16，完整表E5_DEV_PARETO.csv；冻结所选配置的Pareto状态不改变本轮方法锁。
重复成本固定同一Main输入、同一初始模型、三个复本、12方法；这是明确计入新增预算的计时复本，不计入新增科学样本。每个ready集合只有一个生命周期以统一计时边界，仍经动态资源准入。统一组件计时文件 COST_UNIFIED_*.json 包含准备/适配、Verification和门控、模型持久化、其余封存、维护总耗时、独立Service评价、CPU RSS端点、GPU进程峰值与原生缓冲字节。共享主机墙钟不证明能耗或普遍复杂度。
