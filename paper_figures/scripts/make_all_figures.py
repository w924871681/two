from __future__ import annotations
import subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCRIPTS=["build_paper_data.py","fig2_overall_baseline.py","fig3_corruption_severity.py","fig4_benign_evolution.py","fig5_mechanism_analysis.py","fig6_sensitivity_generality.py","fig7_alibaba_external.py","finalize_paper_package.py"]

def main():
    for name in SCRIPTS:
        subprocess.run([sys.executable,str(HERE/name)],check=True,cwd=HERE.parents[1])
    print("PAPER_FIGURE_PACKAGE_COMPLETE")

if __name__=="__main__":main()
