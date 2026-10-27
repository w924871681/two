"""Evidence-led figure drafts. Machine layout checks never pretend to be human review."""
from common import *
import sys,csv
sys.path.insert(0,str(ROOT/'engineering/figure_support'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from profile_data import profile_data
from visual_qa import audit_layout
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#000000']

def export(fig,target,metadata):
    fig.canvas.draw();issues=audit_layout(fig);fig.savefig(str(target)+'.png',dpi=200);fig.savefig(str(target)+'.svg');fig.savefig(str(target)+'.pdf')
    from PIL import Image,ImageOps
    with Image.open(str(target)+'.png')as im:ImageOps.grayscale(im).save(str(target)+'_grayscale.png')
    atomic(str(target)+'.json',dict(**metadata,machine_layout_issues=issues,visual_review='PENDING_AI_OR_HUMAN_REVIEW',publication_ready=False,script='render_figures.py',script_sha256=sha(ROOT/'render_figures.py')));plt.close(fig)

def distribution(path,out,group,metadata):
    frame=pd.read_csv(path);frame['arm']=frame['arm'].astype(str);frame['stream']=frame['stream'].astype(str)
    info=profile_data(str(path),group_cols=['arm','stream']);atomic(out/'DATA_PROFILE.json',json.loads(json.dumps(info,default=str)))
    labels={'mse':'Service MSE (normalized target squared)','harm_frequency':'Harmful commits / all opportunities','mean_downside':'Downside per opportunity (target squared)','commit_rate':'Commit rate','beneficial_recall':'Beneficial-commit recall'}
    for stream in frame['stream'].unique():
        data=frame[frame['stream']==stream];arms=sorted(data['arm'].unique(),key=lambda a:(a!='JOINT__l3__m0',a))
        for metric,label in labels.items():
            if metric not in data:continue
            fig,ax=plt.subplots(figsize=(7.2,max(3.5,.28*len(arms)+1.3)),layout='constrained')
            rng=np.random.default_rng(20261022)
            for index,arm in enumerate(arms):
                y=pd.to_numeric(data.loc[data.arm==arm,metric],errors='coerce').dropna().to_numpy();n=len(y)
                if not n:continue
                ax.scatter(y,index+rng.uniform(-.1,.1,n),s=9,color=COLORS[0]if arm=='JOINT__l3__m0'else'#777777',alpha=.65,zorder=2)
                ax.scatter([y.mean()],[index],s=35,marker='D',facecolor='white',edgecolor='black',zorder=3)
            ax.set_yticks(range(len(arms)),[a.replace('__l3__m0','').replace('__g12','').replace('__g04','')for a in arms]);ax.invert_yaxis();ax.set_xlabel(label);ax.set_title(f'{group} / {stream}');ax.grid(axis='x',alpha=.2)
            if metric in ('harm_frequency','commit_rate','beneficial_recall'):ax.set_xlim(-.02,1.02)
            if metric=='harm_frequency':ax.axvline(.05,color=COLORS[1],ls='--',lw=1)
            if metric=='mean_downside':ax.axvline(5.6036475532487204e-5,color=COLORS[1],ls='--',lw=1)
            fig.suptitle('Points: independent center/machine seed means; diamond: mean.\nTemperature tasks: individual house/room descriptions; no population CI.',fontsize=8)
            export(fig,out/(stream+'_'+metric),dict(**metadata,source_csv=str(path),source_sha256=sha(path),metric=metric,unit=label,stream=stream,actual_points_by_arm={a:int(pd.to_numeric(data.loc[data.arm==a,metric],errors='coerce').notna().sum())for a in arms},interval='none shown; paired cluster percentile95% CIs in PAIRED_ALL_BASELINES.csv',all_available_complete_seed_center_results_included=True,all_other_validated_trajectories_preserved_in_TRAJECTORIES_csv=True,negative_results_retained=True))

def sensitivity(out):
    path=ROOT/'E0_MAIN_TABLES/DEVCAL_JOINT_RESULTS_BY_ARM.csv';frame=pd.read_csv(path);atomic(out/'SENSITIVITY_PROFILE.json',json.loads(json.dumps(profile_data(str(path)),default=str)))
    numeric=[c for c in ('balanced_mse','balanced_clean_mixed_mse','harmful_frequency','mean_downside','commit_rate','service_mse')if c in frame]
    for metric in numeric:
        y=pd.to_numeric(frame[metric],errors='coerce').to_numpy();fig,ax=plt.subplots(figsize=(7.2,3.8),layout='constrained');ax.scatter(np.arange(len(y)),y,c=COLORS[0],marker='o');ax.set_xticks(np.arange(len(y)),frame['arm'].astype(str),rotation=65,ha='right',fontsize=7);ax.set_ylabel(metric);ax.set_title('Frozen DevCal Joint grid: development sensitivity only')
        export(fig,out/('DEV_'+metric),dict(source_csv=str(path),source_sha256=sha(path),source_stage='E0/E5',independent_unit='development centers; no new Final tuning',centers=8,seeds=[7311],metric=metric,interval='none',negative_results_retained=True))
    stream_path=ROOT/'E0_MAIN_TABLES/DEVCAL_JOINT_RESULTS_BY_STREAM.csv';data=pd.read_csv(stream_path)
    for metric in [c for c in ('service_mse','harmful_frequency','mean_downside','commit_rate')if c in data]:
        pivot=data.pivot(index='arm',columns='stream',values=metric);fig,ax=plt.subplots(figsize=(6,6),layout='constrained');im=ax.imshow(pivot.to_numpy(),aspect='auto',cmap='viridis');fig.colorbar(im,ax=ax,label=metric);ax.set_xticks(range(len(pivot.columns)),pivot.columns,rotation=25,ha='right');ax.set_yticks(range(len(pivot.index)),pivot.index,fontsize=7);ax.set_title('Frozen development sensitivity / all streams')
        export(fig,out/('DEV_HEAT_'+metric),dict(source_csv=str(stream_path),source_sha256=sha(stream_path),source_stage='E0/E5',independent_unit='development centers',centers=8,seeds=[7311],metric=metric,interval='none',negative_results_retained=True))

def main(group):
    out=STORAGE/'figures'/group;out.mkdir(parents=True,exist_ok=True)
    if group=='E5_COST':
        tables=[pd.read_csv(p)for p in (STORAGE/'statistics').glob('E5_COST_*/UNIFIED_COST.csv')]
        if not tables:raise RuntimeError('No verified unified cost records')
        data=pd.concat(tables,ignore_index=True);source=out/'ALL_REPEATED_COST.csv';data.to_csv(source,index=False);atomic(out/'COST_PROFILE.json',json.loads(json.dumps(profile_data(str(source),group_cols=['arm','repetition']),default=str)))
        for metric in ('maintenance_common_seconds','training_seconds','verification_and_gate_seconds','model_persistence_seconds','postseal_service_evaluation_and_result_persistence_seconds'):
            means=data.groupby(['arm','repetition'])[metric].mean().reset_index();arms=sorted(means.arm.unique());fig,ax=plt.subplots(figsize=(7.2,5),layout='constrained')
            for i,arm in enumerate(arms):
                z=means[means.arm==arm];ax.scatter(z[metric],np.repeat(i,len(z)),s=25,color=COLORS[0],marker='o')
            ax.set_yticks(range(len(arms)),arms);ax.invert_yaxis();ax.set_xlabel('Seconds / stage (mean within each timing repetition)');ax.set_title(metric+'\nThree timing replicas; no scientific population CI')
            export(fig,out/metric,dict(source_csv=str(source),source_sha256=sha(source),source_stage='E5',independent_unit='timing repetition only; same deterministic input, not new scientific sample',metric=metric,interval='none',host_scope='other host applications can compete; not energy or complexity guarantee'))
    elif group=='E0':
        old=pd.read_csv(ROOT/'E0_MAIN_TABLES/RESULTS_BY_CENTER.csv');old=old.rename(columns={'balanced_clean_mixed_mse':'mse','harmful_frequency':'harm_frequency'});old['stream']='MAIN_EQUAL_PROTOCOL_CONDITIONS';old['beneficial_recall']=np.nan;target=out/'MAIN_CENTER_PLOT_DATA.csv';old.to_csv(target,index=False)
        distribution(target,out,group,dict(source_stage='passed Main / read only E0',metric_scope='MSE balanced clean/mixed; harm/downside/commit across all three original streams; not a same-condition frontier',independent_centers=32,seeds=[7311,7312,7313],limitations='Main primary comparison selection and unadjusted multiple comparisons remain'));sensitivity(out)
    else:
        spec=read(ROOT/'registered_groups'/f'{group}.json');path=STORAGE/'statistics'/group/'CENTERS.csv'
        if not path.exists():return
        distribution(path,out,group,dict(source_stage=spec['stage'],registered_independent_units=len(spec['centers'])if spec['domain']in('synthetic','alibaba')else 1,seeds=spec['seeds'],limits=spec.get('cost_scope','temperature houses not seeds/rooms as independent populations; all supplementary CIs exploratory')))
    atomic(out/'FIGURE_RECEIPT.json',dict(status='MACHINE_RENDERED_DRAFTS',visual_review='PENDING',publication_ready=False,files=[str(p)for p in out.glob('*.png')],at_unix=time.time()))
if __name__=='__main__':main(sys.argv[1])
