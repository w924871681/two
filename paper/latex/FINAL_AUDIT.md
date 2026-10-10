# RAVM-DT Final Revision Audit

## 1. Compilation and layout
- CMC/TSP template retained.
- Final compiled page count: **13 pages**.
- Undefined citations: **0**.
- Undefined cross-references: **0**.
- Overfull boxes: **0**.
- Only the template-level `headheight`/package warning remains; no manuscript content is clipped.

## 2. Abstract--Introduction--Conclusion claim closure
- Abstract, Introduction, and Conclusion all define the same problem: post-adaptation candidate-to-deployed state transition under evolving and potentially unreliable monitoring data.
- Abstract ending now uses `selective-transition behavior` rather than the broader `safety--utility behavior` for the severity/generality/external evidence.
- Introduction gap now reads `while retaining useful adaptation`, avoiding the stronger unsupported implication that every necessary update is preserved.
- Main five-condition result ranges remain unchanged and consistent across Abstract, Section 5.2, and Conclusion.
- Alibaba remains explicitly bounded as external-domain transfer; the 6.49% mixed harmful-transition rate remains above the 5% synthetic calibration criterion.

## 3. Figure 1 / Figure 2 terminology
- Figure 1 remains the frozen problem-setting graphic; its shortened in-figure label `Potentially unreliable data` is disambiguated by the caption and surrounding text as monitoring data.
- Figure 2 remains the frozen framework graphic. To preserve image quality while achieving terminology consistency, Section 4 module headings now match the figure exactly:
  - `Candidate-State Adaptation`
  - `Dual-Evidence Verification`
  - `Verification-Guided State Transition`
- The Figure 2 caption explicitly states recent and bounded historical evidence and defines the output as the maintained DT state.

## 4. Reference audit
- Total cited references: **32**.
- References from 2022--2026: **18/32**.
- The CLeaR citation was replaced by Ding et al., ICML 2024, `Understanding Forgetting in Continual Learning with Linear Regression`, to strengthen the continual-regression support.
- The nonessential Avalanche workshop/tooling sentence and reference were removed.
- All 32 bibliography entries are cited.
- No citation key is missing.
- The `.bbl` order matches first citation appearance exactly: **32/32**.

## 5. High-threshold redundancy reductions
Removed without loss of scientific content:
1. Section 3.1 sentence restating that new operational data enable maintenance.
2. Section 4.5 sentence saying concrete values appear in Section 5.
3. Section 5 opening sentence that duplicated the subsection roadmap.
4. Section 5.4 first sentence restating the retain-all conclusion before the supporting results.
5. Related-work sentence about continual-learning evaluation tooling.

## 6. Scientific boundaries preserved
The revision does **not** remove or weaken the following safeguards:
- service data are unavailable at decision time;
- current verification enters history only after the decision;
- evidence scores are not statistical confidence bounds;
- calibration is offline rather than an online guarantee;
- corruption-severity safety is not claimed to be monotone;
- the frozen kappa setting is not claimed universally optimal;
- architecture/horizon evidence is not claimed architecture-invariant;
- Alibaba risk calibration is explicitly domain dependent.
