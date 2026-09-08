# Joint-policy DAG acceleration report

生成时间：2026-09-08（Asia/Shanghai）  
状态：**诊断、实现、缓存迁移、科学等价性和 benchmark 均已完成；正式 P6 未启动，formal runner 未切换。**

## 决策

建议切换到 joint-policy DAG，并采用 **2 workers、按 center×condition×seed 完整 workload 分区、L1 RAM LRU + L2 persistent cache**。保守的首次 all-400 workload 实测加速已超过 2× 切换标准：DAG 为 10,813 trajectories/hour，相对当前 1,008/h 为 10.73×，相对旧成熟 1,290.95/h 为 8.38×。所有科学等价性与 leakage audit 均通过。

按照用户要求，本报告生成后停止；没有启动完整 P6，也没有把 DAG 接入 `run_all_final.py`。

## 1. Scientific protocol 是否变化

没有。数据划分、seeds、B=5、beta=0.1、threshold grid、candidate training、400 个 Proposed policies、5 个 ValidationCommit policies、24-stage causal lifecycle、攻击身份、窗口定义及 D_srv decision boundary 均未改变。

DAG 只复用完全相同的计算前缀。Causal fingerprint 包含：deployed model hash、ordered historical buffer hash、stage、center、condition、seed、horizon、update/verification/attack identity、candidate RNG seed、B、beta 和 rolling-state marker。不同 historical state 即使模型 hash 相同也不能 merge。静态 kappa/delta 参数继续逐 policy 保存，只把 gate 算术向量化。

## 2. P0–P5 是否完整保留

是。1,560 条 development trajectories 保持原位，冻结 candidate/baseline/calibration protocol 的 SHA-256 均通过。没有重新运行或覆盖 P0–P5。`results/calibration/` 当前为空，heldout 尚未创建或访问。机器审计见 `audits/joint_dag_protocol.json`。

## 3–5. 旧计算资产如何处理

- 旧单进程 23,039 条 P6：继续保存在 `archive/pre_acceleration_20260908_194751/`，只用于 reference、因果状态诊断和严格 cache migration；不会拼入 DAG final CSV。
- 双进程 P6：请求文本记录约 298 条，但安全快照时已经实际完成 795 条，全部保存在 `archive/pre_joint_dag_20260908_210552/`。状态文件停在 786，文件系统有 795 个完整原子 CSV。它们同样只作 reference/cache asset。
- 旧 cache：扫描 65,323 个 candidate 和 19,262 个 evidence 文件。57,397 个唯一 candidate 和全部 19,262 个 evidence 通过验证；7,926 个拒绝项全部是跨归档重复文件，没有 state/data/hash mismatch。复用约 1.494 GB，避免 57,397 次 candidate training 和 19,262 次 evidence computation。
- 验证条件包括 reference row provenance、重算 immutable data hash、重算 attack/mask identity、parent/config/seed/stage/horizon、candidate state hash、cache schema 和 science-source hashes。源归档未修改。

详见 `audits/cache_migration.json`。

## 6. 当前双进程为什么慢

双进程按 policy range 分区，却同时运行相同 center/seed/condition，导致相同 causal prefix 在两个进程中并发请求。19,080 个 candidate stage 请求只有 9,622 个唯一键，理论 cache hit 49.57%；两个 worker 有 840 个共同 candidate keys，占较小键集合的 16.31%。此前发生的同时 miss/cache publish 碰撞也直接证明了重复计算。

无缓存 reference 的 wall-clock 分解如下：

| 部分 | Wall time 占比 |
|---|---:|
| Candidate generation/training | 76.23% |
| Recent verification | 4.38% |
| Historical verification | 11.24% |
| Post-decision service evaluation | 1.21% |
| Python orchestration、hash、copy | 6.93% |

双进程正式归档的 trajectory 内部中位耗时中，candidate 占 61.26%，verification 占 37.39%，两者合计 98.65%。完全命中旧磁盘缓存时，模型反序列化约占 25.2% wall，evidence NPZ 读取约占 39.8%；因此 RAM hot cache 有实际价值。

单进程 profile 平均 GPU utilization 12.5–24.9%、峰值 36–40%、显存约 360 MB；旧双进程曾达到约 90% GPU utilization 和 822 MB 显存，却因同一 GPU 上的细粒度 kernel 争用、重复 miss、哈希/复制和小文件调度而没有提高总体吞吐。旧成熟单 worker 为 1,290.95/h，双进程归档仅约 1,064/h。

## 7. DAG 是否完全等价

是。最终代码重新执行以下 full-24-stage cases：

| Case | Policies | Drift/condition | Scientific rows | 结果 |
|---|---:|---|---:|---|
| five_abrupt_clean | 5 | abrupt / clean | 120 | PASS |
| twenty_abrupt_mixed | 20 | abrupt / mixed | 480 | PASS |
| twenty_recurring_clean | 20 | recurring / clean | 480 | PASS |
| all400_recurring_mixed | 400 | recurring / mixed | 9,600 | PASS |

每行比较 50 个科学字段。Parent/candidate/deployed hashes、commit sequence、deployed-state sequence、historical-buffer sequence、causal fingerprint、数据/攻击 hashes 和所有整数均 exact；全部浮点也 bitwise equal，最大绝对差为 **0.0**。14 项原协议测试再次通过。Candidate/evidence cache key 不含 service data，所有 decision timestamp 均早于 service start。

详见 `audits/joint_dag_equivalence.json` 与 `audits/joint_dag_protocol.json`。

## 全 400-policy causal-state trace

代表 workload：center 12003、recurring、mixed、seed 7311。完整 fingerprint 已包含 ordered historical state；下表不是仅按 model hash 统计。

| Stage | Naive policies | Unique complete causal states | Unique deployed states |
|---:|---:|---:|---:|
| 1 | 400 | 1 | 2 |
| 2 | 400 | 2 | 2 |
| 3 | 400 | 2 | 4 |
| 4 | 400 | 4 | 7 |
| 5 | 400 | 7 | 7 |
| 6 | 400 | 7 | 12 |
| 7 | 400 | 12 | 20 |
| 8 | 400 | 20 | 20 |
| 9 | 400 | 20 | 28 |
| 10 | 400 | 28 | 32 |
| 11 | 400 | 32 | 32 |
| 12 | 400 | 32 | 32 |
| 13 | 400 | 32 | 44 |
| 14 | 400 | 44 | 44 |
| 15 | 400 | 44 | 44 |
| 16 | 400 | 44 | 47 |
| 17 | 400 | 47 | 47 |
| 18 | 400 | 47 | 61 |
| 19 | 400 | 61 | 67 |
| 20 | 400 | 67 | 67 |
| 21 | 400 | 67 | 71 |
| 22 | 400 | 71 | 79 |
| 23 | 400 | 79 | 81 |
| 24 | 400 | 81 | 82 |

总计 9,600 个 naive candidate requests 只形成 851 个 unique complete causal states，减少 **91.14%** candidate/evidence state computations。

## 8–10. Executor benchmark

统一 workload：center 12002 与 12003、mixed、seed 7311、每个 400 policies×24 stages。稳态 benchmark 先补齐 persistent cache，预热本身不计入成绩。

| Executor | Throughput | Wall clock / 800 trajectories | Candidate training | Candidate hits | Evidence compute/hits | GPU mean/max | GPU memory max |
|---|---:|---:|---:|---:|---:|---:|---:|
| A. 旧成熟 reference | 1,290.95/h | 归档长区间 | — | — | — | — | — |
| B. 当前 dual-process cache | 1,064/h（用户基准 1,008/h） | 归档长区间 | — | — | — | 约 90% 峰值采样 | 822 MB |
| C. Joint DAG, 1 worker, L2 | 88,092/h | 32.69 s | 0 | 1,086 L2 | 0 / 2,172 L2 | 14.2% / 81% | 291 MB |
| D. Joint DAG, 2 workload workers, L2 | **135,567/h** | **21.24 s** | 0 | 1,086 L2 | 0 / 2,172 L2 | 14.7% / 97% | 849 MB |
| E. Joint DAG, 1 worker, RAM hot | 127,876/h | 22.52 s | 0 | 1,086 L1 | 0 / 2,172 L1 | 13.8% / 82% | 317 MB |

稳态最快的是 **D：joint DAG + 2 workload workers + L2**。L1 RAM 使单 worker 相对 L2 从 88,092/h 提高到 127,876/h；由于完整 DAG 工作集已在内存中，单 worker RAM-hot 略慢于两个 workload worker 并行。

这些完全预热数字不能直接当作全 P6 首次运行速度。更保守的首次 all-400 equivalence workload 同时包含 123 次新 candidate training 和 1,506 次新 evidence computation：reference 622.73 s，DAG 133.17 s，即 2,312/h 对 10,813/h，实际 **4.68×** 同 workload 加速。

## 11–12. 相对既有速度的提升

| 比较口径 | 相对 1,008/h | 相对 1,290.95/h |
|---|---:|---:|
| 首次 all-400、部分旧 cache 可复用（保守切换依据） | **10.73×** | **8.38×** |
| 完全预热 DAG 2-worker L2（稳态上限） | 134.49× | 105.01× |

切换建议使用第一行。它已经远高于 ≥2.0× 的“强烈建议切换”标准。

## 13. 完整 P6 时间估计

Synthetic Proposed 有 120 个 center×condition×seed workloads，共 48,000 个 policy trajectories；ValidationCommit 另有 600 条，继续使用 reference executor。按首次 DAG 实测速率与两个 workload worker 的并行收益估算：

- Proposed：约 2.8–4.5 小时；
- ValidationCommit、文件写入、汇总与审计：约 0.5–1.0 小时；
- 完整 synthetic P6：**约 3.5–5.5 小时**。

范围已经考虑 workload 间 causal-state 数差异和首次 cache miss；完全预热的 135,567/h 不用于该 ETA。

## 14. 整个剩余实验矩阵时间估计

后续还有 synthetic heldout/baselines、Alibaba direct transfer、Alibaba 独立 calibration、diagnostic、汇总和最终审计。Alibaba calibration 可使用相同 DAG，但缺少与 synthetic 等量的旧 cache，因此预计约 4–7 小时。其他约 15,000 条 baseline/heldout 轨迹包含较慢的 EWC/CLeaR，不能按 DAG 速度外推。

当前合理范围为 **约 24–48 小时**。主要不确定性已经从 Proposed calibration 转移到 EWC/CLeaR 等基线和大量小 CSV 写入；正式重启后应按阶段实测继续更新。

## 15. 仍可安全加速的空间

仍有，但不需要在切换前继续重构：

1. 组合 2 workload workers 与各自 RAM L1；本次分别测了双 worker L2 和单 worker L1，二者组合可能略快。
2. 对 service evaluation 做更大的模型/窗口 batch，但必须先证明逐位或 ≤1e-12 等价。
3. 将 worker 内部小 CSV 写入排队批量发布，最终仍生成同一独立 trajectory 文件与完整审计清单。
4. 对 metadata 与 state-hash 结果做进程内 memoization；不能删除 L2 persistent cache。

这些优化不影响当前结论。已验证的首次 DAG 加速足够大，继续重构只会扩大审计面。

## 产物

- `P6_ACCELERATION_DIAGNOSTIC.md`
- `audits/p6_archive_diagnostic.json`
- `audits/reference_executor_profile.json`
- `audits/cache_migration.json`
- `audits/joint_dag_equivalence.json`
- `audits/joint_dag_protocol.json`
- `audits/joint_dag_benchmark.json`
- `audits/joint_dag_first_pass_snapshot.json`
- `core/joint_dag.py`
- `scripts/run_calibration_joint_dag.py`（staged only，未接入正式队列）
