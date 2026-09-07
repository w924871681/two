# 第二篇数字孪生持续维护论文：实验执行规范（Codex Prompt）
**版本：2026-09-07**
**内部方法标识：`RAVM_DT`（仅用于代码；论文正式方法名暂不冻结）**

---

## 0. 任务目标

请在**不修改第一篇论文冻结科学结果与公开复现档案**的前提下，实现并运行第二篇论文的完整实验。

第二篇论文研究对象是：

> 已部署数字孪生（DT）模型在运行条件持续演化、维护数据可能包含不可靠/被污染观测时的持续模型维护。

核心方法逻辑已经冻结为：

```text
Current deployed DT state
        ↓
Parent-anchored blockwise candidate adaptation
        ↓
Robust aggregation of candidate state deltas
        ↓
Recent + historical paired candidate verification
        ↓
Commit candidate / retain current state
```

本论文**不依赖 MSA-DTI**。实验中的初始 deployed model 必须能由独立的通用初始化过程获得。第一篇代码、生成器、模型实现和预处理工具只能作为基础设施复用，不得把第一篇的方法输出当作第二篇的必要输入。

---

# 1. 不可违反的科学约束

1. **第一篇公开仓库/Release 只读。**
   - 参考仓库：`w924871681/paper-code-DT-Twin`
   - Release `v1.2.7` 视为冻结。
   - 不修改其 `results/`、`paper/`、`configs/`、审计记录、公开结果和 release 语义。
   - 建议创建新的兄弟目录/仓库，例如：
     ```text
     ../dt-trustworthy-maintenance/
     ```
   - 可复制或封装使用：
     - `core/data/sim.py`
     - chronological split/window utilities
     - MLP/TCN/GRU model implementations
     - Alibaba preprocessing utilities
     - bootstrap/statistics utilities
   - 所有复用代码必须在新项目中记录来源和 commit SHA。

2. **第二篇 final held-out pools 必须使用新 center IDs / 新实验池。**
   - 不复用第一篇 architecture-preselection、margin-calibration、diagnostic 或 held-out target IDs 作为第二篇正式证据。
   - 旧 Engineering-24 / DARC / rollback / selector 轨迹只能用于历史诊断，不得作为第二篇 formal held-out 结果。

3. **禁止未来信息泄漏。**
   - `D_srv[t]` 在 stage `t` 的 commit 决策前绝对不可访问。
   - final service/test 数据不得用于：
     - candidate training
     - verification
     - threshold calibration
     - hyperparameter tuning
     - baseline tuning
   - `D_srv[t]` 在标签成熟后可以作为 `D_upd[t+1]` 的底层合法数据来源，但必须先复制为 maintenance view，再按 attack scenario 注入污染；stage `t` 的历史 evaluation 记录不可用于 stage `t` 的决策。

4. **Attack 只作用于 maintenance view，不修改 clean service ground truth。**
   - 保留 immutable clean underlying timeline。
   - 每种 attack 都从 clean data copy 生成 attacked `D_upd` / `D_ver`。
   - `D_srv` 始终是 clean legitimate service evaluation。
   - 这样评估的是 maintenance poisoning/corruption 对未来 deployed DT 的影响，而不是 test-time adversarial input。

5. **所有方法使用完全相同的：**
   - center IDs
   - raw timelines
   - chronological boundaries
   - attack masks
   - random attack seeds
   - initial deployed state `M0`
   - service evaluation data
   - 主 controlled baselines 的总 gradient-update budget
   - 统计协议

6. **绝不根据 held-out 结果修改方法。**
   - development → calibration → config freeze → held-out。
   - 一旦写出 frozen config hash 后，held-out run 不得重新调参。
   - 如果结果失败，保留失败结果并报告，不进行 post-hoc 搜索。

---

# 2. 冻结的问题定义与方法接口

## 2.1 Deployed state

对 center `c`、maintenance stage `t`：

```text
M[c,t] = (a[c], theta[c,t])
```

架构 `a[c]` 在主实验维护阶段固定，只更新参数。

## 2.2 Maintenance data

同一 maintenance data 同时有两个正交分类：

```text
D_maint = D_ben ⊎ D_cor
D_maint = D_upd ⊎ D_ver
```

`D_cor` membership 对算法不可见。

`D_upd` 用于 candidate parameter update。

`D_ver` 在 candidate parameter update 中不可见，仅用于 commit verification。

`D_ver` **不假定 clean**。

## 2.3 Candidate generation

将 `D_upd[c,t]` 按时间分成 `B_u` 个不重叠 chronological blocks。

所有 block 从同一个 parent `theta[c,t-1]` 出发独立短程适配：

```text
theta_b = Adapt(theta_parent, block_b)
delta_b = theta_b - theta_parent
```

然后 coordinate-wise trimmed mean 聚合：

```text
delta_rob = TrimMean_beta(delta_1, ..., delta_Bu)
theta_candidate = theta_parent + delta_rob
```

禁止让 block 1 更新后的参数成为 block 2 的起点。

### 公平更新预算

主 controlled experiment 固定：

```text
TOTAL_GRADIENT_UPDATES_PER_STAGE = 50
```

因此：

```text
B_u * S = 50
```

候选 development grid：

```text
B_u ∈ {5, 10}
S   = 50 / B_u
beta ∈ {0.10, 0.20}
```

基础 optimizer：

```text
SGD
task loss = MSE
learning rate = 0.01
gradient norm clip = 1.0
```

除非 development pool 明确证明数值不稳定，否则不要扩展 optimizer/lr search。

## 2.4 Paired verification

Recent evidence：

```text
E_rec = D_ver[c,t]
```

Historical evidence：

```text
E_hist = bounded rolling verification buffer
```

将两种 evidence 分别切分成 chronological blocks。

对 candidate 和 current stable model 在**同一 block**上计算 paired loss difference：

```text
d_j^q = L(E_j^q; candidate) - L(E_j^q; current)
q ∈ {rec, hist}
```

对 block differences 计算：

```text
m_q = median(d_j^q)
r_q = median(|d_j^q - m_q|)
U_q = m_q + kappa_q * r_q
```

`U_q` 只是 robust conservative evidence score，**禁止称作正式 statistical confidence bound**。

## 2.5 Commit

```text
commit iff:
    U_rec <= -delta_imp
AND U_hist <=  delta_ret
```

否则 retain current deployed state。

Historical buffer：
- 只用于 verification；
- 不进入 candidate training；
- fixed capacity；
- rolling eviction；
- current `D_ver` 在 stage 决策结束后才加入历史 buffer。

---

# 3. Synthetic benchmark：正式数据池

使用第一篇 synthetic generator 的异构性基础，但创建第二篇独立配置。

## 3.1 Fresh pool IDs

固定如下 center ID 范围：

```text
source_initialization_pool : 10000–10019  (20 centers)
method_development_pool    : 11000–11019  (20 centers)
decision_calibration_pool  : 12000–12019  (20 centers)
heldout_pool               : 13000–13029  (30 centers)
```

若与任何已有本地历史池发生冲突，整体平移到更高、完全未使用的连续 ID 区间，并写入 `pool_manifest.json`；不得临时挑选“表现好”的 center。

A/B/C center type 比例继续保持 3:4:3 的平衡 schedule。

## 3.2 Seeds

建议冻结：

```text
data_seed = 7311
model_seeds = [7311, 7312, 7313]
attack_seed = 9417
bootstrap_seed = 2904
```

所有 method 共用同一 model seed / attack seed 配对。

## 3.3 Main task

主验证任务仍为 workload prediction，但这只是 evaluation task，不进入方法定义。

```text
input length L = 96
main horizon H = 1
secondary generality horizon H = 4
task loss = MSE
```

主模型 backbone：

```text
GRU, one layer, hidden size 32
```

独立性/泛化实验再评估：
```text
MLP
TCN
GRU-32
```

## 3.4 Initial deployed model M0

不使用 MSA-DTI 作为必要初始化。

统一过程：

1. 在 `source_initialization_pool` 上 source-pretrain 该 backbone。
2. 每个 target center 使用独立 warm-up segment 做相同 budget 的 target warm-up adaptation。
3. 所有 maintenance methods 从完全相同的 resulting `M0` 开始。

建议 source pretraining：

```text
Adam / MSE
50 epochs
lr = 1e-3
batch size = 64
```

target warm-up adaptation：

```text
SGD / MSE
50 updates
lr = 0.01
grad clip = 1.0
```

必须保存：
```text
initial_state_hash
source_checkpoint_hash
warmup_segment_manifest
```

---

# 4. 24-stage causal lifecycle protocol

每个 center 生成至少约 17k 个 sampled observations，使以下 raw-first chronological protocol 可行。

## 4.1 Warm-up

```text
warmup adaptation raw segment: 800 observations
initial historical-verification raw segment: 200 observations
```

每个 raw segment 在独立 segment 内生成 windows，禁止跨 segment 生成窗口。

## 4.2 Stage 1

```text
D_upd[1] : 400 observations
D_ver[1] : 240 observations
decision
D_srv[1] : 400 observations (future at decision time)
```

## 4.3 Stage t > 1

`D_upd[t]` 的 clean underlying data 使用前一 stage 已成熟的 `D_srv[t-1]`：

```text
clean(D_upd[t]) = D_srv[t-1]
```

随后：

```text
candidate generation on attacked/clean maintenance copy of D_upd[t]
D_ver[t] = next 240-observation matured verification segment
commit / retain
D_srv[t] = next 400-observation future service segment
```

共：

```text
T = 24 maintenance stages
```

务必在代码中显式验证：

```text
decision_time(t) < first_timestamp(D_srv[t])
```

Historical verification buffer 默认容量：

```text
24 verification blocks
```

Recent verification 默认：

```text
B_rec = 6 blocks
```

历史 block 个数根据 rolling buffer 中实际可用数量取值。

---

# 5. Benign operating-evolution regimes

不要依赖原 generator 的随机单次 drift 作为主 protocol。为第二篇创建显式可控的 lifecycle drift wrapper；第一篇原 `sim.py` 保持不变。

底层 seasonal / AR / burst / center heterogeneity 保留。

主 synthetic held-out centers 平衡分到四种 regime：

1. `stationary`
   - 无额外长期分布漂移。

2. `gradual`
   - 在 lifecycle 中段逐步改变 latent workload level/dynamics；
   - 变化应跨多个 stage 持续，而不是单点 perturbation。

3. `abrupt`
   - 在预先固定 stage（例如 stage 9）产生一次显著 step shift。

4. `recurring`
   - regime A → B → A → B；
   - 用于检查 historical retention 是否错误阻止 legitimate recurring adaptation。

所有 drift 参数在 development 前写入配置，不允许根据 final 结果更改。

---

# 6. Threat model 与 corruption/poisoning

## 6.1 Threat boundary

攻击者/故障过程可以：
- 修改每个 maintenance block 中不超过 `alpha` 比例的 observations；
- 作用于 `D_upd`、`D_ver` 或两者；
- 修改监测 feature、训练 target，或替换为 stale telemetry（根据 attack 类型）。

攻击者不能：
- 修改 model code；
- 修改 commit implementation；
- 读取或修改 future `D_srv[t]`；
- 修改 final evaluation records；
- 直接篡改 persisted deployed model state。

主论文安全 claim 因此限定为：

> resilience to bounded unreliable/poisoned maintenance telemetry

不声称解决任意模型仓库/代码执行层攻击。

## 6.2 Corruption ratios

```text
alpha ∈ {0.00, 0.05, 0.10, 0.20}
```

## 6.3 Attack types

数据已归一化到 `[0,1]` 时，默认 bounded attack strength：

```text
attack_strength = 0.20
random_noise_sigma = 0.15
```

所有 attack 后 clip 到合法数值范围。

### A. Random corruption

随机选择 `alpha` 比例 observations：
- active metrics 添加 zero-mean Gaussian perturbation；
- 若配置为 target corruption，同步对 target 添加 bounded random perturbation。

### B. Persistent bias injection

每个 attacked episode 固定一个 sign；
随机选取部分 active metrics；
对 selected observations 添加同方向 bounded bias。
可对 target 加同方向 bounded bias。

### C. Burst poisoning

选择一个 contiguous chronological interval，使 attacked observation 比例等于 `alpha`；
在该连续 interval 内施加一致 signed shift。
用于区别“少量孤立 outlier”与“持续一段时间的污染”。

### D. Replay / stale telemetry

将 selected observations 替换为前一 lifecycle regime / episode 中时间对齐的旧 telemetry。
保留 attack mask 和 source timestamps，以便审计。

## 6.4 Main attacked condition

主 Overall table 除 clean condition 外，使用：

```text
alpha = 0.10
attack_type = balanced mixed attack
attack_location = both update and verification
```

mixed attack 必须按 center-stage 通过 frozen seed 在四种 attack type 间平衡采样。

## 6.5 Security stress sweep

在 held-out_pool 中预先固定前 20 个 center 作为 stress subset：

```text
attack_type ∈ {random, persistent_bias, burst, replay}
alpha ∈ {0.05, 0.10, 0.20}
attack_location = both
```

额外 location sensitivity：

```text
attack_type ∈ {persistent_bias, replay}
alpha = 0.10
attack_location ∈ {update_only, verification_only, both}
```

---

# 7. Baselines

所有 controlled neural baselines 使用相同：
- `M0`
- episode data
- 50 gradient updates / stage（除 Frozen 和 method-specific frameworks）
- SGD/MSE/lr=0.01/grad clip=1.0
- no future service access

## 7.1 Primary baselines

### B0. Frozen
```text
never update
M_t = M_0
```
作用：证明维护的必要性；不能作为唯一强 baseline。

### B1. Always-FT
普通 continual fine-tuning：
```text
candidate = 50-step FT on D_upd
always commit
```
主 controlled adaptation baseline。

### B2. Experience Replay (ER)
固定大小 raw replay buffer：
```text
train on current D_upd + replay samples
always commit
```
Replay memory byte budget应与 proposed historical verification buffer 的 raw-data byte budget近似匹配，并另外报告实际 bytes。

### B3. EWC
标准 online Elastic Weight Consolidation：
```text
current loss + lambda_EWC * parameter regularization
always commit
```
`lambda_EWC` 只在 development pool 调整。

### B4. Huber-FT
用 Huber loss 替代 MSE 的简单 robust-update control：
```text
50 updates
always commit
```
作用：判断收益是否只来自“换一个抗异常 loss”。

### B5. CLeaR
实现 He & Sick 的 continual-learning-for-regression framework：
- novelty/familiarity buffers
- error-driven novelty detection
- framework-specific update trigger
- 不允许使用 future service data
- method-specific hyperparameters在 development pool 冻结

这是 regression-specific continual-learning baseline。

### B6. MER-Reg-2026
实现 2026 `Continual Learning for non-stationary regression via Memory-Efficient Replay` 的 prototype-based generative replay framework。
尽量忠实实现：
- regression target discretization
- prototype memory
- synthetic rehearsal
- regression model update
如完整 method-specific backbone 与主 GRU 不可严格共享，保留论文方法自身 backbone，并标注为 method-level baseline，而不是 controlled same-backbone comparison。

如果论文细节无法忠实复现：
- 不允许自行发明“看起来像”的版本然后仍称原方法名；
- 将其标记为 `implementation_unavailable_or_nonfaithful`；
- 主结果仍保留其余可公平实现 baselines；
- 在日志中写明原因。

### B7. ValidationCommit
最接近 proposed commit 思路的 controlled baseline：
1. ordinary 50-step FT 产生 candidate；
2. 只在 recent `D_ver` 上计算 current vs candidate 的 mean loss；
3. 使用 calibration pool 冻结单一 commit threshold；
4. 无 block-consensus；
5. 无 robust median/MAD；
6. 无 historical evidence。

用于证明 Proposed 不只是“一般 validation gate”。

## 7.2 Diagnostic upper bound

### OracleCommit
每 stage 生成与 Always-FT 相同 candidate，但使用 `D_srv[t]` 选择：
```text
commit iff candidate future service loss < current future service loss
```
仅用于 offline upper-bound / headroom analysis。
**不得列为可部署 baseline，不参与“方法公平比较”排名。**

## 7.3 不强行纳入 main baseline 的邻近方法

不要为了“最新”而做不公平复现：

- CALM-DT (ICML 2025)：LLM/in-context DT，问题和模型形式不同。
- TMC continual RL DT synchronization：优化无线同步资源，而非固定神经回归模型状态维护。
- PuriDivER (CVPR 2022)：依赖离散 noisy labels + semi-supervised classification。
- SANU (Neural Networks 2025)：围绕 continual classification label-space shift/noisy labels。
- STP task-vector defense (CoLLAs 2026)：exemplar-free classification task-vector poisoning defense。
- Trustworthy PSDT De-PI-AE (ESWA 2026)：power-system physics-informed anomalous-data evaluation，物理模型和输入假设不可直接迁移。

这些文献应进入 Related Work / novelty discussion，但除非可以忠实转为同一 regression task，不要伪装成主实验 baseline。

---

# 8. Calibration protocol

## 8.1 Candidate mechanism development

仅用 `method_development_pool`：

```text
B_u ∈ {5,10}
beta ∈ {0.10,0.20}
```

固定总 gradient update budget 50。

选择 candidate-generation configuration 时只能使用 development service outcomes。

目标：
- 兼顾 clean drift adaptation 与 attacked robustness；
- 不看 decision_calibration 或 heldout。

冻结后输出：

```text
configs/frozen_candidate_config.yaml
candidate_config_sha256.txt
```

## 8.2 Decision calibration

仅用 `decision_calibration_pool`。

Grid：

```text
kappa_rec  ∈ {0.0, 0.5, 1.0, 1.5}
kappa_hist ∈ {0.0, 0.5, 1.0, 1.5}
```

`delta_imp` / `delta_ret` 的数值网格必须依据 calibration 前已经固定的 task-loss scale 构造；不得看 held-out。
推荐先从 development loss scale 生成 5 个预注册 absolute candidates，再在 calibration pool 选组合。

主 constraint：

```text
rho = 0.05
```

harmful downside tolerance `epsilon`：
- 先在 development 阶段以 frozen reference lifecycle MSE 的固定比例定义；
- 建议 `epsilon = 0.01 * reference_lifecycle_MSE_dev`；
- 一旦写入 calibration config，不允许改。

从 eligible configurations 中选择 calibration lifecycle MSE 最低者。

若无 configuration 满足约束：
- 不得放宽约束直到“得到好结果”；
- 使用最保守 fallback（retain policy），并明确报告 calibration failure。

输出：

```text
configs/frozen_commit_config.yaml
commit_config_sha256.txt
calibration_grid.csv
calibration_summary.json
```

## 8.3 Baseline tuning

所有 baseline 超参数只可使用：
```text
method_development_pool
+
decision_calibration_pool（仅需要 threshold 的方法）
```

final held-out 不做任何重新调参。

---

# 9. Metrics

## 9.1 Accuracy / lifecycle utility

每个 center-stage 保存：

```text
service_mse
service_mae
```

汇总：

```text
Lifecycle MSE
Lifecycle MAE
Final-stage MSE
```

## 9.2 Transition safety

保存 candidate 和 current 在 clean `D_srv[t]` 上的 offline evaluation：

```text
delta_srv = candidate_service_mse - current_service_mse
harmful_commit = 1 if commit==1 and delta_srv>0 else 0
downside = commit * max(delta_srv,0)
beneficial_candidate = 1 if delta_srv<0 else 0
```

汇总：

```text
Harmful-commit rate
Average harmful downside
Conditional harmful rate among commits
Beneficial-commit recall
Commit rate
```

`Beneficial-commit recall` 用于检测 Proposed 是否通过“几乎永不更新”人为取得低 harmful rate：

```text
# beneficial candidates committed / # beneficial candidates generated
```

## 9.3 Tail risk

报告：

```text
Worst-10% center-stage service MSE
CVaR90 of center-level lifecycle MSE
```

明确在代码和表注中固定定义，不允许不同图表使用不同 CVaR 口径。

## 9.4 Drift adaptation

clean drift condition 下：

```text
post-drift excess-loss area
recovery episodes
```

Recovery 定义必须在跑 final 前冻结，例如：
- service MSE 回到 post-drift best attainable reference 的 5% 范围内；
- 连续 2 stage 满足才视为 recovery。

如果该定义在所有方法上不稳定，保留 excess-loss area 为主指标，recovery 作为 supplementary。

## 9.5 Security robustness

对每个 attack condition：

```text
attack-induced lifecycle-MSE increase vs same-center clean run
attack-induced harmful-commit increase
attack-induced downside increase
```

## 9.6 Cost

每个 stage 记录：

```text
candidate_update_time
verification_time
total_maintenance_time
peak_gpu_memory
persistent_buffer_bytes
number_of_forward_passes
number_of_backward_updates
```

测试 evaluation 时间不计入 maintenance runtime。

GPU timing：
```text
torch.cuda.synchronize() before/after timed section
```

正式 runtime 每配置至少 5 repeats。

---

# 10. Statistics

1. 主统计单位为 center，不把 24 episodes 当作 24 个独立样本。
2. 每个 center 内保留所有 episodes、attacks、seeds 的关联。
3. 95% CI 使用 center-cluster bootstrap：
   ```text
   4000 replicates
   bootstrap seed = 2904
   ```
4. 对 paired method comparison：
   - 先计算同 center、同 condition 的 paired metric difference；
   - bootstrap centers。
5. 三个 model seeds：
   - 保留 seed-level raw results；
   - 主表先对 seed 求平均，再做 center-cluster bootstrap，或使用保持 seed-center block 的 hierarchical cluster bootstrap；
   - 不把不同 seed 当独立 center。
6. 不使用 test-derived p-value 搜索。
7. 主 paired comparisons 至少报告：
   - Proposed vs Always-FT
   - Proposed vs ValidationCommit
   - Proposed vs strongest non-oracle baseline

---

# 11. Section 5 的实验问题与执行矩阵

## Q1 / Section 5.2 — Overall Lifecycle Maintenance Performance
**问题：**
> 在动态运行条件下，Proposed 能否在保持/改善生命周期预测性能的同时，降低 harmful commits 和 downside，而不是通过几乎不更新来获得“安全”？

条件：
- all 30 held-out centers
- 24 stages
- balanced drift regimes
- clean condition
- mixed attack (`alpha=0.10`, both update/ver)

方法：
- Frozen
- Always-FT
- ER
- EWC
- Huber-FT
- CLeaR
- MER-Reg-2026（若忠实实现）
- ValidationCommit
- Proposed
- OracleCommit（diagnostic only）

主指标：
- Lifecycle MSE / MAE
- Harmful-commit rate
- Downside
- Worst-10%
- CVaR90
- Beneficial-commit recall
- Commit rate

输出：
```text
results/q1_overall/raw_episode_results.csv
results/q1_overall/summary.csv
results/q1_overall/paired_bootstrap.csv
```

## Q2 / Section 5.3 — Robustness to Unreliable Monitoring Data
**问题：**
> 随着污染比例、污染类型以及污染进入 update/verification 的位置变化，Proposed 是否比持续更新、replay、regularization 和简单 verification gate 更稳健？

使用预注册 held-out stress subset（20 centers）。

Sweep：
```text
attack_type = 4 types
alpha = 0.05/0.10/0.20
location = both
```

另做：
```text
persistent_bias + replay
alpha=0.10
location=update_only/ver_only/both
```

报告：
- lifecycle MSE vs alpha
- harmful rate vs alpha
- downside vs alpha
- clean-to-attack degradation
- verification-only attack behavior

## Q3 / Section 5.4 — Adaptation under Benign Operating Evolution
**问题：**
> 在没有攻击时，robust candidate + dual-evidence gate 会不会过于保守，从而牺牲 legitimate drift adaptation？

仅 `alpha=0`。

分：
- stationary
- gradual
- abrupt
- recurring

报告：
- lifecycle curves
- post-drift excess-loss area
- recovery
- commit rate
- beneficial-commit recall
- Frozen / Always-FT / ER / ValidationCommit / Proposed / Oracle

特别观察：
- recurring drift 下 historical evidence 是否造成 stale retention；
- abrupt drift 后 gate 是否导致长时间 retain-all。

## Q4 / Section 5.5 — Component Analysis
**问题：**
> Proposed 的收益分别来自 candidate construction、robust aggregation、recent/historical evidence 还是 commit gate？

Variants：

```text
A Full
B SinglePath + DualEvidence
  - 普通 single-path 50-step FT candidate
  - 保留完整 dual-evidence gate

C MeanDelta + DualEvidence
  - same-parent block adaptation
  - arithmetic mean delta aggregation instead of TrimMean

D RobustCandidate + RecentOnly
  - 去掉 historical evidence

E RobustCandidate + MeanVerification
  - recent/history 上直接用 mean paired difference
  - 去掉 median/MAD disagreement penalty

F RobustCandidate + AlwaysCommit
  - 去掉 commit gate
```

所有 ablation：
- same held-out diagnostic slice预先固定；
- 不允许为每个 ablation 单独重新搜索有利超参数；
- 使用 Full 对应 frozen candidate/decision settings，只有被删除组件改变。

输出主指标：
- Lifecycle MSE
- Harmful rate
- Downside
- Beneficial-commit recall

## Q5 / Section 5.6 — Sensitivity, Generality, and Maintenance Cost
**问题：**
> 方法对 block 数、trim ratio、historical capacity 和 verification conservativeness 是否稳定？额外维护开销是否可接受？方法是否依赖某一种 initializer/backbone？

Sensitivity：
```text
B_u = 5 / 10
beta = 0.10 / 0.20
history capacity = 12 / 24 / 48 verification blocks
kappa around frozen value ± one grid step
```

Generalization：
```text
backbone ∈ {MLP, TCN, GRU-32}
H ∈ {1,4}
```

主 generality 可在 held-out 的预注册 10-center subset 上运行，避免计算爆炸。

报告：
- lifecycle MSE
- harmful rate
- commit rate
- update/verification/total time
- memory bytes

## Q6 / Section 5.7 — External Alibaba Trace Evaluation
**问题：**
> 在真实生产 workload trace 上，冻结方法是否仍能维持 lifecycle utility 与 harmful-transition control？

使用 Alibaba Cluster Trace v2018。

要求：
1. 创建**新的 machine split**，尽量不与第一篇 20/20/40 machine split 的已发布 machine hashes 重叠。
2. 只选择 timeline 长度满足 lifecycle protocol 的 machines。
3. 推荐：
   ```text
   source/init machines = 20
   development machines = 20
   calibration machines = 20
   heldout machines = 40
   ```
4. 若 24-stage timeline 不可行，外域固定 `T_ext=12`，不得因结果调整 stage 数。
5. raw production trace 保持原始 clean service evaluation。
6. Controlled maintenance corruption 只注入 maintenance copy。

报告两种模式：
- **direct transfer**：synthetic frozen configuration 不改；
- **domain-specific calibration diagnostic**：只用 Alibaba calibration machines 重新校准 commit parameters，再在 Alibaba heldout 上评估。

direct transfer 为主 generalization evidence；recalibration 单独标注，不混为同一结论。

---

# 12. Planned Section 5 structure

```text
5. Experimental Evaluation

5.1 Experimental Setup
    5.1.1 Benchmark and Lifecycle Protocol
    5.1.2 Drift, Corruption, and Calibration Protocol
    5.1.3 Baselines and Metrics
    5.1.4 Implementation and Statistical Protocol

5.2 Overall Lifecycle Maintenance Performance
    Q1

5.3 Robustness to Unreliable Monitoring Data
    Q2

5.4 Adaptation under Benign Operating Evolution
    Q3

5.5 Component Analysis
    Q4

5.6 Sensitivity, Generality, and Maintenance Cost
    Q5

5.7 External Trace Evaluation
    Q6
```

---

# 13. Mandatory raw-result schema

每个 center-stage-method-condition 必须至少保存：

```text
run_id
center_id
center_type
model_seed
horizon
backbone
stage
drift_regime
attack_type
attack_alpha
attack_location
method

parent_state_hash
candidate_state_hash
commit

current_service_mse
candidate_service_mse
deployed_service_mse
deployed_service_mae
delta_srv
harmful_commit
downside
beneficial_candidate

U_rec
U_hist
median_rec
mad_rec
median_hist
mad_hist

candidate_update_time_s
verification_time_s
maintenance_time_s
peak_gpu_memory_bytes
persistent_buffer_bytes

update_start_ts
update_end_ts
verification_start_ts
verification_end_ts
decision_ts
service_start_ts
service_end_ts

attack_mask_hash
update_data_hash
verification_data_hash
service_data_hash
```

不适用于某 baseline 的字段填 NA，不得删除列。

---

# 14. Mandatory audits/tests

必须自动化测试并输出 `audits/`：

1. `test_no_future_service_leakage.py`
2. `test_raw_segment_disjointness.py`
3. `test_window_no_cross_boundary.py`
4. `test_attack_fraction_bound.py`
5. `test_attack_masks_paired_across_methods.py`
6. `test_service_data_immutable.py`
7. `test_same_initial_state_across_methods.py`
8. `test_controlled_update_budget.py`
9. `test_verification_not_used_for_candidate_gradients.py`
10. `test_historical_buffer_not_used_for_training.py`
11. `test_rejected_candidate_does_not_modify_deployed_state.py`
12. `test_calibration_heldout_disjoint_centers.py`
13. `test_final_config_hash_frozen_before_heldout.py`
14. `test_bootstrap_clusters_by_center.py`

任何 audit failure：
```text
STOP
```
不得继续产出“可发表结果”。

---

# 15. Execution order

按以下顺序执行：

```text
P0 repository/bootstrap audit
P1 synthetic lifecycle generator + leakage tests
P2 baseline smoke tests on 2 development centers / 3 stages
P3 Proposed smoke tests
P4 method_development_pool
P5 freeze candidate config
P6 decision_calibration_pool
P7 freeze commit config + SHA256
P8 full held-out Q1
P9 held-out security Q2
P10 benign drift Q3
P11 ablation Q4
P12 sensitivity/generality/cost Q5
P13 Alibaba Q6
P14 4000-replicate center-cluster bootstrap
P15 plot-ready CSV + figures + manuscript-ready tables
P16 final reproducibility audit
```

不得跳过 P4–P7 直接对 held-out 调参数。

---

# 16. Required outputs

```text
dt-trustworthy-maintenance/
├─ configs/
│  ├─ frozen_candidate_config.yaml
│  ├─ frozen_commit_config.yaml
│  ├─ synthetic_protocol.yaml
│  ├─ attack_protocol.yaml
│  └─ baseline_protocol.yaml
├─ core/
├─ experiments/
├─ baselines/
├─ results/
│  ├─ q1_overall/
│  ├─ q2_security/
│  ├─ q3_benign_drift/
│  ├─ q4_ablation/
│  ├─ q5_sensitivity_cost/
│  ├─ q6_alibaba/
│  ├─ figure_data/
│  └─ tables/
├─ audits/
├─ logs/
├─ scripts/
│  ├─ run_smoke.py
│  ├─ run_development.py
│  ├─ run_calibration.py
│  ├─ run_heldout.py
│  ├─ run_all_final.py
│  └─ verify_repository.py
├─ README.md
└─ FINAL_EXPERIMENT_REPORT.md
```

`FINAL_EXPERIMENT_REPORT.md` 必须包含：
- exact git commit
- environment
- GPU
- frozen config hashes
- every baseline status
- failed/omitted baseline reasons
- all main metrics with 95% CI
- no-leakage audit result
- whether the three method contributions are empirically supported
- negative findings，不得隐藏

---

# 17. 结果判定原则

不要把“成功”编码成必须达到某个结果。

最终只回答下列科学问题：

1. Proposed 是否降低 lifecycle loss？
2. Proposed 是否降低 harmful frequency / downside？
3. 这种安全收益是否只是来自低 commit rate？
4. block-consensus 是否真的比 single-path / mean-delta 更有用？
5. dual evidence 是否比 recent-only / mean verification 更可靠？
6. verification data 自身被污染时是否仍有收益？
7. benign drift 下是否损失过多 plasticity？
8. external trace 是否能 transfer？
9. 额外 runtime/memory cost 是多少？

如果结果显示：
- retain-all；
- clean drift 明显变差；
- verification attack 下崩溃；
- block-consensus 无收益；
- external transfer 失败；

必须原样报告，不允许利用 held-out 反复改 threshold 直到“好看”。

---

# 18. 文献/方法实现参考边界

建议 Codex 在实现 baseline 前核对原论文：

- He & Sick, **CLeaR: An adaptive continual learning framework for regression tasks**, 2021.
- Bang et al., **Online Continual Learning on a Contaminated Data Stream With Blurry Task Boundaries**, CVPR 2022（相关安全背景；不直接作为 regression baseline）。
- Pham & Sun, **Certified Continual Learning for Neural Network Regression**, ISSTA 2024（相关 verification/continual regression 背景）。
- Samuel & Ahmed, **Continual Learning Strategies for 3D Engineering Regression Problems: A Benchmarking Study**, 2025.
- Amad et al., **Continuously Updating Digital Twins using Large Language Models**, ICML 2025（DT continual updating 相关，但不直接公平对比）。
- García-Santaclara et al., **Continual Learning for non-stationary regression via Memory-Efficient Replay**, 2026.
- Pawlak et al., **Addressing the Devastating Effects of Single-Task Data Poisoning in Exemplar-Free Continual Learning**, CoLLAs 2026（security-related CL）。
- Hu & Duan, **Theory of Continual Learning Against Data Poisoning Attacks**, ICML/2026 version if available（task-to-task verification / poisoning theory）。
- Shen et al., **Anomalous data evaluation for reliable updates of trustworthy power system digital twins**, ESWA 2026.

实现时：
- 不得把分类方法粗暴改造成 regression 后仍声称是“原方法复现”。
- method-level adaptation 必须在报告中清楚标注。
