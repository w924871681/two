# RAVM-DT CMC LaTeX Package - 14-Page Final Review Version

This package uses the Tech Science Press / Computers, Materials & Continua (CMC) LaTeX template and contains the RAVM-DT manuscript after the final implementation-to-manuscript audit.

## Included
- Sections 1--6 aligned with the verified Final V2 implementation and final experimental artifacts.
- Figures 1--8, Algorithm 1, Table 1 (main configuration), and Table 2 (maintenance cost).
- 32 references under the TSP Vancouver style.
- Completed author metadata and the six mandatory TSP declarations.
- `SUBMISSION_METADATA.md` with all author emails for submission-system entry.
- A compiled 14-page `main.pdf` preview.

## Final implementation-audit clarifications integrated
- Defined the pre-maintenance initialization of the historical verification buffer.
- Defined chronological verification blocks and the post-decision FIFO history update.
- Aligned candidate adaptation with the executed stochastic mini-batch SGD implementation.
- Added the raw-first lifecycle split, target warm-up initialization, and exact H=1 window counts.
- Added concise lifecycle-regime and corruption construction details.
- Added the executed calibration grid and baseline implementation details, including ValidationCommit's retain-all fallback.
- Added random-seed information and maintenance-timing boundaries.
- Added the external Alibaba-trace preprocessing boundary needed for reproducibility.

## Author and declaration status
The manuscript currently uses:
- Affiliation: `School of Intelligent Science and Engineering, Qinghai Minzu University, Xining 810007, China`.
- Corresponding author: Fengbiao Zan (`zanfb@163.com`).
- Funding: Qinghai Major Science and Technology Special Project, Grant No. `2024-GX-A3` only.
- Data/code availability: available from the corresponding author upon reasonable request; no public repository is assumed.
- AI acknowledgement: OpenAI ChatGPT is disclosed for language polishing and editorial revision.

The `Author Contributions` paragraph should be checked by all authors before submission to ensure that the listed CRediT roles exactly reflect actual contributions.

## Compile
```bash
pdflatex main.tex
bibtex main      # or bibtex8 main, depending on the local TeX distribution
pdflatex main.tex
pdflatex main.tex
```

The compiled preview is 14 pages, remaining within CMC's 15-page research-article APC threshold.
