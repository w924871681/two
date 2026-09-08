# 实验执行报告（进行中，非最终科学结论）

更新时间：2026-09-08T20:13:00（本机时间）。

## 当前状态

已开展实际实验。P0–P5 已完成：开发池的 1,560 条完整生命周期全部完成，候选配置冻结为 `B=5, beta=0.1`，基线配置也已冻结。P6 首次单进程校准运行到 23,039/48,600 条轨迹后，在可恢复边界主动停止并封存；加速实现已通过等价性与并发碰撞审计，双进程正式 P6 已从空结果目录重新启动。完整 Q1–Q6 结果尚未产生。

- 独立项目：`D:/dt-trustworthy-maintenance`
- 实现提交：`6b685453b1c36b4dfa5ca91ecee71c4cd971f909`
- 第一篇复用提交：`b679181b3133ab9c3058afcde421d36380001f14`（v1.2.7）
- Python：`C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe`
- PyTorch：`2.5.1+cu121`
- GPU：`NVIDIA GeForce RTX 3060 Laptop GPU`
- 当前正式队列 PID：`6848`；两个校准工作进程 PID：`33536`、`20868`
- 执行日志：`logs/full_console.log`；错误日志：`logs/full_stderr.log`
- 机器可读进度：`logs/execution_status.json`（每条生命周期完成后更新）

## 已完成的实际工作

1. 单独建立 Git 项目，第一篇冻结目录保持只读，保存复用文件与 SHA-256 来源记录。
2. 生成 20 个 source、20 个 development、20 个 calibration 中心，每中心 17000 条观测。未生成 synthetic heldout。
3. 检查已知两处历史结果中的 69 个带中心 ID 的 CSV：无新池 ID 冲突、无读取错误。扫描范围见 `audits/legacy_pool_scan.json`。
4. 运行 2 个开发中心 × 3 stages × 2 conditions × 8 methods，得到 96 条冒烟结果；另完成 CLeaR-Predictor 3-stage 冒烟。冒烟 checkpoint 明确隔离，不能用于正式结果。
5. 14 项基础协议测试通过，包括禁止决策前服务读取、原始段及窗口边界、污染上限、配对掩码、不可变服务数据、初始化/预算、拒绝候选、验证数据禁入梯度和中心聚类 bootstrap。此结果不等于 P16 最终复现审计完成。
6. 正式 GRU/H1/seed7311 源模型完成 50 epochs，耗时约 110 秒；后续种子由正式队列顺序训练。
7. Alibaba 原始归档 SHA-256 核验通过；已完成 246934820 条原始记录的统计与筛选，生成 100 台新机器的 source/development/calibration/heldout 划分。原始归档不修改。

## 加速变更与等价性证据

旧的部分校准结果、候选缓存和日志完整保存在 `archive/pre_acceleration_20260908_194751/`，不参与新一轮结果汇总。加速只改变物理执行：校准证据按父模型、候选模型、预测窗口和 horizon 的完整哈希复用；两个独立进程处理互斥的策略区间；每条生命周期内部仍保持 24 stages 串行。候选权重、证据缓存和攻击掩码均使用进程独立临时文件后原子替换，避免并发半写文件。

`audits/acceleration_equivalence.json` 对旧归档、无缓存、冷缓存和热缓存执行进行了比较。两个 24-stage 代表性轨迹的 45 个科学字段全部一致；旧 CSV 仅有不超过 `1e-14` 的十进制回读尾差，缓存与无缓存的内存结果逐位一致。`audits/cache_concurrency.json` 进一步验证两个进程同时发布同一缓存键时输出相同。代表性热缓存速度为原无缓存的约 2.67–11.71 倍。正式总耗时仍以重新启动后的实测吞吐动态估计。

## 用户确认的协议解释

- 在完整原始角色段内生成窗口，再按预测时间分块；允许相邻块共享输入上下文，目标时间不重叠。H4 会删除导致跨块目标重叠的边界窗口。
- 突发污染使用严格块比例上限下的块内短连续突发。实现以每角色段十个固定原始观测分层生成共用攻击掩码，不将其称为全段单次连续突发。

## 基线状态

| 方法 | 状态 |
|---|---|
| Frozen / Always-FT / ER / EWC / Huber-FT / ValidationCommit | 已实现并通过冒烟，正式结果待运行 |
| Proposed 及组件变体 | 已实现；Full 通过冒烟；正式配置待开发与校准 |
| CLeaR-Predictor | 明确标注的 predictor-only、stage-batched 框架适配，非原论文 autoencoder 实验的逐项复现 |
| MER-Reg-2026 | `implementation_unavailable_or_nonfaithful`；未提供冒名近似结果 |
| OracleCommit | 仅离线诊断，不进入可部署方法排名 |

文献核对来源：[CLeaR 原文](https://arxiv.org/html/2101.00926v3)、[MER-Reg-2026 原文](https://arxiv.org/html/2602.09720v1)。

## 执行队列与完成条件

队列按开发 → 候选冻结 → 400 个 Proposed 校准配置及 5 个 ValidationCommit 配置 → 校准冻结 → 进入 heldout 前审计 → Q1/Q2/Q3/Q4/Q5 → Q6 → 4000 次中心聚类 bootstrap 顺序执行。

校准候选缓存只保存训练产生的权重，不保存或读取服务标签/损失。审计将比较缓存与重新训练结果。每个校准配置拥有独立、依赖其实际提交历史的生命周期轨迹。约束不满足时保留 retain-all 失败结论。

若实现/数据/配置审计失败，队列停止并写入 `logs/execution_failure.json`，不将部分结果作为正式完成结果。P15 科研图表的读图校验和 P16 最终复现审计仍需在正式数据生成后完成。

## 科学结论

所有主指标、95% CI、三项贡献是否成立、负面发现：**待正式运行完成，当前不作结论**。

冻结配置哈希：**待 P5/P7 产生**。不使用 heldout 调参。
