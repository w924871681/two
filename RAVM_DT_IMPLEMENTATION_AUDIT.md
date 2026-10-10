# RAVM-DT Final Implementation Audit

审计对象：`C:\Users\92487\Downloads\RAVM_DT_CMC_13Pages_Revised_Final.zip` 及其中的 `main.pdf`。ZIP 内 `main.pdf` 与 `C:\Users\92487\Downloads\main.pdf` 字节一致。ZIP SHA-256 为 `bda9f217f4ea78d3912d8d295d6bf6efcb330a25935eb2146565ff5461bdc316`，PDF SHA-256 为 `914e88a8db0c11c74936b118de4bea765c68895fc317028bb7b4c23e80473fdb`。本报告只恢复已执行事实；没有运行新实验，也没有把旧 V1 或 development-only 机制解释为 Final V2。

状态词含义：**VERIFIED** 表示有直接运行或冻结 artifact；**STRONGLY INFERRED** 表示多个执行实现和结果相互印证但缺少单一直接 manifest 字段；**NOT FOUND** 表示项目证据不足；**INCONSISTENT** 表示证据互相冲突。

## 1. Executive Verdict

- Canonical final implementation：**VERIFIED**。Final V2 科学实现提交为 `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`；`core/v2_engine.py` 的冻结 SHA-256 为 `f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024`。当前 HEAD 为 `1b84fbcff8c47fb76dafc313f536f04ba8a9287b`，但当前四个核心文件相对 `7ae7fab` 无内容差异，后续提交主要是冻结、执行、分析与制图。
- Canonical final results：**VERIFIED**。主确认实验位于 `results_v2_final/`，baseline 位于 `results_v2_final_baselines/`，严重度、通用性和 Alibaba 分别位于 `results_v2_severity/`、`results_v2_generality/`、`results_v2_alibaba/`。这些目录被最终制图脚本直接读取，论文图 PDF 与 `paper_figures/pdf/` 对应文件哈希一致。
- 最终方法：**VERIFIED** 为 `Final_V2_SP_ShortDual`：SinglePath candidate、50 次 MSE-SGD 更新、12-block history、GRU、`L=96`、`H=1`、`kappa_rec=0`、`kappa_hist=0.5`、`delta_imp=2.8018237766243602e-05`、`delta_ret=0`。
- 当前论文忠实度：核心方法、门控不等式、冻结参数、主表数字、总体结论和 Alibaba 边界均与 artifacts 一致；未发现 BLOCKER 级事实冲突。论文仍缺少若干影响复现的执行细节，尤其是 history 初始化、block 构造、随机 minibatch、初始模型、污染取整、calibration grid/tie-break、ValidationCommit fallback、计时边界和 Alibaba 预处理。

最终四项判定：

- **A. Historical-buffer initialization: VERIFIED**
- **B. Verification-block construction: VERIFIED**
- **C. Final experimental protocol: VERIFIED**
- **D. Current manuscript fidelity to implementation: PASS WITH REQUIRED CLARIFICATIONS**

## 2. Canonical Experiment Identification

| Item | Identified artifact/path | Evidence | Confidence |
|---|---|---|---|
| Canonical paper package | `C:\Users\92487\Downloads\RAVM_DT_CMC_13Pages_Revised_Final.zip` | ZIP 内 PDF 与单独 `main.pdf` 完全一致；ZIP 中所有结果图与本地最终图逐文件同哈希 | VERIFIED |
| Scientific implementation | commit `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3` | frozen method/provenance 直接记录；当前 core 与该提交无差异 | VERIFIED |
| Final method config | `configs_v2_final/frozen_v2_final_method.yaml` | `FINAL_METHOD_FROZEN`，method、steps、history、backbone、horizon 和 core hash 齐全 | VERIFIED |
| Final decision config | `configs_v2_final/frozen_v2_final_commit_config.yaml` | `FINAL_CONFIG_FROZEN`；文件 SHA-256 `7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13` | VERIFIED |
| Main confirmatory manifest | `configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json` | 30 centers、3 seeds、4 streams、2 methods、720 trajectories；SHA-256 `b4428cf870a5bf52aafb5b9b8d74176ea95fb2654f995397f2aa13f8b56430fe` | VERIFIED |
| Main final results | `results_v2_final/` | integrity：720/720 valid、17,280 stage rows、0 missing/duplicate/unexpected/partial | VERIFIED |
| Final baseline results | `results_v2_final_baselines/` | 六个 baselines 共 2,160 trajectories；与复用的 Proposed 合并为七方法比较 | VERIFIED |
| Severity results | `results_v2_severity/` | frozen α sweep 输出及 paired summaries | VERIFIED |
| Architecture/horizon results | `results_v2_generality/` | 2,160 trajectories 的汇总、paired comparisons 与执行状态 | VERIFIED |
| Alibaba external results | `results_v2_alibaba/` | 1,200 trajectories；protocol/integrity/pairing/leakage audits 均 PASS | VERIFIED |
| Paper result mapping | `paper_figures/scripts/build_paper_data.py`, `paper_figures/scripts/finalize_paper_package.py` | 直接读取上述 Final V2 目录；生成图与论文包中的图完全一致 | VERIFIED |
| Excluded evidence | V1、V2 development、失败/恢复 scratch 与旧归档 | 它们用于 provenance、选择或诊断，不是生成当前论文 final 数字的 canonical 目录 | VERIFIED |

Canonical implementation: `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`, especially `core/v2_engine.py`.

Canonical config: `configs_v2_final/frozen_v2_final_method.yaml` + `configs_v2_final/frozen_v2_final_commit_config.yaml`.

Canonical result directories: `results_v2_final/`, `results_v2_final_baselines/`, `results_v2_severity/`, `results_v2_generality/`, `results_v2_alibaba/`.

Canonical run/artifact identifiers: `Final_V2_SP_ShortDual`, final manifest SHA-256 `b4428cf...`, commit-config SHA-256 `7275a287...`, core SHA-256 `f27d0abb...`.

Confidence: **VERIFIED**.

## 3. Confirmed RAVM-DT Execution Flow

下列顺序来自实际 executor。注意，history append 在 service evaluation **之前**，但一定在 decision seal **之后**；未来 service capability 只有在 `record_decision` 后才能打开。

```text
parent = target-specific initial deployed model M_c,0
history = six chronological blocks from raw target interval [800, 1000)

for stage t = 1,...,24:
    raw_update, raw_verification = timeline.maintenance(t)
    corrupt only authorized update/verification roles
    D_upd = windows(raw_update, L=96, H)

    candidate = deepcopy(parent)
    create a fresh SGD optimizer
    adapt candidate for 50 stochastic minibatch steps on D_upd only

    recent_blocks = six chronological blocks of D_ver
    U_rec = score(candidate, parent, recent_blocks, kappa_rec)
    U_hist = score(candidate, parent, pre-stage history, kappa_hist)

    commit = (U_rec <= -delta_imp) and (U_hist <= delta_ret)
    timeline.record_decision(t, commit)       # immutable decision token

    history = FIFO_tail_12(history + recent_blocks)
    finish maintenance timer

    D_srv = timeline.service(t)               # access now permitted
    evaluate parent and candidate on D_srv
    deployed = candidate if commit else parent
    evaluate/log deployed service MSE and MAE
    parent = deployed
```

**VERIFIED**：candidate proposal 与 deployed state 分离；candidate 由 deep copy 产生，拒绝时不覆盖 parent。**VERIFIED**：`D_srv` 在 decision 后才由 `Timeline.service()` 返回；服务标签不参与 adaptation、verification 或 commitment。**VERIFIED**：代码在服务评估后才把局部变量 `parent` 指向 deployed model，但 commit 与选模逻辑已在服务开放前冻结，因此没有 service leakage。

## 4. Historical Buffer Initialization

1. `H_{c,0}` **不是空集（VERIFIED）**。它由目标 center 的 raw interval `[800,1000)` 构造成 verification blocks。
2. `L=96,H=1` 时该区间生成 `200-96-1+1=104` 个 windows，并按时间顺序 `array_split` 成 6 个 blocks，window 数为 `18,18,17,17,17,17`。
3. 每个 window block 保存为可再次构窗的 raw `Segment`；对应 raw 长度为 `114,114,113,113,113,113`。相邻 block 的 raw input context 重叠 96 个点，但目标时间不重叠。
4. stage 1 decision 前 history 已含上述 6 blocks，因此 final run 不触发 empty-history 分支。底层 scorer 对空 evidence 返回无穷大，但它不是最终执行路径。
5. stage 1 的 current verification 不会参与 stage 1 的 historical statistic。顺序为：用 pre-stage history 计算 `U_hist` → seal decision → append stage-1 recent blocks。
6. stage 1 append 后容量为 12（initial 6 + recent 6）；stage 2 decision 前使用这 12 blocks。stage 2 append 后保留最后 12 blocks，即 stage 1 + stage 2；此后为 block-level FIFO，近似保留最近两个 stage 的 verification evidence。
7. history 保存 verification evidence，不保存 service data。

**Paper-safe factual statement:** `H_{c,0}` is initialized before the first maintenance decision with six chronological verification blocks constructed from the target-specific pre-maintenance interval `[800,1000)`. At stage `t`, the historical statistic uses only the buffer available before stage `t`; the current verification blocks are appended after the commit/retain decision, and the buffer retains the most recent 12 blocks by FIFO truncation.

## 5. Verification Block Construction

令一个 raw segment 长度为 `N`，输入长度 `L=96`，预测步长为 `H`。窗口起点数为

```text
n = N - L - H + 1.
```

`block_indices(n,B=6,H)` 先取得允许的窗口起点，再按起点顺序执行 `numpy.array_split(...,6)`。因此 blocks 按时间顺序、不共享目标索引；为了每个 block 能独立重构完整输入窗口，相邻 block 的 raw segment 可共享长度为 `L` 的上下文。`array_split` 使 block window 数最多相差 1，最后块不会丢弃。

对每个 block `j`，实际差值为原始 MSE 差，而非相对或归一化差：

```text
e_cand(i)   = mean_h (candidate(x_i) - y_i)^2
e_parent(i) = mean_h (parent(x_i)    - y_i)^2
d_j         = mean_{i in block j} [e_cand(i) - e_parent(i)]
m           = median_j(d_j)
MAD         = median_j(|d_j - m|)
U           = m + kappa * MAD
```

没有 `1.4826` 等 MAD scaling constant。负 `d_j` 表示 candidate 更好。recent 与 historical evidence 使用同一个 block loss 和 `median + kappa·MAD` 实现，只是 block 来源和 kappa 不同。

Final `H=1` 每个 stage 的 240-point verification 段生成 144 windows，严格为 6 blocks × 24 windows。`history_capacity=12` 明确指 **12 个 block objects**，不是 12 stages 或 12 datasets。Final H=1 下 recent evidence 为当前 stage 的 6 blocks；historical evidence最多为 12 blocks。

通用性实验 `H=4` 没有改变 raw 段边界；verification 为 141 windows，仍分为 6 个时间块。**VERIFIED**：block 数、顺序、差值方向、median/MAD 与 FIFO 均由实际代码和 final trajectory fields 交叉支持。

## 6. Candidate Adaptation

| Property | Final executed value | Status |
|---|---|---|
| Starting state | `copy.deepcopy(current deployed parent)` at every stage | VERIFIED |
| Candidate path | SinglePath; no block candidate ensemble or trimmed parameter aggregation | VERIFIED |
| Optimizer | fresh `torch.optim.SGD` each stage | VERIFIED |
| Learning rate | `0.01` | VERIFIED |
| Steps | 50 optimizer steps | VERIFIED |
| Batch size | `min(64,n)` | VERIFIED |
| Sampling | `numpy.default_rng(seed).integers(...)`; with replacement at every step | VERIFIED |
| Full batch / epoch shuffle | neither; stochastic replacement minibatches | VERIFIED |
| Loss | MSE | VERIFIED |
| Gradient clipping | global norm `1.0` | VERIFIED |
| Weight decay | PyTorch SGD default `0` | VERIFIED |
| Optimizer state across stages | not retained; optimizer recreated | VERIFIED |
| Training data | `D_upd` only for Proposed | VERIFIED |
| `D_ver` in gradients | never | VERIFIED |
| `D_srv` in adaptation | impossible before decision token | VERIFIED |
| Adaptation RNG | `model_seed + center_id + 100*stage` | VERIFIED |

候选训练前后均检查 parent state hash；candidate 被接受前不会覆盖 parent。论文所说“使用 complete update subset”在数据角色上正确，即全部 update windows 构成可采样池；但实际 50 次更新并非 full-batch 地遍历完整 subset，这一 minibatch 细节目前在论文中欠明确。

## 7. Stage Data Protocol

Raw timeline 先按角色切段，再在每段内部构造 sliding windows，窗口绝不跨 `D_upd/D_ver/D_srv` 边界。

```text
Source pretraining (different source centers): raw [0,1000)

Target center:
[ warm-up for M_c,0: 0..799 ][ initial history: 800..999 ]

Stage 1:
[ D_upd: 1000..1399, 400 ][ D_ver: 1400..1639, 240 ][ D_srv: 1640..2039, 400 ]

Stage 2:
[ D_upd: 1640..2039, 400 ][ D_ver: 2040..2279, 240 ][ D_srv: 2280..2679, 400 ]

General stage t:
v_t = 1400 + 640(t-1)
[ D_upd: v_t-400 .. v_t-1 ][ D_ver: v_t .. v_t+239 ][ D_srv: v_t+240 .. v_t+639 ]
```

Final `L=96,H=1` 的窗口数：update 304、verification 144、service 304。`H=4` 通用性实验对应 301、141、301。三段在同一 stage 内 raw points 不重叠。前一 stage 的 service raw interval 会在下一 stage 成熟为 update raw interval；这体现在线维护的延迟反馈，而不是当前 decision 使用未来 service。

`Timeline.maintenance(t>1)` 要求上一 stage decision 已存在；`Timeline.service(t)` 要求当前 decision 已记录。当前 history 只由 initial-history/current verification 构成。没有独立的 stage-time “check” 集；development/calibration pools 是 center-level protocol split。

## 8. Initial Deployed Model

初始模型是两步形成的（VERIFIED）：

1. **Source pretraining**：synthetic 使用 source centers `10000–10019`，Alibaba 使用 `20000–20019`。每个 model seed 独立训练 checkpoint。取每个 source center raw `[0,1000)` 并拼接 windows；使用 Adam、LR `0.001`、50 epochs、MSE、batch 64，每 epoch permutation。没有 validation-based checkpoint selection。
2. **Target initialization**：对每个 target center/seed，从对应 source checkpoint 加载，然后在该 target 的 warm-up raw `[0,800)` 上执行与 stage candidate 相同的 50-step SGD adaptation（LR `0.01`、batch 64 with replacement、MSE、clip 1），形成 `M_{c,0}`。

目标 warm-up `[0,800)`、initial history `[800,1000)` 和 stage-1 update `[1000,1400)` raw 区间互斥。相同 center/seed 的初始 checkpoint由不同 lifecycle condition/method 复用；final pairing audit 对初始 state、data、attack 和 service hashes 执行一致性检查。架构默认为单层 GRU（input 24、hidden 32、linear head），H=1。

## 9. Lifecycle Condition Generation

Synthetic final pool由 `vendor.sim.simulate_centers` 生成异质 A/B/C center 后，final runner 关闭 simulator 内生 drift，并施加确定性显式 shift。shift 同时作用于 target `y` 和特征值：对概率型值采用 logit-space additive shift 后 sigmoid 回 `[0,1]`，各特征有固定 gain/delay；12 个值与 12 个 availability masks 拼为 24 维输入。

- **Stationary（VERIFIED）**：`q(t)=0`。
- **Gradual（VERIFIED）**：`q(t)=0.8·clip((t_raw-6520)/5120,0,1)`。
- **Abrupt（VERIFIED）**：`q(t)=0` for `t_raw<6520`，否则 `q(t)=0.8`。
- **Recurring（VERIFIED）**：`q(t)=0.8` on raw intervals `[5240,9080)` and `[12920,∞)`，其他时间为 0。
- **Mixed（VERIFIED）**：不是第五种独立 drift generator。每个 center 仍保留其由 `(center_id-14000) mod 4` 指定的 stationary/gradual/abrupt/recurring base regime，再叠加 `alpha=0.10`、location=`both` 的 mixed telemetry corruption。最终主表将其作为第五个 primary condition 汇总。

raw index `6520` 是 stage 9 verification 的起点；因此 stage 9 update 仍在 shift 前，stage 9 verification/service 已处于 shift 后。30 个 final centers 分配为 stationary 8、gradual 8、abrupt 7、recurring 7。

## 10. Corruption Mechanisms

污染只作用于 maintenance telemetry 中授权的 update 和/或 verification 段；service 始终 clean。对每个 raw role segment，代码先切为 10 个时间 strata，在每个 stratum 选择 `floor(stratum_length*alpha)` 个位置。因此 `alpha` 是 **nominal per-stratum corrupted fraction/cap**，不是噪声幅度。update 长 400 时 α=0.05/0.10/0.20 的实际比例正好为 5%/10%/20%；verification 长 240 时因每 strata 长 24，实际比例为 4.1667%/8.3333%/16.6667%。

- **Random**：在选中行的 12 个值特征加入截断/裁剪的高斯扰动（尺度 0.15、单次变化边界 0.2），label 独立扰动并裁剪到 `[0,1]`。
- **Persistent bias**：每 center/stage 固定选择 6/12 个值维度和一个正负号；在被选中的、分散的 raw positions 上对这些值及 label 加 `sign·0.2` 并裁剪到 `[0,1]`。这里的 persistent 是 stage 内共同方向/变量，并非跨全部 24 stages 连续保持同一 bias。
- **Burst**：数值变换与 persistent bias 相同，但在每个时间 stratum 内形成一个短连续 run；这是块内突发。
- **Replay**：选中位置被固定的过去 warm-up tail 中相应偏移的 `(x,y)` 替换，而非与当前数据混合。update 长 400 使用 `[400,800)`，verification 长 240 使用 `[560,800)`；所有 source timestamps 早于当前 segment。
- **Mixed**：每个四-stage cycle 内包含 random、persistent_bias、burst、replay 各一次；排列由 `SeedSequence([9417,center_id,cycle])` 决定。位置 RNG 由 `SeedSequence([9417,center_id,stage,role])` 决定。

污染种子独立于 model seed，因此同一 center/scenario/stage 的 attack realization 可跨方法和 model seeds 对齐；final pairing audits 报告 0 个 hash mismatch。服务数据不污染，用于计算已提交决策的 future consequence。

## 11. Exact RAVM-DT Decision Rule

对 recent 或 history 中的每个 block `j`：

```text
d_j = mean_i [ MSE(candidate(x_i), y_i) - MSE(parent(x_i), y_i) ]

median_rec = median({d_j : j in current-stage verification blocks})
MAD_rec    = median_j |d_j - median_rec|
U_rec      = median_rec + kappa_rec * MAD_rec

median_hist = median({d_j : j in pre-stage historical blocks})
MAD_hist    = median_j |d_j - median_hist|
U_hist      = median_hist + kappa_hist * MAD_hist
```

Final frozen values：

```text
kappa_rec  = 0
kappa_hist = 0.5
delta_imp  = 2.8018237766243602e-05
delta_ret  = 0

commit = True iff
    (U_rec <= -delta_imp) AND (U_hist <= delta_ret)
```

否则 retain parent。等号满足 commit。`d<0` 表示 candidate 优于 parent。`rho=0.05` 与 `epsilon=5.6036475532487204e-05` 是 calibration safety constraints，不在逐 stage commit 公式中直接出现。

## 12. Calibration Protocol

| Pool | Centers | Role | Final-evaluation access during selection |
|---|---:|---|---|
| Source | 10000–10019 | source checkpoints | n/a |
| Development | 11000–11019 | structural screening | no final pool |
| Calibration | 12000–12019 | frozen decision calibration | no final pool |
| Final confirmatory | 14000–14029 | final evaluation | sealed until method/config freeze |

四个 synthetic center ranges 完全不相交（VERIFIED）。Development 先在预注册 4,800-trajectory grid 中选择 `V2_SP_ShortDual` 与 history capacity 12；该阶段可能出现的 adaptive recovery/realignment 结构没有进入 final method。

最终 V2.1 decision calibration 在运行前固定：

```text
kappa_rec  in {0, 0.5, 1.0, 1.5}
kappa_hist in {0, 0.5, 1.0, 1.5}
```

共 16 组；`delta_imp`、`delta_ret`、history capacity、candidate path、optimizer 和 steps 均不再搜索。clean/mixed 的既有 calibration results 被复用；security-aware completion 新运行 verification-only persistent_bias/replay，得到 1,920 个 V2 trajectories，另有 120 个 V0 reference trajectories，完整性与 hash pairing 均 PASS。

Feasible 条件为 mixed、persistent-only、replay-only 均满足 absolute harmful rate `<=rho=0.05` 与 downside `<=epsilon=5.6036475532487204e-05`，且两个 verification-only scenario 相对 V0 的 harmful/downside paired CI 不得是完全 adverse 的正区间。14/16 组 feasible。

主目标是在 feasible configurations 中最小化 stationary、gradual、abrupt、recurring、mixed 五个 condition **等权**的 lifecycle MSE。Tie-break 顺序：较低 mixed downside → 较高 balanced beneficial recall → 较低 verification-only downside → manifest order。选中 `kappa_rec=0,kappa_hist=0.5`。final config 在 heldout materialization 前写入并哈希冻结；freeze、seal、leakage audits 全部 PASS。未找到 final-pool 结果反向调参证据（VERIFIED by sealed provenance/audits）。

## 13. ValidationCommit Baseline

```text
candidate generation:
    same SinglePath operator as Final V2
    deepcopy(parent), 50-step SGD, lr=0.01, MSE, batch 64 replacement sampling

decision statistic:
    mean over the whole D_ver of
    candidate per-window MSE - parent per-window MSE

nominal commit rule:
    commit iff mean_difference <= -validation_threshold

calibration:
    threshold grid = {0,
                      5.6036475532487204e-06,
                      2.8018237766243602e-05,
                      5.6036475532487204e-05,
                      2.8018237766243602e-04}
    calibration outcome = calibration_failure_retain_all

final executed behavior:
    validation_retain_all = true
    commit is always false; nominal threshold is operationally irrelevant
```

Final commit count 为 0（VERIFIED）。因此 deployed trajectory 和 lifecycle metrics 与 Frozen 相同；但 ValidationCommit 仍在每个 stage 训练 candidate 并做 verification，所以 runtime 和 Frozen 不同。零 commit 是冻结 calibration fallback 的显式执行结果，不是 final runner 偶然失败或漏调用。

## 14. Other Baselines and Fairness

| Method | Adaptation data | Steps | LR | Loss | Memory / regularization | Commit behavior |
|---|---|---:|---:|---|---|---|
| Proposed | current `D_upd` | 50 | 0.01 | MSE | 12 verification blocks; dual evidence | gate decides |
| Always-FT | current `D_upd` | 50 | 0.01 | MSE | none | always candidate |
| ER | current `D_upd` + raw replay buffer | 50 | 0.01 | MSE | FIFO raw replay, byte budget matched approximately to Proposed history; observed max 302,400 B | always candidate |
| EWC | current `D_upd` | 50 | 0.01 | MSE + EWC | λ=10; Fisher EMA γ=0.9; 32 examples initially/each stage; anchor updated to candidate | always candidate |
| Huber-FT | current `D_upd` | 50 | 0.01 | Huber, δ=0.1 | none | always candidate |
| ValidationCommit | current `D_upd` | 50 | 0.01 | MSE | whole-verification mean criterion; final retain-all fallback | never commits in final |
| Frozen | none | 0 | n/a | n/a | none | always retains M0 |

Final benchmark manifest 为 `6 baselines × 30 centers × 3 seeds × 4 streams = 2,160` trajectories；复用 Proposed 的 360 trajectories 后，七方法共 2,520 trajectories。四 streams 为 clean、mixed α=.10 both、persistent α=.10 verification-only、replay α=.10 verification-only；clean 再按 center regime 形成四个 clean lifecycle conditions，所以论文展示七类条件和其中五个 primary conditions。

公平性判断：所有 active adaptation 方法的名义 optimizer-update budget 均为 50 steps、LR .01、batch 64。总计算量和可见训练数据并不完全相同：EWC 每 stage 另有 Fisher backward passes；ER 的训练池含 replay；Proposed 有 verification forward passes。论文可声称 matched update-step budget，不能声称所有方法具有完全相同的总 FLOPs、数据量或 wall time。

## 15. Metrics

对 stage `t` 的 future clean service windows，先在未提交的两个反事实 state 上计算：

```text
L_current(t)   = mean service-window MSE of parent
L_candidate(t) = mean service-window MSE of candidate
Delta_srv(t)   = L_candidate(t) - L_current(t)

harmful(t) = 1{commit(t)=1 and Delta_srv(t)>0}
downside(t) = 1{commit(t)=1} * max(0, Delta_srv(t))
```

`Delta_srv=0` 不 harmful。没有 commit 时 downside 为 0。

- lifecycle MSE/MAE：一个 trajectory 内 24 stages 的 deployed service-window mean error 再取均值。
- harmful-transition frequency：`sum_t harmful(t)/24`，分母是全部 candidate stages，不是 commits。
- average downside：`sum_t downside(t)/24`。
- conditional harmful among commits：`sum harmful/sum commit`；零 commits 时为 NA。
- beneficial candidate：`Delta_srv<0`；beneficial-commit recall 为 `sum(commit·beneficial)/sum(beneficial)`，无 beneficial 时为 NA。
- commit rate：`sum commit/24`。

统计流程（VERIFIED）：先形成 seed-level trajectory metric，再对同一 center 的 seeds 求均值；center 是 bootstrap/resampling unit。paired comparison 在相同 center、model seed、scenario 上合并后求差，再在 center 内平均 seeds，最后以 center 为单位有放回抽样 4,000 次，seed=2904，报告 percentile 95% CI。stages 未被当作独立 bootstrap observations。

主表五条件数值可与论文逐项匹配：Proposed lifecycle MSE `0.0031503305`、harmful `0.02387897`、downside `2.3216338e-06`、commit `0.24521495`；相对 active baselines 的 MSE cost 为 6.8%–13.2%，harmful 减少 85.5%–91.4%，downside 减少 85.3%–94.9%；相对 Frozen 的 MSE 改善 34.945%。

## 16. Runtime Measurement

每个 stage 的 `maintenance_time_s`：CUDA synchronize/reset peak → 开始计时 → update tensor construction → candidate adaptation → recent/history verification → decision seal → history/replay/Fisher bookkeeping → CUDA synchronize → 停止计时。之后才打开 service、计算反事实/部署后 service metrics 并发布 CSV。

因此 runtime **包含** candidate adaptation、verification、history update 和方法特定的 maintenance bookkeeping；**不包含** service evaluation、CSV publishing、checkpoint/model initialization、进程启动。GPU 路径有 synchronization。没有找到统一 warm-up pass 的明确证据（NOT FOUND）。最终数值是 stage time 经 trajectory/seed/center/scenario 汇总的均值。

七方法 all-seven-condition mean stage times（秒）：Proposed `0.184537`、Always-FT `0.249596`、ER `0.262024`、EWC `0.504161`、Huber-FT `0.250123`、ValidationCommit `0.251534`、Frozen `0.004404`。这些数字在 artifact 中 **VERIFIED**。Proposed 在 synthetic run 中快于 Always-FT，而 Alibaba 中 Proposed `0.1832`、Always-FT `0.1342`；两者来自独立正式 runs。代码没有“candidate 被拒绝后跳过后续 candidate/verification 计算”的捷径。synthetic 速度反转的确定机制原因在现有 evidence 中 **NOT FOUND**，故不能把该顺序解释为算法固有加速。

`peak_gpu_memory_bytes` 是每 stage reset 后由 PyTorch 报告的 peak allocated memory，不是整机 GPU 总占用。`persistent_buffer_bytes` 是持久 raw/evidence numpy buffers 的字节数。

## 17. Architecture and Horizon Experiments

- GRU：单层，input 24、hidden 32、linear head。
- MLP：flatten `96×24=2304` → 64 → ReLU → H。
- TCN：causal Conv1d `24→32,k=3`，ReLU；Conv1d `32→32,k=3,dilation=2`，裁去右 padding；linear `32→H`。

执行矩阵为 `3 architectures × 2 horizons × 2 conditions(clean,mixed) × 3 methods(Proposed,Always-FT,Frozen) × 20 centers × 3 seeds = 2,160 trajectories`；其中 360 个 GRU-H1 trajectories 从已审计 final artifacts 复用，1,800 个为该 phase 新执行。完整性审计 PASS。

H=1 与 H=4 均复用最终 `kappa_rec=0,kappa_hist=.5,delta_imp,delta_ret,history capacity=12`，没有针对 backbone 或 horizon 重新 calibration。raw segment 边界不变，因此 H=4 的 update/verification/service windows 减为 301/141/301。结果支持已测试六种 architecture-horizon settings 上的定性排序；不能扩大为 architecture-invariant 或对任意 horizon 成立。

## 18. Alibaba External Trace Protocol

- 原始 archive：`D:\RCF_DTI_pre_submission\data\alibaba2018\raw\machine_usage.tar.gz`，冻结 SHA-256 `3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a`。
- 数据读取：定位 `machine_usage.csv`；按 machine 分组，过滤 target CPU 不在 `[0,100]` 或 timestamp 缺失的行，按 timestamp 排序并去重，保留前 17,000 个有效 observation；不插值，保留 irregular timestamps。
- 输入：CSV positional columns 2–8 的 7 个 telemetry metrics；已知百分比 `/100`，无声明尺度的 `mkpi` 标为 unavailable；7 个值补到 12 value channels，再拼 12 masks，形成 24 维。target 为 CPU utilization（column 2）。旧 repository 中列名可佐证 positional mapping，但当前 final archive 本身没有数据字典。
- Split：100 台 outcome-independent hashed machines；source `20000–20019`、development `20020–20039`、calibration `20040–20059`、heldout/external evaluation `20060–20099`。Final V2 复用了既有 40-machine heldout split，因此是 external-domain transfer check，不是 fresh external confirmation。
- Lifecycle：同一 raw-first causal protocol，`L=96,H=1`、24 stages、update/ver/service raw sizes 400/240/400；clean 与 mixed α=.10 both；service clean。
- Methods：Proposed、Always-FT、ER、Huber-FT、Frozen。矩阵 `40×3×2×5=1,200` trajectories、28,800 stage rows，integrity/pairing/leakage 均 PASS。
- Final V2 gate、history 和 adaptation 参数不变；没有 Alibaba-specific recalibration。
- mixed Proposed harmful frequency `0.0649305556 = 187/(40×3×24)`，分母为所有 2,880 stage transitions，不是 commits；commit rate `0.15520833`。
- 汇总以 machine 为 cluster；seeds 在 machine 内平均，4,000 次 paired machine-cluster bootstrap，seed 2904。

机器 timestamp 的物理单位/标称 sampling interval在 final 项目与 archive metadata 中 **NOT FOUND**。可验证的是 irregular timestamps 被原样保留。因此论文的 external-domain boundary 与实现一致，但若声明固定采样间隔将无法由当前 evidence 支持。

## 19. Random Seeds and Effective Sample Counts

| Randomness source | Executed rule | Status |
|---|---|---|
| Data generator | `data_seed=7311`; center-specific generator offset/center logic | VERIFIED |
| Model seeds | 7311, 7312, 7313 | VERIFIED |
| Source PyTorch | `torch.manual_seed(model_seed)` | VERIFIED |
| Source NumPy | `numpy.random.seed(model_seed)` and seeded generator for epoch permutations | VERIFIED |
| Target/stage minibatches | `default_rng(model_seed+center+100*stage)`；M0 uses `model_seed+center` | VERIFIED |
| Corruption | base attack seed 9417; SeedSequence keyed by center/stage/role/cycle | VERIFIED |
| Bootstrap | 2904, 4,000 replicates | VERIFIED |
| Python `random` | scientific path未发现调用；显式 Python-random seed NOT FOUND | NOT FOUND |
| CUDA | cuDNN benchmark false、deterministic true | VERIFIED |
| Strong deterministic mode | 未发现 `torch.use_deterministic_algorithms(True)` 或 CUBLAS workspace config | NOT FOUND |

主 final manifest：`2 methods × 30 centers × 3 seeds × 4 streams = 720` complete trajectories，每条 24 stages，因此 17,280 stage rows。主论文五条件聚合把 clean stream 按每 center 的四种 regime 拆为 stationary/gradual/abrupt/recurring，再加入 mixed stream。baseline phase 为 `6×30×3×4=2,160` trajectories；generality 为 2,160；Alibaba 为 1,200。

对任一固定 method/scenario 的 harmful frequency，基础 denominator 为 `centers × seeds × 24 stages`；聚合时以 center 为 inferential unit。artifact-level exact-equivalence 审计在本机执行中通过，但缺少强制 deterministic-algorithms 配置，因此不能声称任意硬件/软件环境下 bitwise reproducible。

## 20. Manuscript-vs-Implementation Consistency Matrix

| Manuscript item | Manuscript claim | Actual implementation | Status | Evidence | Severity |
|---|---|---|---|---|---|
| Canonical method | Candidate adaptation → paired temporal verification → selective commitment | 正是 Final V2 SinglePath + recent/history gate；旧 block-candidate/trimmed aggregation未使用 | MATCH | E01–E05 | NONE |
| Candidate isolation | Candidate does not automatically overwrite deployed model | deepcopy parent；commit 后选择 deployed | MATCH | E06–E07 | NONE |
| Service causality | Future service unavailable at decision time | `service()` 需 current-stage decision token | MATCH | E08 | NONE |
| History timing | Current verification enters history after decision | 实际先 score/decision，再 append | MATCH | E06 | NONE |
| History initialization | 未给出足够操作定义 | `[800,1000)` 预填充 6 blocks，非空 | UNDER-SPECIFIED | E08–E09 | MAJOR |
| History capacity | 12 | 12 block objects，FIFO；Final H1 约两 stages | MATCH | E02,E06 | NONE |
| Verification blocks | Chronological blocks | 6 个 ordered `array_split` window-origin blocks；目标不重叠、input context重叠 | UNDER-SPECIFIED | E09–E10 | MAJOR |
| Candidate adaptation data | complete update subset | 全部 update windows构成 pool；每步 batch64有放回随机采样，并非 full batch | UNDER-SPECIFIED | E07 | MAJOR |
| Optimizer table | SGD/MSE/50, LR=.01, clipping=1 | 完全一致；fresh optimizer、weight decay0未写明 | UNDER-SPECIFIED | E02,E07 | MINOR |
| Exact gate | `U_rec<=-delta_imp` and `U_hist<=delta_ret` | 同方向，等号 commit | MATCH | E02,E06 | NONE |
| MAD | median/MAD robust statistic | unscaled MAD，无1.4826 | UNDER-SPECIFIED | E10 | MINOR |
| Stage chronology | update → verification → service | raw-first 400/240/400；服务仅 decision 后开放 | MATCH | E08 | NONE |
| Window boundary | maintenance subsets disjoint | raw segments disjoint并各自构窗；不跨角色边界 | UNDER-SPECIFIED | E08 | MAJOR |
| Delayed data reuse | 未完整说明下一 stage 数据来源 | stage t service raw interval成为 stage t+1 update | UNDER-SPECIFIED | E08 | MAJOR |
| Initial model | 已部署 initial DT | source pretrain + target warm-up adaptation；无 validation selection | UNDER-SPECIFIED | E11–E12 | MAJOR |
| Five primary conditions | stationary/gradual/abrupt/recurring/mixed | 四个 deterministic base regimes；mixed 为 base regime 上的污染 overlay | UNDER-SPECIFIED | E13–E14 | MAJOR |
| Drift onset | stage-level description | exact raw onset 6520，即 stage-9 verification起点 | UNDER-SPECIFIED | E13 | MINOR |
| Corruption α | corruption fraction / later称 nominal fraction | 10 strata逐块 floor；verification实际比例低于 nominal α | UNDER-SPECIFIED | E14 | MINOR |
| Persistent/replay/burst | 名称级描述 | stage内固定 bias、warm-up-tail replacement、每stratum连续 burst | UNDER-SPECIFIED | E14 | MAJOR |
| Calibration | loss subject to harmful/downside constraints | 16-kappa grid + verification-only relative-CI constraints + fixed tie-break | UNDER-SPECIFIED | E15–E17 | MAJOR |
| Frozen final config | Table values | 全部数值与 frozen config 完全一致 | MATCH | E02–E04 | NONE |
| Heldout independence | final pool held out until freeze | pre-heldout provenance false/false；freeze/leakage audits PASS | MATCH | E04,E18 | NONE |
| ValidationCommit | validation-based baseline | whole-verification mean threshold；calibration failure触发 retain-all，final commit 0 | UNDER-SPECIFIED | E19–E20 | MAJOR |
| Baseline update budget | comparable adaptation | active methods各50 optimizer updates；EWC/ER/Proposed总计算与数据不同 | UNDER-SPECIFIED | E07,E19,E21 | MAJOR |
| Harmful definition | commit and candidate future loss exceeds retained-state loss | `commit and delta_srv>0`；delta正是 candidate-current clean service MSE | MATCH | E06,E22 | NONE |
| Harmful denominator | all center-stage opportunities | 所有24 stages；conditional metric另以commits为分母 | MATCH | E22–E23 | NONE |
| Cluster inference | center statistical unit，3 seeds averaged，4,000 paired bootstrap | 实际相同，seed=2904 | MATCH | E23 | NONE |
| Main numeric claims | MSE cost 6.8–13.2%；harmful/downside大幅下降；vs Frozen -34.9% | final tables精确支持所报舍入值 | MATCH | E24–E25 | NONE |
| Runtime table | maintenance cost comparison | 数字匹配；计时排除 service、disk I/O、model load，且无明确统一 warm-up | UNDER-SPECIFIED | E06,E24 | MAJOR |
| Proposed runtime < Always-FT | 表中如此 | artifact确认；代码无 rejection shortcut；确定原因 NOT FOUND | MATCH | E24 | NONE |
| Architecture/horizon | MLP/TCN/GRU、H1/H4，不重调参数 | 矩阵及固定 gate均匹配 | MATCH | E26–E28 | NONE |
| Generality scope | 在测试架构/步长上保持趋势 | 12/12 setting-method condition comparisons支持定性结论；不支持普适不变性 | MATCH | E27–E28 | NONE |
| Alibaba external trace | 40 machines direct transfer，无 target recalibration | 原 40-machine split复用，40×3×2×5；final gate不变 | MATCH | E29–E33 | NONE |
| Alibaba 6.49% | mixed harmful frequency | `187/2880=6.4931%`，all-stage denominator | MATCH | E32–E33 | NONE |
| Alibaba sampling | production trace | irregular timestamps retained；物理时间单位/固定 interval未找到 | NOT VERIFIABLE | E29–E30 | MINOR |
| Reproducibility | seeded execution |关键 RNG 已固定；未启用 PyTorch strongest deterministic-algorithm guard | UNDER-SPECIFIED | E04,E34 | MINOR |

没有发现 `MISMATCH` 行，亦没有 BLOCKER。`PASS WITH REQUIRED CLARIFICATIONS` 的原因是多项可复现性细节缺失，而非论文公式与 final execution 相反。

## 21. Information Missing from the Current Manuscript

以下只列为科学复现所需的事实：

1. `H_{c,0}` 来自 target raw `[800,1000)`，在 stage 1 前已填充 6 blocks。
2. 每个 verification set 固定分成 6 个 chronological window-origin blocks；目标索引不重叠，但相邻 raw blocks 共享输入 context；capacity 12 的单位是 blocks。
3. MAD 未乘 robust-normal scaling constant。
4. Candidate 每 stage由 deployed parent deep copy；fresh SGD；50 次 batch-64 with-replacement updates；optimizer state不跨 stage；weight decay 0。
5. raw-first split及精确 sizes：warm-up800、initial-history200、stage update400、verification240、service400；H1 window counts 304/144/304；下一 stage update复用已成熟的上一 service raw interval。
6. Source checkpoint training与 target-specific M0 warm-up adaptation的完整流程，以及无 validation checkpoint selection。
7. 四个 drift函数、精确 raw onset/interval、30 centers的 regime assignment，以及 mixed 是 base regime上的 telemetry corruption overlay。
8. α 的 per-stratum floor定义及 verification 的实际污染比例；random/persistent/burst/replay 的数值、位置和 replay source。
9. V2.1 calibration 的 16 组 kappa grid、固定参数、三个 absolute safety constraints、两个 verification-only paired-CI constraints和 tie-break。
10. ValidationCommit threshold grid、`calibration_failure_retain_all` fallback及 final commit=0。
11. ER replay budget、EWC λ/γ/Fisher样本、Huber δ，以及“matched 50 update steps”不等同于相同总计算。
12. Runtime计时包含/排除范围、CUDA synchronization、mean aggregation、无明确 warm-up。
13. MLP/TCN/GRU的具体层结构；H4只改变窗数，未重新 calibration。
14. Alibaba positional columns、去重/过滤、17,000-point截断、缺失mask、无插值、machine split，以及不规则时间的处理。
15. RNG key composition、bootstrap seed，以及当前 deterministic设置的实际边界。

## 22. Implementation Facts That Must NOT Be Added to the Paper

- V1 Legacy Full 的 parent-anchored block-consensus candidate construction。
- V1 的 trimmed state-delta aggregation或 multi-candidate construction作为 Final V2 核心。
- V2 development grid 中未选中的 AdaptiveDual、recovery branch、history realignment、V3/V4 variants。
- post-calibration GO-5 completion、crash recovery、status-writer retry、watcher、worker topology等 execution/debug provenance作为科学方法。
- P6 joint-DAG、persistent candidate/evidence caches、preprocessing reuse benchmark等旧执行加速路径。
- config/source 中存在但 final manifest未启用的默认值、smoke参数或 stale experiment arms。
- CLeaR、OracleCommit、MER-Reg 等未进入 Final V2 七方法主 benchmark 的方法。
- 把 ValidationCommit 的 retain-all fallback 描述成 RAVM-DT gate的一部分。
- 把 Alibaba 结果称为 fresh external confirmation；它是冻结 40-machine split 的 external-domain transfer evaluation。
- 把 runtime差异解释成拒绝 candidate 后少训练；实际没有该 shortcut。

## 23. Unresolved Questions

1. **NOT FOUND**：Alibaba timestamp 的物理单位和数据提供方声明的 nominal sampling interval。实现只保证按原时间戳排序、去重、不插值并保留 irregular gaps。
2. **NOT FOUND**：为何 synthetic 正式运行中 Proposed 的均值计时低于 Always-FT。结果与计时代码均可验证，但独立 runs 的系统调度/热状态不足以建立机制因果。
3. **NOT FOUND**：所有正式运行前是否执行了完全相同的显式 GPU warm-up；代码中没有统一 warm-up步骤。
4. **NOT FOUND**：跨不同 GPU、CUDA、cuDNN/PyTorch 版本的 bitwise reproducibility。当前 artifacts内部 exact audits PASS，但未启用最强 deterministic-algorithm enforcement。
5. **STRONGLY INFERRED**：Alibaba positional columns 的语义来自读取代码及旧 repository 列名映射；final archive中未找到独立官方 schema artifact。CPU target、范围过滤、最终张量内容和 hashes 本身已验证。

上述问题不改变当前 final artifacts 的完整性或论文已报告数字，但限制可复现声明的精确范围。

## 24. Evidence Index

- **[E01]** `configs_v2_final/frozen_v2_final_method.yaml`：`FINAL_METHOD_FROZEN`、method id、SinglePath、50 steps、MSE、capacity 12、GRU/H1、scientific commit/core hash。
- **[E02]** `configs_v2_final/frozen_v2_final_commit_config.yaml`：final kappa/delta/rho/epsilon；SHA sidecar与实算 `7275a287...`。
- **[E03]** `configs_v2_final/frozen_v2_final_provenance.json`：source checkpoint hashes、seeds、stages、L、data/attack seeds、pre-heldout false/false。
- **[E04]** `audits_v2_final/final_method_freeze_audit.json`、`final_manifest_freeze_audit.json`、`final_heldout_access_audit.json`、`final_leakage_audit.json`：freeze/seal/leakage PASS。
- **[E05]** Git commit `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`；当前 `core/engine.py`, `core/models.py`, `core/protocol.py`, `core/v2_engine.py` 对该提交无 diff。
- **[E06]** `core/v2_engine.py`, final lifecycle loop（约 lines 187–290）：history init、adapt、scores、decision seal、append、maintenance timer、service evaluation和deployed assignment。
- **[E07]** `core/models.py`, `adapt`（约 lines 41–55）：deepcopy、fresh SGD、replacement minibatches、MSE/Huber/EWC、clip、50 steps。
- **[E08]** `core/protocol.py`, `spans`, `Timeline.initial_history`, `maintenance`, `record_decision`, `service`（约 lines 25–86）：raw boundaries与capability gate。
- **[E09]** `core/engine.py`, `evidence_blocks`（约 lines 9–15）：由 chronological window indices重建 six raw block segments。
- **[E10]** `core/protocol.py`, `block_indices`（约 lines 53–56）及 `core/engine.py`, score helpers：ordered `array_split`、raw MSE difference、median、unscaled MAD。
- **[E11]** `scripts/pretrain.py`：source center ranges、raw `[0,1000)`、Adam `.001`、50 epochs、batch64、MSE、seeded permutation。
- **[E12]** `core/engine.py`, `initial_model`（约 lines 52–62）与 `audits_v2_final/final_initial_checkpoint_manifest.json`：source load + target warm-up `[0,800)` adaptation及checkpoint hashes。
- **[E13]** `scripts/v2_final_minimal_runner.py`, final center materialization/shift（约 lines 93–120）：center assignment、stationary/gradual/abrupt/recurring q函数及特征/target transform。
- **[E14]** `scripts/v2_final_minimal_runner.py`, `_v2_attack`，以及 `core/protocol.py`, attack/replay source：strata、alpha floor、mixed cycle、bias、burst、random、replay和seed keys。
- **[E15]** `audits_v2_dev/v2_development_execution_manifest.json`、`v2_development_integrity.json`、`v2_structural_selection.json`：4,800 development grid、20 centers和structural winner。
- **[E16]** `audits_v2_dev/v2_1_security_aware_calibration_execution_manifest.json`：frozen 16-arm grid、20 calibration centers、3 seeds、verification-only extension、2,040 jobs。
- **[E17]** `audits_v2_dev/v2_1_security_aware_calibration.json`：14/16 feasible、objective、constraints、tie-break、selected `kr0_kh0.5`、integrity与heldout flags。
- **[E18]** `configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json`：2 methods、30 centers、3 seeds、4 streams、720 trajectories；SHA `b4428cf...`。
- **[E19]** `core/engine.py`, baseline branches（约 lines 90–136）：Always/ER/EWC/Huber/Validation/Frozen adaptation与commit逻辑。
- **[E20]** `calibration_summary.json`、`configs/frozen_baseline_config.yaml` 与 frozen baseline manifest：Validation threshold grid、`calibration_failure_retain_all`、`validation_retain_all=true`。
- **[E21]** `audits_v2_final_baselines/final_benchmark_manifest.json`、`baseline_execution_integrity_audit.json`、`baseline_pairing_hash_audit.json`：2,160 baseline trajectories、steps和pairing PASS。
- **[E22]** `core/engine.py` stage-row construction（约 line 156）及 `core/v2_engine.py` result fields（约 lines 315–360）：`delta_srv`、harmful/downside、state/data/attack hashes。
- **[E23]** final analysis scripts及 `configs_v2_final/frozen_v2_minimal_analysis_plan.json`：center aggregation、paired center-cluster bootstrap、4,000 replicates、seed 2904。
- **[E24]** `results_v2_final_baselines/final_main_table.csv`：七方法 final metrics、runtime、GPU memory、persistent buffer bytes。
- **[E25]** `results_v2_final_baselines/proposed_vs_baseline_paired.csv` 与 `audits_v2_final/final_confirmatory_verdict.json`：relative differences、paired CI与 `CONFIRMED` verdict。
- **[E26]** `core/models.py`, model constructors：GRU、MLP、TCN结构。
- **[E27]** frozen generality manifest/protocol及 `results_v2_generality/generality_trajectory_index.csv`：3×2×2×3×20×3 matrix和GRU-H1复用。
- **[E28]** `results_v2_generality/generality_main_table.csv`、`generality_paired_comparisons.csv`：固定配置下 architecture/horizon定性结果。
- **[E29]** `scripts/prepare_alibaba.py`：archive checksum、filter/sort/dedup、17,000 observations、normalization/masks、no interpolation。
- **[E30]** `alibaba_pool_manifest.json`：100-machine hashed split、archive provenance和irregular timestamp policy。
- **[E31]** `scripts/v2_alibaba_external_freeze.py`、Alibaba frozen protocol/manifest：40 machines、3 seeds、2 scenarios、5 methods、不重调 gate。
- **[E32]** `audits_v2_alibaba/alibaba_protocol_provenance_audit.json`、`alibaba_execution_integrity_audit.json`、`alibaba_pairing_audit.json`、`alibaba_leakage_audit.json`：1,200/1,200、28,800 rows、pairing/leakage PASS。
- **[E33]** `results_v2_alibaba/alibaba_scenario_summary.csv`、`alibaba_paired_comparisons.csv`：6.4931% mixed harmful、commit rate和machine-cluster CI。
- **[E34]** reproducibility setup in model/pretrain/runner scripts：torch/NumPy seeds、cuDNN deterministic/benchmark flags；未发现 Python-random scientific use或`torch.use_deterministic_algorithms(True)`。
- **[E35]** `audits_v2_final/final_execution_integrity_audit.json`：720 valid、0 missing/duplicate/unexpected/partial、17,280 stage rows、0 chain/hash/order errors。
- **[E36]** `paper_figures/scripts/build_paper_data.py`、`finalize_paper_package.py` 与 `paper_figures/audits/figure_determinism_audit.json`：final result directory到论文图的数据链。
- **[E37]** 当前论文包中的 `main.tex`、表格与 figure files，以及 `main.pdf`：方法公式、参数表、实验陈述和最终数字；其 figure PDFs 与 `paper_figures/pdf/` 对应 outputs 完全同哈希。

审计结论以 final frozen manifests/configs 和实际 final artifacts 为最高优先级；README、旧 V1 报告、development-only branches、失败运行与默认参数没有被用来覆盖最终执行事实。
