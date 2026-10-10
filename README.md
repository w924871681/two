# RAVM-DT — Paper 2 research artifacts / 第二篇论文研究材料

This repository accompanies the second RAVM-DT paper. It publishes the original implementation, frozen configurations, completed experimental outputs, manuscript, and figure sources. The release packages existing research artifacts; no models were retrained for publication.

本仓库对应第二篇 RAVM-DT 论文，公开原始实现、冻结配置、已完成的实验输出、论文及图表源文件。本次发布整理已有成果，没有重新训练或重新生成实验轨迹。

**[Paper / 论文 PDF](paper/RAVM_DT.pdf) · [LaTeX source / 论文源码](paper/latex/main.tex) · [Reproduction guide / 复现说明](docs/REPRODUCIBILITY.md) · [Release downloads / 下载附件](https://github.com/w924871681/two/releases/tag/ravm-dt-paper2-v1)**

## Contents / 内容

| Location / 路径 | Contents / 内容 |
|---|---|
| `core/`, `scripts/`, `tests/`, `vendor/` | Algorithm, experiment/analysis code, tests, and attributed reused code / 算法、实验分析代码、测试和带来源说明的复用代码 |
| `configs/`, `configs_v2_dev/`, `configs_v2_final/` | Historical, development, and frozen final protocols / 历史协议、开发配置及最终冻结协议 |
| `results_v2_final/` | 720 final confirmatory trajectories / 720 条最终确认实验轨迹 |
| `results_v2_final_baselines/` | 2,160 baseline trajectories / 2,160 条基线轨迹 |
| `results_v2_severity/` | 2,160 severity trajectories / 2,160 条扰动强度轨迹 |
| `results_v2_generality/` | 1,800 architecture/horizon trajectories / 1,800 条架构与预测跨度轨迹 |
| `results_v2_alibaba/` | 1,200 external-trace trajectories / 1,200 条外部数据实验轨迹 |
| `results_v2_dev/` | Separate development and calibration results / 独立的开发与校准输出 |
| `audits*`, root `V2_*_REPORT.md` | Provenance, integrity checks, and original reports / 来源记录、完整性审计及原报告 |
| `paper_figures/` | Figure PDFs/PNGs, data, tables, and plotting scripts / 图表、底层数据、表格及绘图脚本 |
| `paper/` | Supplied PDF, complete LaTeX package, and original submission ZIP / 提供的 PDF、完整 LaTeX 项目和原投稿 ZIP |

The five final suites contain **8,040 trajectory CSV files**. Development/calibration outputs and the two legacy Q4 evidence CSVs are separate from that total. Local plot files numbered **2–7** correspond to manuscript figures **3–8**; manuscript figures 1–2 are included in `paper/latex/figures/`.

五组正式实验合计 **8,040 个轨迹 CSV 文件**；开发、校准及两份旧版 Q4 机制分析 CSV 不计入此数。`paper_figures` 中图号 **2–7** 对应稿件图号 **3–8**；稿件图 1–2 位于 `paper/latex/figures/`。

## Use the artifacts / 使用材料

For completed results and figures, browse the files directly. To rebuild the six experimental figures from published outputs, install the dependencies described in the [reproduction guide](docs/REPRODUCIBILITY.md), then run from the repository root:

现有结果与图表可直接查阅。按[复现说明](docs/REPRODUCIBILITY.md)安装依赖后，在仓库根目录运行以下命令，可从已发布输出重建六张实验图：

```bash
python tools/verify_snapshot.py
python paper_figures/scripts/make_all_figures.py
```

The first command checks the publication snapshot using only Python's standard library. The second validates frozen reports/result hashes, rebuilds figure data, and writes figures/tables; it does not train models. Observed dependency versions are listed in [requirements-observed-20261010.txt](requirements-observed-20261010.txt). Run the figure pipeline in a separate working copy if you want to preserve the distributed files unchanged. Original experiment runners retain strict checks for the recorded interpreter, GPU, source hashes, and/or Git tags. Full experimental execution on another machine requires a documented environment adaptation; the guide explains these limits.

第一条命令仅用 Python 标准库校验发布快照；第二条校验冻结报告与结果哈希、重建绘图数据并写入图表，不训练模型。建议在单独工作副本中重绘以保留发布文件。原实验运行器保留解释器、显卡、代码哈希及／或 Git 标签检查；换机重新执行完整实验需记录环境适配，具体见复现说明。

The [release](https://github.com/w924871681/two/releases/tag/ravm-dt-paper2-v1) provides:

- `RAVM-DT-code-results-paper-v1.zip`: code, results, manuscript, and figures corresponding to the published repository snapshot; no `.git` history.
- `RAVM-DT-reproduction-inputs-v1.zip`: 120 synthetic NPZ inputs and all top-level checkpoint `.pt`/`.json` files; extract into a working copy's root. Execution caches and Alibaba-derived NPZ files are excluded.

发布附件分别提供仓库内容快照，以及 **120 份合成输入与顶层模型权重／元数据**。输入包解压到工作副本根目录；包中不含运行缓存或 Alibaba 派生 NPZ。Alibaba 原始轨迹不在本仓库分发，外部实验结果、固定划分和预处理代码保留。

## Provenance and rights / 来源与权利

The original Git history and five frozen tags are retained. The scientific implementation commit is [`7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`](https://github.com/w924871681/two/commit/7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3). Source artifact bytes are preserved; `.gitattributes` uses `* -text` to prevent newline conversion from invalidating recorded hashes. See [snapshot provenance](docs/source_snapshot_manifest.json).

仓库保留原 Git 历史与五个冻结标签，最终科学实现提交可追溯。原材料保持字节不变，使用 `* -text` 禁止 Git 自动换行转换。原投稿稿件或报告中的“数据可按需提供”等表述保留投稿时原文；本仓库是之后公开发布的材料。

Earlier submission-time statements such as “data available on request” remain verbatim in the original manuscript/reports; this repository is a subsequent public artifact release. Reused files retain their original notices, including [`vendor/LICENSE`](vendor/LICENSE) and [`audits/provenance.json`](audits/provenance.json). No new blanket license is asserted for the manuscript, third-party templates/data, or the entire repository.

复用文件保留原许可及来源。本次发布没有为论文、第三方模板／数据或整个仓库擅自新增统一许可。
