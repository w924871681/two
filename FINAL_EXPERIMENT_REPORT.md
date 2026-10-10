# 实验执行报告（进行中，非最终科学结论）

更新时间：2026-09-08T23:05:00（本机时间）。

## 当前状态

已开展实际实验。P0–P5 已完成并冻结。旧单进程 P6 的 23,039 条轨迹和后续双进程 P6 的 795 条完整轨迹均已分别封存，只作 reference/cache asset；`results/calibration/` 为空，未进入 heldout。Joint-policy DAG 已获得人工批准并正式接入 P6 runner，当前正在执行提交前检查，随后重跑 mandatory scientific audits 并启动两个完整 workload worker。P0–P5 只作完整性与冻结哈希核验，不重新运行。

- 独立项目：`D:/dt-trustworthy-maintenance`
- 实现提交：`6b685453b1c36b4dfa5ca91ecee71c4cd971f909`
- 第一篇复用提交：`b679181b3133ab9c3058afcde421d36380001f14`（v1.2.7）
- Python：`C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe`
- PyTorch：`2.5.1+cu121`
- GPU：`NVIDIA GeForce RTX 3060 Laptop GPU`
- 正式队列：joint-policy DAG 正式接入完成，启动前审计中；原 PID `6848`、worker PID `33536/20868` 均不再运行
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

后续 joint-policy DAG 审计覆盖 5 policies、20 policies、all 400 policies、abrupt/recurring 与 clean/mixed，10,680 行结果的 50 个科学字段全部逐位一致，最大浮点差为 0。首次 all-400 workload 从 622.73 秒降至 133.17 秒；完整报告见 `JOINT_DAG_ACCELERATION_REPORT.md`。按用户要求，报告完成后没有自行启动完整 P6。

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

<!-- FORMAL_EXECUTION_STATUS_START -->
## 正式执行状态

更新时间：2026-09-10T13:04:00.907617

阶段：**P16 完成**

完整正式实验、图表、4,000 次中心聚类 bootstrap 与最终复现审计均已完成。
<!-- FORMAL_EXECUTION_STATUS_END -->

## Q2 执行分母只读审计（2026-09-09 10:03 +08:00）

本次审计未暂停、重启或修改正在运行的 heldout runner。审计结论是：此前报告的 `3360` 以及随后更正的 `6720` 都不是正式 Q2 矩阵的真实分母；启动前冻结并由当前 runner 一直执行的 Q2 完整矩阵为 **7680 条完整轨迹**：

```text
3 seeds × 20 centers × 16 unique conditions × 8 methods = 7680
```

16 个唯一条件由两部分组成：主 sweep 为 `4 attack types × 3 alpha × location=both = 12`；location sensitivity 为 `2 attack types（persistent_bias、replay）× alpha=0.10 × 2 个额外位置（update_only、verification_only）= 4`。规范中的 `both` 已包含在主 sweep，执行代码不会重复生成它，因此总数为 `12 + 4 = 16`。

`audits/final_freeze.json` 没有展开列出 7680 个键，但在 heldout 启动前冻结了 `scripts/run_heldout.py` 和 `scripts/final_reproducibility_audit.py`。前者从一开始生成上述 16 个条件并排除仅用于离线诊断的 OracleCommit；后者明确要求 `q2_security = 3*20*16*(len(METHODS)-1)`。当前文件 SHA-256 与 final freeze 中的值逐项一致：`scripts/run_heldout.py`、P16 完整性审计、`core/engine.py`、`core/protocol.py`、`core/models.py`、三份 frozen config 及 `pool_manifest.json` 均无变化。Git 历史也没有显示 `run_heldout.py` 在 Q2 启动前后发生修改。

此前的 `3360` 来自监控回复中的手工计算错误：先把额外 location sensitivity 的 4 个组合误当作 2 个，并在计算 `3 × 20 × 14 × 8` 时又少计了一个因子 2。随后给出的 `6720` 修复了算术错误，但仍沿用了错误的 14-condition 假设。`logs/execution_status.json` 只记录阶段、最近完成文件和 heldout 状态，不保存或驱动 denominator；这两个数字均未进入 runner、任务矩阵或结果文件。**reporting-only issue; scientific execution matrix unchanged**。

在 10:03:22 的只读快照中，Q2 已完成 4791/7680 条完整轨迹。逐方法覆盖如下；每条完整轨迹 CSV 均含 24 个互不重复的 stage 行。

| Method | Expected trajectories | Completed | Remaining | 历史平均 trajectories/hour |
|---|---:|---:|---:|---:|
| Frozen | 960 | 599 | 361 | 6714 |
| Always-FT | 960 | 599 | 361 | 1040 |
| ER | 960 | 599 | 361 | 980 |
| EWC | 960 | 599 | 361 | 521 |
| Huber-FT | 960 | 599 | 361 | 1040 |
| CLeaR-Predictor | 960 | 599 | 361 | 1195 |
| ValidationCommit | 960 | 599 | 361 | 1015 |
| Proposed | 960 | 598 | 362 | 686 |

唯一键按 `seed × center × attack_type × alpha × attack_location × method` 重建。快照中的 4791 个文件有 4791 个唯一键：重复键 0、计划外键 0、已完成前缀内缺口 0；其余 2889 个键均位于尚未执行的计划后缀，没有漏跑、重复执行或动态扩充迹象。对截至 10:00 已完成的 4759 个文件进一步读取内容后确认：每文件均为 24 个且仅有 stage 1–24，文件名与 CSV 内 seed/center/condition/method 元数据不一致为 0，跨方法的 `update_data_hash`、`verification_data_hash`、`service_data_hash`、`attack_mask_hash` 不一致组数为 0。

20 个 Q2 heldout 数据文件均在 Q2 首条结果（05:03:55）之前生成，Q2 运行期间未见文件时间变化；加上跨方法数据与攻击哈希完全一致，可确认当前已执行范围内的数据和条件没有在 Q2 启动后改变。冻结配置、seeds、centers、conditions、methods 及核心实现的冻结哈希也全部保持一致。不存在漏跑 4 个方法、中途增加方法、修改 execution matrix 或动态扩充 heldout 任务。

逐方法平均吞吐按相邻完整轨迹文件的完成时间差计算，包含生命周期计算与落盘时间。八种方法按固定顺序循环；EWC（约 521/h）和 Proposed（约 686/h）较慢，Frozen（约 6714/h）较快，其余方法约 980–1195/h。按各方法实际平均耗时合成的平衡循环吞吐约 965 trajectories/hour，因此短窗口出现约 1040/h 到 924/h 的变化与 condition 耗时、方法边界和系统调度波动一致，不表示矩阵或协议改变。10:03 快照最近完成的是 ValidationCommit，下一计划项、即当时正在进入执行的 method 为 Proposed。

## POST-Q2 Execution Benchmark（2026-09-09）

限定范围 benchmark 使用正式 Q2 的 Python/CUDA 环境，重放 2 centers × 2 conditions × 1 seed × 4 methods，共 16 条完整 24-stage lifecycle/variant。A、B、C、D 均仅写入 `scratch/post_q2_executor_benchmark/`；D 只在同轮 B、C 均超过 1.03× 筛选线后执行。64 个 formal Q2→A 与 A→B/C/D trajectory 比较全部 PASS，最大浮点差为 0；Q1/Q2 目录清单、scientific core、frozen config 均未改变，Q3 正式输出为 0。

权威 I/O 完整轮中，A 为 605.5 trajectories/hour，B 为 1089.5/h（1.800×），C 为 665.0/h（1.098×），D 为 1160.2/h（1.916×）。前一轮有效 CUDA wall-clock 中，B 为 1.703×，C 为 0.938×。因此 B 的收益可重复，而 C 的小幅收益方向不稳定；D 相对 B 仅再提高 1.065×，峰值 GPU 显存从 618 MiB 增至 1288 MiB。推荐 **B：两个独立 workload workers**，每个 worker 只处理完整 `center × condition × seed × method` lifecycle，24 stages 保持串行。正式切换仍需人工决定。

按本次测得速度，Q3–Q6 加 Alibaba direct/diagnostic 的单策略部分采用 B 预计约 5.87–6.21 小时；Alibaba calibration 保留此前已验证 joint-DAG 的 0.54–2.03 小时估计。合计剩余约 6.41–8.24 小时，相比 A 预计节省约 4.36–4.70 小时。完整结果见 `POST_Q2_EXECUTION_BENCHMARK.md` 与 `audits/post_q2_execution_benchmark.json`。状态已设为 `WAITING_FOR_MANUAL_EXECUTOR_DECISION`。

<!-- FINAL_SCIENTIFIC_RESULTS_START -->
## Final scientific results

Generated: 2026-09-10T13:04:00.792116

- Exact final git commit: `0a21cf6f7bdf068ab64b8e5ef0f5e2e8bfb95e2e`
- Environment: Python 3.11.15, PyTorch 2.5.1+cu121, GPU NVIDIA GeForce RTX 3060 Laptop GPU
- Frozen candidate config SHA-256: `4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea`
- Frozen commit config SHA-256: `1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a`
- Frozen baseline config SHA-256: `765f58a595a156320caa3c4664657670968d4638e5bf15b7d430444b82581908`
- Frozen commit configuration: `{"delta_imp": 2.8018237766243602e-05, "delta_ret": 0.0, "kappa_hist": 0.0, "kappa_rec": 0.5, "validation_retain_all": true}`
- No-leakage/pre-heldout audit: `approved_by_implementation_audit`
- Final reproduction status: `passed`

### Q1 main metrics with 95% center-cluster confidence intervals

| attack_type | method | lifecycle_mse | lifecycle_mse_ci_low | lifecycle_mse_ci_high | harmful_commit_rate | harmful_commit_rate_ci_low | harmful_commit_rate_ci_high | average_downside | average_downside_ci_low | average_downside_ci_high | commit_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | Always-FT | 0.00311249 | 0.00226841 | 0.00402386 | 0.237963 | 0.209259 | 0.26713 | 2.83561e-05 | 1.47408e-05 | 4.78126e-05 | 1 |
| clean | EWC | 0.00311351 | 0.00226923 | 0.00402546 | 0.238889 | 0.210185 | 0.267593 | 2.79179e-05 | 1.45212e-05 | 4.72158e-05 | 1 |
| clean | OracleCommit | 0.00312155 | 0.00227567 | 0.00403478 | 0 | 0 | 0 | 0 | 0 | 0 | 0.765741 |
| clean | ER | 0.00329607 | 0.00237492 | 0.0042849 | 0.162037 | 0.137488 | 0.1889 | 1.4545e-05 | 5.3613e-06 | 2.76879e-05 | 1 |
| clean | Huber-FT | 0.00333878 | 0.00241835 | 0.00434522 | 0.243519 | 0.213426 | 0.274074 | 2.7368e-05 | 1.34382e-05 | 4.61694e-05 | 1 |
| clean | CLeaR-Predictor | 0.00369375 | 0.00272073 | 0.00473563 | 0.209722 | 0.19213 | 0.227778 | 0.00021339 | 0.000151746 | 0.000282664 | 0.474074 |
| clean | Proposed | 0.00389542 | 0.00280326 | 0.00506634 | 0.0171296 | 0.0101852 | 0.025 | 8.60612e-07 | 4.04961e-07 | 1.41512e-06 | 0.211111 |
| clean | Frozen | 0.00524122 | 0.00365362 | 0.00694205 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| clean | ValidationCommit | 0.00524122 | 0.00365362 | 0.00694205 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| mixed | OracleCommit | 0.00322886 | 0.00237333 | 0.00414962 | 0 | 0 | 0 | 0 | 0 | 0 | 0.508333 |
| mixed | EWC | 0.0032648 | 0.00240867 | 0.00418308 | 0.422222 | 0.393056 | 0.452315 | 0.000120104 | 7.78977e-05 | 0.000176753 | 1 |
| mixed | Always-FT | 0.00326579 | 0.00240977 | 0.00418276 | 0.423611 | 0.394444 | 0.453241 | 0.000122552 | 7.97858e-05 | 0.00018027 | 1 |
| mixed | ER | 0.00334597 | 0.00242847 | 0.0043197 | 0.248611 | 0.219907 | 0.277778 | 2.69918e-05 | 1.54352e-05 | 4.25569e-05 | 1 |
| mixed | Huber-FT | 0.00341472 | 0.00247632 | 0.00443702 | 0.365741 | 0.338889 | 0.392593 | 6.20637e-05 | 3.42185e-05 | 9.92726e-05 | 1 |
| mixed | Proposed | 0.00398087 | 0.00287283 | 0.00516022 | 0.0375 | 0.0291667 | 0.0462963 | 4.00558e-06 | 2.53596e-06 | 5.73245e-06 | 0.205556 |
| mixed | CLeaR-Predictor | 0.00485128 | 0.00395382 | 0.00579052 | 0.165741 | 0.148611 | 0.184259 | 0.000488664 | 0.000401715 | 0.000578525 | 0.334722 |
| mixed | Frozen | 0.00524122 | 0.00365362 | 0.00694205 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| mixed | ValidationCommit | 0.00524122 | 0.00365362 | 0.00694205 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### Contribution assessment

```json
[
  {
    "condition": "clean",
    "reference": "Always-FT",
    "metric": "deployed_service_mse",
    "difference": 0.0007829327793539,
    "ci": [
      0.0004990253859317,
      0.0011134287946603
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "clean",
    "reference": "Always-FT",
    "metric": "harmful_commit",
    "difference": -0.2208333333333333,
    "ci": [
      -0.250462962962963,
      -0.1907407407407407
    ],
    "verdict": "supported"
  },
  {
    "condition": "clean",
    "reference": "Always-FT",
    "metric": "downside",
    "difference": -2.7495516641698925e-05,
    "ci": [
      -4.683506689009797e-05,
      -1.4032690079246967e-05
    ],
    "verdict": "supported"
  },
  {
    "condition": "clean",
    "reference": "ValidationCommit",
    "metric": "deployed_service_mse",
    "difference": -0.0013457940296642,
    "ci": [
      -0.0019834641876567,
      -0.0007524958633419
    ],
    "verdict": "supported"
  },
  {
    "condition": "clean",
    "reference": "ValidationCommit",
    "metric": "harmful_commit",
    "difference": 0.0171296296296296,
    "ci": [
      0.0101851851851851,
      0.0249999999999999
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "clean",
    "reference": "ValidationCommit",
    "metric": "downside",
    "difference": 8.606121506696153e-07,
    "ci": [
      4.049614600026394e-07,
      1.4151236771590756e-06
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "Always-FT",
    "metric": "deployed_service_mse",
    "difference": 0.0007150806330173,
    "ci": [
      0.0004267342886992,
      0.0010386632706764
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "Always-FT",
    "metric": "harmful_commit",
    "difference": -0.386111111111111,
    "ci": [
      -0.4106597222222222,
      -0.361574074074074
    ],
    "verdict": "supported"
  },
  {
    "condition": "mixed",
    "reference": "Always-FT",
    "metric": "downside",
    "difference": -0.0001185465454976,
    "ci": [
      -0.0001763243613575,
      -7.55953697371519e-05
    ],
    "verdict": "supported"
  },
  {
    "condition": "mixed",
    "reference": "ValidationCommit",
    "metric": "deployed_service_mse",
    "difference": -0.0012603453275207,
    "ci": [
      -0.0018708793821005,
      -0.0006903742336005
    ],
    "verdict": "supported"
  },
  {
    "condition": "mixed",
    "reference": "ValidationCommit",
    "metric": "harmful_commit",
    "difference": 0.0375,
    "ci": [
      0.0291666666666666,
      0.0462962962962962
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "ValidationCommit",
    "metric": "downside",
    "difference": 4.005583495771806e-06,
    "ci": [
      2.535958568572028e-06,
      5.73244663664026e-06
    ],
    "verdict": "contradicted"
  }
]
```

### Negative and inconclusive findings

ValidationCommit calibration used the preregistered retain-all fallback. Comparisons whose confidence interval crosses zero, or favors the reference, are retained below without suppression.

```json
[
  {
    "condition": "clean",
    "reference": "Always-FT",
    "metric": "deployed_service_mse",
    "difference": 0.0007829327793539,
    "ci": [
      0.0004990253859317,
      0.0011134287946603
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "clean",
    "reference": "ValidationCommit",
    "metric": "harmful_commit",
    "difference": 0.0171296296296296,
    "ci": [
      0.0101851851851851,
      0.0249999999999999
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "clean",
    "reference": "ValidationCommit",
    "metric": "downside",
    "difference": 8.606121506696153e-07,
    "ci": [
      4.049614600026394e-07,
      1.4151236771590756e-06
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "Always-FT",
    "metric": "deployed_service_mse",
    "difference": 0.0007150806330173,
    "ci": [
      0.0004267342886992,
      0.0010386632706764
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "ValidationCommit",
    "metric": "harmful_commit",
    "difference": 0.0375,
    "ci": [
      0.0291666666666666,
      0.0462962962962962
    ],
    "verdict": "contradicted"
  },
  {
    "condition": "mixed",
    "reference": "ValidationCommit",
    "metric": "downside",
    "difference": 4.005583495771806e-06,
    "ci": [
      2.535958568572028e-06,
      5.73244663664026e-06
    ],
    "verdict": "contradicted"
  }
]
```

### Baseline fidelity notes

- Frozen, Always-FT, ER, EWC, Huber-FT, ValidationCommit and Proposed were executed under their frozen configurations.
- CLeaR-Predictor is a declared predictor-only framework adaptation: `{"clear_capacity": 128, "clear_ewc_lambda": 200.0, "clear_factor": 0.75, "ewc_fisher_examples": 32, "ewc_gamma": 0.9, "ewc_lambda": 10.0, "huber_delta": 0.1}`.
- MER-Reg-2026 remains `implementation_unavailable_or_nonfaithful` and is not represented by a proxy.
- OracleCommit is an offline diagnostic and is excluded from deployable rankings.

### Outputs

Q1–Q6 tables, 4,000-replicate center-cluster bootstrap comparisons, figure-ready CSVs, publication figures, runtime/cost data and audit manifests are under `results/` and `audits/`.
<!-- FINAL_SCIENTIFIC_RESULTS_END -->
