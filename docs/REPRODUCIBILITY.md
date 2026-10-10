# Reproduction and artifact guide / 复现与材料说明

This guide describes the published Paper 2 RAVM-DT snapshot. It distinguishes inspecting completed experiments, rebuilding figures from those experiments, and rerunning model training. The publication process did not retrain models or regenerate experimental trajectories.

本说明针对第二篇 RAVM-DT 公开材料，区分查阅已完成实验、根据已有结果重绘图表、重新训练模型三种操作。本次发布未重新训练，也未重新生成实验轨迹。

## 1. Obtain a working copy / 获取工作副本

```bash
git clone https://github.com/w924871681/two.git
cd two
git checkout ravm-dt-paper2-v1
```

The release checkout is suitable for viewing the exact publication snapshot. Make a separate branch/copy before regenerating files. A Git clone includes the original history and frozen tags. `RAVM-DT-code-results-paper-v1.zip` contains the corresponding published files but no Git database; original runners that verify historical tags cannot satisfy those checks using only the ZIP.

该版本对应发布快照。重建文件前可另建分支或副本。Git 克隆保留原历史及冻结标签；`RAVM-DT-code-results-paper-v1.zip` 提供同等材料文件但不含 Git 历史，仅使用 ZIP 无法满足原运行器的历史标签检查。

The five original frozen tags are:

```text
v1-final-frozen
v2-final-baseline-benchmark-frozen
v2-final-minimal-frozen
v2-final-remaining-master-v1
v2-robustness-severity-frozen
```

The final scientific implementation commit is `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`; the publication release adds packaging and documentation while preserving the scientific source files and recorded provenance.

最终科学实现提交为 `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`；公开发布增加整理与说明，保留科学源码及原溯源信息。

## 2. Environment / 环境

`configs_v2_final/frozen_v2_final_environment.json` records the original frozen environment:

| Component / 组件 | Recorded value / 原冻结记录 |
|---|---|
| Python | 3.11.15 |
| PyTorch | 2.5.1+cu121 |
| CUDA reported by PyTorch | 12.1 |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU |
| OS | Windows |
| Original interpreter / 原解释器 | `C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe` |

Additional packages observed in that local environment at publication time are listed below. These observations are not a claim that every package version was individually frozen during the original experiments.

以下为发布时在本机环境中观察到的版本，不意味着每个包都在原实验时单独完成了版本冻结。

| Package | Observed version / 发布时观察版本 |
|---|---|
| numpy | 2.4.6 |
| pandas | 3.0.5 |
| matplotlib | 3.11.1 |
| Pillow | 12.3.0 |
| pytest | 9.1.1 |

For the original CUDA 12.1 PyTorch build and the observed analysis packages, install into an appropriate Python 3.11 environment:

在合适的 Python 3.11 环境中，原 CUDA 12.1 PyTorch 构建及观察到的分析依赖可按以下方式安装：

```bash
python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r requirements-observed-20261010.txt
```

`pytest` is needed only for tests. A compatible CPU PyTorch installation can be sufficient for the figure/aggregation import chain; that does not satisfy the original GPU experiment runner guards. `make_all_figures.py` indirectly imports PyTorch through the statistical helper and experiment modules, even though the figure pipeline does not execute training. Running the individual `fig*.py` files against the included `paper_figures/data/` CSVs only needs NumPy, pandas, Matplotlib, and Pillow for the complete figure package finalization.

`pytest` 仅供测试。图表流水线虽不训练模型，但统计助手的间接导入链会加载 PyTorch；兼容 CPU 版可以满足该导入需求，但不能满足原 GPU 实验运行器的保护条件。只基于现成绘图 CSV 执行单张 `fig*.py` 需要 NumPy、pandas、Matplotlib；完整图表包整理另需 Pillow。

## 3. Inspect completed experiments / 查阅已完成实验

Before rebuilding outputs, check the distributed snapshot from the repository root:

重建输出前，可在仓库根目录校验发布材料：

```bash
python tools/verify_snapshot.py
```

This read-only verifier needs only Python's standard library. It checks every source file listed in the publication manifest, counts the five formal trajectory suites, and verifies that the supplied paper PDF matches the PDF inside the original submission ZIP. A `PASS` verifies this snapshot's integrity, not a new training run. Rebuilding files later may change their bytes and therefore change this verification result.

该只读校验程序仅需 Python 标准库，检查发布清单列出的原材料文件、五组轨迹数量，并核对独立论文 PDF 与原投稿 ZIP 内 PDF。`PASS` 表示快照完整性通过，不代表重新训练通过；后续重建文件可能改变字节及校验结果。

| Result directory / 结果目录 | Trajectory CSV count / 轨迹数 | Purpose / 用途 |
|---|---:|---|
| `results_v2_final/trajectories/` | 720 | Final confirmatory comparison / 最终确认实验 |
| `results_v2_final_baselines/trajectories/` | 2,160 | Controlled baseline benchmark / 基线比较 |
| `results_v2_severity/trajectories/` | 2,160 | Corruption severity extension / 扰动强度扩展 |
| `results_v2_generality/trajectories/` | 1,800 | Architecture and forecast horizon / 架构与预测跨度 |
| `results_v2_alibaba/trajectories/` | 1,200 | External Alibaba trace evaluation / 外部数据评估 |
| **Total / 合计** | **8,040** | Five final suites only / 仅五组正式实验 |

Summary tables, paired comparisons, trajectory indices, and execution records are included beside the trajectory folders. Their audit records are under the corresponding `audits_v2_*` directories. Development and calibration outputs remain in `results_v2_dev/`, separate from the final confirmatory pools and the 8,040-file count.

轨迹目录旁保留汇总表、配对比较、轨迹索引和执行记录，审计证据位于对应 `audits_v2_*` 目录。开发和校准结果保留在 `results_v2_dev/`，与最终确认数据池及 8,040 条统计独立。

Only two legacy V1 result files are needed by the published figure pipeline and included at their original paths: `results/q4_ablation/raw_episode_results.csv` and `results/q4_ablation/summary.csv`. Other legacy V1 outputs, failed-run archives, and executor caches are outside this publication snapshot. The original project README is preserved at `docs/original_project_readme.md` as historical context; its V1 workflow is not the Paper 2 release quick start.

图表流水线需要的旧版 V1 结果仅两份 Q4 文件，按原路径保留；其他旧版 V1 输出、失败运行归档和执行缓存不在本次快照内。`docs/original_project_readme.md` 保留旧项目说明，其 V1 流程不作为第二篇发布材料的快速运行入口。

## 4. Rebuild figures and tables / 重建图表

From the repository root, in a working copy:

在仓库根目录的工作副本中运行：

```bash
python paper_figures/scripts/make_all_figures.py
```

The pipeline first checks six frozen report hashes and four result hash manifests, then aggregates existing outputs, redraws six experimental figures, rebuilds tables, and writes figure-package audits. Outputs are written into `paper_figures/data/`, `pdf/`, `png/`, `tables/`, and `audits/`. It uses the already completed experiment outputs and does not execute model training or parameter selection.

流水线先检查六份冻结报告和四份结果哈希清单，再汇总已有实验输出、重绘六张实验图、重建表格并写入图表包审计。输出写入 `paper_figures` 下的 `data/`、`pdf/`、`png/`、`tables/`、`audits/`，不执行模型训练或参数选择。

Besides the five final result directories, the pipeline reads these mechanism/development files:

除五组正式结果外，流水线还读取以下机制分析和开发材料：

```text
results/q4_ablation/raw_episode_results.csv
results/q4_ablation/summary.csv
results_v2_dev/development/development_trajectory_metrics.csv
results_v2_dev/v2_1_security_calibration/security_pareto_table.csv
```

| Plot stem / 绘图文件前缀 | Manuscript figure / 稿件图号 |
|---|---|
| `fig2_overall_baseline` | Fig. 3 |
| `fig3_corruption_severity` | Fig. 4 |
| `fig4_benign_evolution` | Fig. 5 |
| `fig5_mechanism_analysis` | Fig. 6 |
| `fig6_sensitivity_generality` | Fig. 7 |
| `fig7_alibaba_external` | Fig. 8 |

The numbering offset reflects manuscript assembly. The manuscript's concept/framework figures 1–2 are in `paper/latex/figures/`; they are not generated by this six-figure data plotting pipeline. The submitted experimental PDFs are also preserved under the manuscript figure names in that directory. Regenerated image bytes can depend on the plotting environment; the distributed originals and their recorded hashes remain the publication reference.

图号偏移源于稿件组装。稿件图 1–2 为问题设置／方法框架图，位于 `paper/latex/figures/`，不由六张数据图流水线生成；该目录也保留按稿件图号命名的实验 PDF。重新绘制的图像字节可能受绘图环境影响，已发布原图与对应哈希仍为发布版本依据。

## 5. Inputs and checkpoints / 输入和权重

Download `RAVM-DT-reproduction-inputs-v1.zip` from the [versioned release](https://github.com/w924871681/two/releases/tag/ravm-dt-paper2-v1) and extract its contents into a working copy's root. This adds `data/center_*.npz`, `checkpoints/*.pt`, `checkpoints/*.json`, and the input manifest.

从[指定版本 Release](https://github.com/w924871681/two/releases/tag/ravm-dt-paper2-v1)下载输入附件，解压到工作副本根目录。它提供 120 份合成 NPZ、顶层全部模型权重和 JSON 元数据，并附输入清单。

The input ZIP contains 120 synthetic centers and 1,908 top-level `.pt`/`.json` checkpoint/metadata files: 2,028 input files in total, plus its manifest. It excludes the calibration/joint-DAG candidate/evidence cache subdirectories, all original third-party Alibaba raw traces, and all Alibaba-derived NPZs. Checkpoint files include historical/source and external-experiment model artifacts; their presence does not include the underlying external trace data.

输入包合计 2,028 份输入文件（120 份合成 NPZ 和 1,908 份顶层模型／元数据），另附清单。包内不含 calibration 或 joint-DAG 的候选／证据缓存子目录，不含 Alibaba 原始轨迹及派生 NPZ。模型文件中可能包含历史、源模型和外部实验模型材料；模型文件不等同于提供底层外部轨迹。

The file-level input hashes are recorded in `docs/reproduction_inputs_manifest.json` and `INPUTS_MANIFEST.json` inside the input ZIP. The publication source file manifest is `docs/source_snapshot_manifest.json`. Preserve exact file bytes: `.gitattributes` uses `* -text`, so Git does not normalize line endings and break the frozen SHA-256 checks.

输入包逐文件哈希见 `docs/reproduction_inputs_manifest.json` 和包内 `INPUTS_MANIFEST.json`，原材料快照清单见 `docs/source_snapshot_manifest.json`。请保留文件原字节；`.gitattributes` 的 `* -text` 避免自动换行转换破坏冻结 SHA-256。

## 6. Rerunning experiments / 重新执行实验

The original final experiment entry points are retained:

| Phase / 阶段 | Execution script / 执行入口 | Analysis script / 分析入口 |
|---|---|---|
| Final confirmation / 最终确认 | `scripts/v2_final_minimal_runner.py` | `scripts/v2_final_minimal_analyze.py` |
| Baselines / 基线 | `scripts/v2_final_baseline_runner.py` | `scripts/v2_final_baseline_analyze.py` |
| Severity / 扰动强度 | `scripts/v2_severity_runner.py` | `scripts/v2_severity_analyze.py` |
| Generality / 泛化 | `scripts/v2_generality_runner.py` | `scripts/v2_generality_analyze.py` |
| Alibaba external / 外部验证 | `scripts/v2_alibaba_external_runner.py` | `scripts/v2_alibaba_external_analyze.py` |

These entry points are archival experiment runners with frozen preflight checks, not a portable command that promises a fresh run on every machine. For example, `v2_final_minimal_runner.py` validates the original interpreter path, Python 3.11.15, PyTorch 2.5.1+cu121, CUDA 12.1 availability, RTX 3060 Laptop GPU, frozen artifact/source hashes, and the `v2-final-minimal-frozen` tag. Other runners enforce their own environment and provenance checks. Running them with completed output files generally reuses valid trajectories; it is not evidence of a fresh training run.

这些入口是带冻结预检的原始实验运行器，不是承诺任意机器开箱即用的完整重跑命令。例如最终确认运行器检查原解释器绝对路径、Python／Torch／CUDA、原 GPU、代码与配置哈希以及原冻结标签。其他运行器各有对应保护条件；已有有效结果时通常会复用轨迹，不能据此声称完成了新训练。

For a new experimental execution, use a separate clone, restore required synthetic inputs/checkpoints, read the relevant frozen protocol and runner guards, and document any environment/portability adaptations together with a new output location and new run provenance. Do not change the distributed frozen manifests to make a modified environment appear identical to the recorded original. The published run outputs remain available for comparison.

如需新实验，应另建克隆，恢复必要的合成输入和权重，阅读相关冻结协议及运行器预检，记录环境／可移植性适配，使用新的输出位置并建立新运行溯源。不要修改原冻结清单，使新环境看似与原实验相同。已发布结果可用于后续比较。

Development/calibration scripts remain under `scripts/` and their outputs under `results_v2_dev/`. They are separate stages with fixed pools; do not mix their rows into the final confirmatory analysis. Historical recovery, acceleration, and audit scripts may reference omitted caches/archives or the author's other local repositories. Their source and recorded audit outcomes are preserved, but those historical execution environments are not reconstructed by this release.

开发／校准阶段使用独立固定数据池，其结果不应混入最终确认分析。部分历史恢复、加速与审计脚本引用本次未包含的缓存、归档或作者本地其他仓库；保留源码与审计记录不意味着本次发布重建了这些历史执行环境。

### Alibaba data / Alibaba 数据

The release distributes external experiment outputs, preprocessing code, and fixed machine split metadata, but neither the original Alibaba archive nor derived NPZ traces. Obtain the matching public trace from its original provider under its original terms before attempting external-trace execution. The original code expects the archive SHA-256:

```text
3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a
```

本发布提供外部实验输出、预处理代码和固定机器划分，不分发 Alibaba 原始压缩包或派生 NPZ。外部实验重跑需要先按原提供方条款获取匹配数据，并核对上述 SHA-256。

`scripts/prepare_alibaba.py` retains the original local archive path `D:/RCF_DTI_pre_submission/data/alibaba2018/raw/machine_usage.tar.gz` and a prior-study exclusion scan under `D:/dt-talk/v127_freeze_clean/results`. The exact fixed split is recorded in `alibaba_pool_manifest.json`; reproduce its exclusions and machine hashes when adapting paths. Merely substituting an available dataset or ignoring the exclusion history does not establish the same external experiment.

预处理脚本保留原归档路径及首篇研究排除记录扫描路径。换机时需根据 `alibaba_pool_manifest.json` 复核机器哈希、排除集合与划分；仅更换可用数据集或忽略历史排除信息，不能认为复现了同一外部实验。

## 7. Manuscript and rights / 论文与权利说明

`paper/RAVM_DT.pdf` preserves the supplied manuscript. `paper/latex/` contains the complete extracted submission project, including `main.tex`, sections, bibliography, figure PDFs, journal template assets, and the supplied compiled PDF. The original archive is also retained as `paper/RAVM_DT_CMC_14Pages_Final_Contrib.zip`; consult `paper/latex/README.md` for its own compilation notes.

论文 PDF、完整投稿 LaTeX 项目与原投稿 ZIP 均保留。项目内包含章节、参考文献、图表及原期刊模板资源，编译说明见 `paper/latex/README.md`。

Submission-time wording such as availability “on request” is intentionally unchanged in the original manuscript/reports. This public repository was released later; it does not retroactively rewrite those source documents or imply a revised publication status.

原稿及报告中“按需提供”等措辞保留投稿时原文。本仓库是后续公开发布的材料，不追溯修改原文，也不据此变更论文发表状态。

`audits/provenance.json` identifies reused generator/configuration files from `paper-code-DT-Twin`, release `v1.2.7`, commit `b679181b3133ab9c3058afcde421d36380001f14`; those files retain `vendor/LICENSE`. Existing author, data-provider, and template rights/notices remain applicable. This release does not assign a new blanket license to the repository, manuscript, or third-party materials.

复用生成器／配置文件来源、版本、提交和哈希见 `audits/provenance.json`，并保留 `vendor/LICENSE`。作者、数据提供方及模板的原权利和声明继续保留，本发布不擅自为整个仓库、论文或第三方材料添加统一许可。
