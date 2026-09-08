# P6 acceleration diagnostic

生成时间：2026-09-08 21:20（Asia/Shanghai）。本报告仅分析 reference executor 和归档产物；诊断阶段没有修改 `core/` 科学代码，没有运行完整 P6，也没有访问 heldout。

## 结论

建议实现隔离的 joint-policy state-DAG executor，然后按严格等价性和 benchmark 决定是否切换。原因不是 DAG 形式本身，而是实测存在大量相同 causal prefix，且重复 candidate training 与 verification 占主要成本。

### A. 当前主要瓶颈

无缓存 reference 的一个 24-stage 代表轨迹耗时 9.382 s：candidate training 占 76.23%，recent verification 占 4.38%，historical verification 占 11.24%，post-decision service evaluation 占 1.21%，其余 Python 编排、哈希与对象复制占 6.93%。双进程正式归档的中位 trajectory 内部耗时中，candidate 占 61.26%，verification 占 37.39%，其余 maintenance 编排仅占 1.35%。因此主要成本是重复训练和重复验证 forward。

缓存完全命中时，一个代表轨迹耗时 1.758 s。模型反序列化 0.443 s（25.2% wall），48 次 evidence NPZ 打开/读取 0.700 s（39.8% wall，包含在 verification 时间中），service evaluation 0.203 s（11.5%），其余哈希、路径检查、对象复制和 Python 调度约 40.8%。写缓存的冷运行中，24 次模型序列化为 0.048 s，48 次 evidence 写入为 0.058 s，合计约 2.1% wall。单次 Python `Path.exists()` 约 53 μs。

### B. 双进程为何没有超过旧成熟单进程

旧成熟单进程实测 1,290.95 trajectories/hour；当前双进程完整归档平均约 1,064 trajectories/hour。两个 worker 按 policy range 分工，却以相同 center/seed/condition 顺序执行，因此会同时请求相同 causal prefix。归档的 19,080 个 candidate stage 请求仅有 9,622 个唯一键，理论命中率 49.57%；两个 worker 的唯一键集合有 840 个交集，占较小集合 16.31%。此前出现过一次两个进程同时 miss 并发布同一 evidence key 的实际碰撞，证明重复并发计算确实存在。

两个进程把 GPU 瞬时利用率推高到约 90%，但同一小 GPU 上的细粒度 GRU kernel、CPU 哈希/复制和小文件读取相互争用，吞吐没有同比增加。单进程 profile 的 GPU 平均利用率为 12.5%（无缓存）到 24.9%（冷缓存），峰值 36–40%；显存约 360 MB。双进程采样约 822 MB/6144 MB，容量不是瓶颈。单进程 CPU 使用约 80–99% 的一个逻辑核，只占整机逻辑 CPU 的约 4–5%。操作系统文件缓存使进程级物理 I/O 字节计数接近零，但 23,834 个小 CSV 的只读扫描耗时约 6 分钟，说明元数据和 Python 文件编排成本不可忽略。

### C. 是否存在大量相同 causal prefix

是。旧归档中，center 12002（abrupt）、clean、seed 7311 的 192 个完整 Proposed policies，共有 192×24=4,608 个 naive candidate stage 请求，仅形成 555 个唯一 parent/candidate causal computations，理论可消除 87.96%。

完整 fingerprint 在本工作负载中包含 deployed model hash、按顺序排列的 historical verification block hashes、stage、center、condition、seed、horizon、update/verification/attack identity 和确定性 candidate RNG identity。Proposed 的历史 buffer 只追加同一 workload 的 verification blocks，与 commit 决策无关；同 stage 内这些字段对全部 policy 相同。因此实测完整 causal state 数等于唯一 parent state 数。静态 gate 参数仍逐 policy 保存并参与向量化决策，不能从 policy 身份中丢失。

### D. 每 stage 的 unique causal state

下表给出 192-policy 实测值，以及按 400/192 线性放大的保守近似。前两 stage 的 400-policy 值有严格上界 1、2；后续近似只用于决定是否值得实现，最终值必须由 DAG 全 400-policy trace 给出。

| Stage | Naive policies | Unique causal states observed /192 | Conservative estimate /400 |
|---:|---:|---:|---:|
| 1 | 400 | 1 | 1 |
| 2 | 400 | 2 | 2 |
| 3 | 400 | 2 | 5 |
| 4 | 400 | 3 | 7 |
| 5 | 400 | 3 | 7 |
| 6 | 400 | 6 | 13 |
| 7 | 400 | 6 | 13 |
| 8 | 400 | 6 | 13 |
| 9 | 400 | 6 | 13 |
| 10 | 400 | 6 | 13 |
| 11 | 400 | 6 | 13 |
| 12 | 400 | 12 | 25 |
| 13 | 400 | 17 | 36 |
| 14 | 400 | 24 | 50 |
| 15 | 400 | 30 | 63 |
| 16 | 400 | 40 | 84 |
| 17 | 400 | 40 | 84 |
| 18 | 400 | 44 | 92 |
| 19 | 400 | 47 | 98 |
| 20 | 400 | 48 | 100 |
| 21 | 400 | 51 | 107 |
| 22 | 400 | 51 | 107 |
| 23 | 400 | 52 | 109 |
| 24 | 400 | 52 | 109 |

估计 400-policy 全生命周期约 1,164 个唯一 candidate states，而 naive 是 9,600 次，理论上限约减少 87.9%。实际全 400 trace 可能高于或低于线性估计。

### E. DAG 理论上最多减少多少 candidate computations

在代表性 192-policy trace 上是 87.96%；线性外推到 400 policies 约 87.88%。Verification primitive 与 candidate state 一一对应，具有近似相同的减少空间。Service evaluation 可按每个 parent/candidate state 复用，但仍必须为每个 policy 写出独立科学结果行。

### F. RAM hot cache 是否值得做

值得，但它是第二优先级。完全命中磁盘缓存时，模型反序列化和 evidence NPZ 读取合计占 wall 的约 65%；process-local LRU 可直接避免这些小文件打开与解析。L2 persistent cache必须保留，用于 resume 和审计。L1 必须以完整版本化 key 查询，不能放宽等价条件。

### G. 当前 1 worker 还是 2 workers 更合理

对现有 policy-range reference executor，1 worker 更合理：旧成熟实测 1,291/h，高于双进程归档的 1,064/h。对 joint-DAG 不能预判，必须用同一 workload 实测 1 worker 与 2 workers；新的分区单位应是完整的 center×condition×seed workload，避免两个 worker 同时请求同一 policy DAG。

### H. 是否建议实施 joint-policy DAG

建议实施并验证。触发条件同时成立：多数 policies 共享 causal prefix，candidate/verification 重复计算占绝大多数 wall time。实现必须隔离，不能覆盖 reference executor；只有科学字段等价、泄漏审计通过且实测至少达到切换阈值，才可建议替换正式 P6。

机器可读数据见 `audits/p6_archive_diagnostic.json` 和 `audits/reference_executor_profile.json`。
