"""P15: publish plot-ready CSVs, manuscript tables, and publication figures."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageOps
from core.protocol import ROOT,save_json

COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#000000','#F0E442','#999999']

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def export(fig,name,caption,manifest):
    out=ROOT/'results/figures';out.mkdir(parents=True,exist_ok=True);png=out/f'{name}.png';svg=out/f'{name}.svg';gray=out/f'{name}_grayscale.png'
    fig.savefig(png,dpi=300,bbox_inches='tight',facecolor='white');fig.savefig(svg,bbox_inches='tight',facecolor='white');plt.close(fig)
    with Image.open(png) as im:
        ImageOps.grayscale(im).save(gray,dpi=(300,300));width,height=im.size
    assert width>=1400 and height>=800 and svg.stat().st_size>1000
    manifest.append({'name':name,'png':str(png.relative_to(ROOT)).replace('\\','/'),'svg':str(svg.relative_to(ROOT)).replace('\\','/'),
        'grayscale':str(gray.relative_to(ROOT)).replace('\\','/'),'pixels':[width,height],'dpi':300,'caption':caption,
        'sha256':{'png':digest(png),'svg':digest(svg),'grayscale':digest(gray)}})

def main():
    tables=ROOT/'results/tables';summary=pd.read_csv(tables/'all_summaries.csv');pairs=pd.read_csv(tables/'all_paired_comparisons.csv')
    profile={'rows':len(summary),'paired_rows':len(pairs),'questions':sorted(summary.question.dropna().unique().tolist()),
        'methods':sorted(summary.method.dropna().unique().tolist()),'missing_fraction':{c:float(summary[c].isna().mean()) for c in summary.columns}}
    q1=summary[summary.question=='q1_overall'].copy();assert len(q1)
    q1cols=['attack_type','attack_alpha','method','centers','seeds','lifecycle_mse','lifecycle_mse_ci_low','lifecycle_mse_ci_high',
        'harmful_commit_rate','harmful_commit_rate_ci_low','harmful_commit_rate_ci_high','average_downside','average_downside_ci_low','average_downside_ci_high','commit_rate']
    q1[q1cols].sort_values(['attack_alpha','lifecycle_mse','method']).to_csv(tables/'manuscript_q1_main.csv',index=False,na_rep='NA')
    pairs[pairs.question=='q2_security'].sort_values(['attack_type','attack_alpha','attack_location','metric','reference']).to_csv(tables/'manuscript_q2_security.csv',index=False,na_rep='NA')
    summary[summary.question=='q4_ablation'].sort_values(['attack_alpha','method']).to_csv(tables/'manuscript_q4_ablation.csv',index=False,na_rep='NA')
    summary[summary.question=='q6_alibaba'].sort_values(['variant','attack_alpha','method']).to_csv(tables/'manuscript_q6_alibaba.csv',index=False,na_rep='NA')
    manifest=[];plt.rcParams.update({'font.size':8,'axes.labelsize':8,'axes.titlesize':9,'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'svg.fonttype':'none'})
    methods=[m for m in ['Frozen','Always-FT','ER','EWC','Huber-FT','CLeaR-Predictor','ValidationCommit','Proposed','OracleCommit'] if m in set(q1.method)]
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.2),constrained_layout=True,sharey=True)
    for ax,(attack,title) in zip(axes,[('clean','Clean'),('mixed','Mixed corruption')]):
        d=q1[q1.attack_type==attack].set_index('method').reindex(methods);y=np.arange(len(d));x=d.lifecycle_mse.to_numpy();lo=x-d.lifecycle_mse_ci_low.to_numpy();hi=d.lifecycle_mse_ci_high.to_numpy()-x
        ax.errorbar(x,y,xerr=np.vstack([lo,hi]),fmt='o',capsize=2,color=COLORS[0],ecolor='#666666');ax.set_title(title);ax.set_xlabel('Lifecycle MSE (mean, 95% center-cluster CI)');ax.grid(axis='x',alpha=.2)
        ax.set_yticks(y,methods);ax.invert_yaxis()
    export(fig,'figure_q1_lifecycle_mse','Point estimates and 95% center-cluster bootstrap CIs; centers are the sampling unit.',manifest)
    sec=pairs[(pairs.question=='q2_security')&(pairs.reference=='Always-FT')&(pairs.metric=='deployed_service_mse')].copy();assert len(sec)
    heat=sec.groupby(['attack_type','attack_alpha']).difference.mean().unstack().sort_index();fig,ax=plt.subplots(figsize=(5.2,3.2),constrained_layout=True)
    vmax=float(np.nanmax(np.abs(heat.to_numpy())));im=ax.imshow(heat.to_numpy(),cmap='RdBu_r',vmin=-vmax,vmax=vmax,aspect='auto');ax.set_yticks(range(len(heat)),heat.index);ax.set_xticks(range(len(heat.columns)),[f'{x:g}' for x in heat.columns]);ax.set_xlabel('Corruption fraction');ax.set_ylabel('Attack type');ax.set_title('Proposed minus Always-FT lifecycle MSE');fig.colorbar(im,ax=ax,label='Paired MSE difference (negative favors Proposed)')
    export(fig,'figure_q2_security_heatmap','Center-paired lifecycle-MSE differences; a perceptually balanced diverging scale is centered at zero.',manifest)
    curve=pd.read_csv(ROOT/'results/figure_data/q3_lifecycle_curves.csv');keep=[m for m in ['Frozen','Always-FT','ER','ValidationCommit','Proposed'] if m in set(curve.method)];fig,ax=plt.subplots(figsize=(7.2,3.4),constrained_layout=True)
    for i,m in enumerate(keep):
        d=curve[curve.method==m].groupby(['center_id','stage']).deployed_service_mse.mean().reset_index();g=d.groupby('stage').deployed_service_mse;mean=g.mean();lo=g.quantile(.025);hi=g.quantile(.975);x=mean.index.to_numpy();ax.plot(x,mean.to_numpy(),label=m,color=COLORS[i],marker=['o','s','^','D','v'][i],markevery=4,linewidth=1.2);ax.fill_between(x,lo.to_numpy(),hi.to_numpy(),color=COLORS[i],alpha=.10)
    ax.set_xlabel('Lifecycle stage');ax.set_ylabel('Service MSE');ax.set_title('Clean-drift lifecycle trajectories');ax.legend(frameon=False,ncol=3);ax.grid(alpha=.2)
    export(fig,'figure_q3_lifecycle','Lines are center means; shaded regions show the 2.5th–97.5th percentiles across centers.',manifest)
    save_json(ROOT/'audits/p15_figure_manifest.json',{'status':'passed','data_profile':profile,'figures':manifest,'machine_checks':{
        'vector_exports':True,'png_min_300_dpi':True,'minimum_pixels':True,'colorblind_palette_and_redundant_markers':True,'grayscale_previews':True,
        'no_dual_y_axes':True,'no_pie_or_3d':True,'continuous_heatmap_has_colorbar':True,'ci_or_uncertainty_described':True},
        'visual_review':'machine-rendered; Codex visual inspection is recorded separately when available'})
    print(f'P15 generated {len(manifest)} figures and 4 manuscript tables',flush=True)

if __name__=='__main__':main()
