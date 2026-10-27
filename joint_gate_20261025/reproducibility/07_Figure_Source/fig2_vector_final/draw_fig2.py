"""Author-confirmed layout, rebuilt exclusively from editable vector objects.

Run with Python + matplotlib + PyMuPDF + Pillow. No images are imported.
Coordinates are final-size points: 468 pt = 165.1 mm. All type is >= 8 pt.
The tiny bars/dots/curves are conceptual, never experimental observations.
"""
from pathlib import Path
import json, hashlib, math, platform
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, patches
from matplotlib.path import Path as MPath
import fitz
from PIL import Image, ImageOps

OUT=Path(__file__).resolve().parent
W,H=468,278
BLUE='#1268B9'; ORANGE='#D97316'; GREEN='#26823D'; GREY='#657684'; INK='#152C3A'
plt.rcParams.update({'font.family':'Arial','font.size':8.2,'text.color':'black',
 'mathtext.fontset':'custom','mathtext.rm':'Arial','mathtext.it':'Arial:italic',
 'mathtext.bf':'Arial:bold','pdf.fonttype':42,'svg.fonttype':'none',
 'svg.hashsalt':'RAVM-FIG2-CONFIRMED-VECTOR-20261025'})
fig=plt.figure(figsize=(W/72,H/72),facecolor='white')
ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,W),ylim=(0,H));ax.axis('off')
texts=[];edges=[];nodes={}
def text(x,y,s,size=8.2,bold=False,ha='center',**kw):
    t=ax.text(x,y,s,fontsize=size,fontweight='bold'if bold else'normal',ha=ha,
      va='center',linespacing=1.03,**kw);texts.append(t);return t
def box(x,y,w,h,color=GREY,fill='white',lw=.65,r=3,node=None):
    a=patches.FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',
      fc=fill,ec=color,lw=lw);ax.add_patch(a)
    if node:nodes[node]={'rect':[x,y,w,h]}
    return a
def arrow(points,source,target,role='current',color=INK,lw=.72,dashed=False):
    path=MPath(points,[MPath.MOVETO]+[MPath.LINETO]*(len(points)-1))
    ax.add_patch(patches.FancyArrowPatch(path=path,arrowstyle='-|>',mutation_scale=6.2,
      color=color,lw=lw,linestyle=(0,(3,2))if dashed else'-',zorder=2))
    edges.append({'source':source,'target':target,'time_role':role,'points':points,
      'dashed':dashed})
def line(points,color=INK,lw=.65):
    ax.plot([p[0]for p in points],[p[1]for p in points],c=color,lw=lw)
def net(cx,cy,r=7,color=BLUE):
    pts=[(cx+r*math.cos(math.pi/3*i),cy+r*math.sin(math.pi/3*i))for i in range(6)]+[(cx,cy)]
    for i in range(6):
        for j in [(i+1)%6,6]:line([pts[i],pts[j]],color,.7)
    for i,(x,y)in enumerate(pts):ax.add_patch(patches.Circle((x,y),r*.20,fc='white'if i==6 else color,ec=color,lw=.6))
def series(x,y,w,h,color):
    line([(x,y+h),(x,y),(x+w,y)],INK,.55)
    vals=[.16,.32,.25,.48,.39,.58,.74,.46,.32,.53,.76,.63,.87]
    line([(x+2+(w-4)*i/(len(vals)-1),y+1+(h-2)*v)for i,v in enumerate(vals)],color,.9)
def bars(x,y,w=41,h=15):
    line([(x,y+h),(x,y),(x+w,y)],INK,.5)
    for xx,hh,c in [(x+10,h*.8,BLUE),(x+29,h*.51,ORANGE)]:
        ax.add_patch(patches.Rectangle((xx-4,y),8,hh,ec=c,fc=c,lw=.5))
        line([(xx,y+hh-2),(xx,y+hh+2)],INK,.55);line([(xx-1.4,y+hh+2),(xx+1.4,y+hh+2)],INK,.5)
    text(x+10,y-5,r'$P$',8);text(x+29,y-5,r'$Q$',8)
def dots(x,y,w=41,h=15):
    line([(x,y+h),(x,y),(x+w,y)],INK,.5)
    for xx,c,offset in [(x+10,BLUE,2),(x+30,ORANGE,0)]:
        for dx,dy in [(0,0),(-2.6,3),(2.6,3),(0,6),(-2.6,9),(2.6,9),(0,12)]:
            ax.add_patch(patches.Circle((xx+dx,y+1+dy*.85+offset*.3),1.1,fc=c,ec=c,lw=.3))
    text(x+10,y-5,r'$P$',8);text(x+30,y-5,r'$Q$',8)

# Top row preserves the author's three-column arrangement.
box(8,222,135,48,BLUE,'#E9F4FF',node='parent_header')
text(75.5,260,'Deployed parent',9.4,True)
net(43,240,8,BLUE);text(88,244,'Current state',8.1);text(88,232,r'$f_{t-1}$',10)
box(149,222,155,48,BLUE,'#EFF7FD',node='maintenance_data')
text(226.5,260,'Maintenance data',9.4,True)
box(155,227,67,24,'#9EBED4',r=2,node='update_header')
box(231,227,67,24,'#9EBED4',r=2,node='verification_header')
text(188.5,245,'Update '+r'$U_t$',8.1);series(161,230,54,10,BLUE)
text(264.5,245,'Verification '+r'$V_t$',8.1);series(237,230,54,10,ORANGE)
box(310,222,150,48,GREY,'#F8F9FA',node='legend')
text(385,260,'Model states (legend)',9.0,True)
for x,c,title,symbol in [(335,BLUE,'Parent',r'$f_{t-1}$'),(385,ORANGE,'Candidate',r'$\widetilde f_t$'),(435,GREEN,'Deployed',r'$f_t$')]:
    net(x,248,5.4,c);text(x,237,title,8.0,True);text(x,227.5,symbol,8.5)

# Three panels: no imported bitmap, no repeated evidence cards in panel 3.
for x,w,c,fill,n,title in [(8,135,BLUE,'#E9F4FF','1','Candidate adaptation'),
 (151,153,ORANGE,'#FFF3E1','2','Current verification'),
 (310,150,GREEN,'#E9F8EB','3','Joint Gate & deployment')]:
    box(x,56,w,158,c,fill,lw=.75,r=4)
    ax.add_patch(patches.Circle((x+10,204),6.4,fc=c,ec=c,lw=.5))
    text(x+10,204,n,9.3,True,color='white');text(x+w/2+8,204,title,8.5,True)

# Candidate adaptation starts with a COPY. Parent remains available to verify.
box(16,155,55,36,BLUE,node='parent')
text(43.5,183,'Parent',8.4,True);net(32,169,6,BLUE);text(53,169,r'$f_{t-1}$',9)
box(79,155,55,36,BLUE,node='update')
text(106.5,182,'Update',8.4,True);text(106.5,168,r'$U_t$',10)
arrow([(43,222),(43,218),(10,218),(10,174),(16,174)],'parent_header','parent',color=BLUE)
arrow([(188,227),(188,218),(141,218),(141,181),(134,181)],'update_header','update',color=BLUE)
box(38,119,79,26,BLUE,node='adaptation')
text(77.5,136,'Copy + 50-step',8.5,True);text(77.5,125,'SGD',8.5,True)
arrow([(43.5,155),(43.5,150),(77.5,150),(77.5,145)],'parent','adaptation',color=BLUE)
arrow([(106.5,155),(106.5,150),(77.5,150)],'update','adaptation',color=BLUE)
box(38,76,79,28,ORANGE,node='candidate')
net(51,90,7,ORANGE);text(91,97,'Candidate',8.3,True);text(91,84,r'$\widetilde f_t$',10)
arrow([(77.5,119),(77.5,104)],'adaptation','candidate',color=ORANGE)

# Both model identities and V_t enter ONE loss evaluation node.
box(159,182,137,14,ORANGE,node='verification')
text(227.5,189,'Current Verification '+r'$V_t$',8.3,True)
arrow([(266,227),(302,227),(302,189),(296,189)],'verification_header','verification',color=ORANGE)
box(159,136,137,38,ORANGE,node='loss_evaluation')
text(227.5,165,'Loss evaluation on the same '+r'$V_t$',8.0,True)
net(174,148,5.5,BLUE);text(197,148,r'$f_{t-1}$',9)
net(247,148,5.5,ORANGE);text(272,148,r'$\widetilde f_t$',9)
arrow([(43.5,191),(43.5,196),(147,196),(147,160),(159,160)],'parent','loss_evaluation',color=BLUE)
arrow([(117,90),(147,90),(147,146),(159,146)],'candidate','loss_evaluation',color=ORANGE)
arrow([(227.5,182),(227.5,174)],'verification','loss_evaluation',color=ORANGE)
box(159,115,137,14,ORANGE,node='loss_samples')
text(227.5,122,'Loss samples  '+r'$\ell^{P},\ \ell^{Q}$',8.4)
arrow([(227.5,136),(227.5,129)],'loss_evaluation','loss_samples',color=ORANGE)
box(159,63,65,40,ORANGE,node='mean')
box(231,63,65,40,ORANGE,node='rank')
text(191.5,97,'Mean '+r'$(d_t,s_t)$',8.1,True)
text(263.5,97,'Rank/MWU '+r'$(p_t)$',8.0,True)
bars(169,73);dots(240,73)
arrow([(227.5,115),(227.5,109),(191.5,109),(191.5,103)],'loss_samples','mean',color=ORANGE)
arrow([(227.5,109),(263.5,109),(263.5,103)],'loss_samples','rank',color=ORANGE)
# Explicit junction bundles both outputs; neither bypasses the score.
nodes['evidence_tuple']={'point':[227.5,59]}
arrow([(191.5,63),(191.5,59),(227.5,59)],'mean','evidence_tuple',color=ORANGE)
arrow([(263.5,63),(263.5,59),(227.5,59)],'rank','evidence_tuple',color=ORANGE)
ax.add_patch(patches.Circle((227.5,59),1.2,fc=ORANGE,ec=ORANGE,lw=.3))

# A single score and a single joint decision. Green denotes state, not safety.
box(319,156,132,32,GREEN,'#F6FBFF',node='score')
text(385,181,'Joint score',8.7,True)
text(385,167,r'$J_t=d_t+\lambda s_t(p_t-0.2)$',9.1)
arrow([(227.5,59),(306,59),(306,191),(385,191),(385,188)],'evidence_tuple','score',color=ORANGE)
nodes['decision']={'polygon':[[385,147],[451,129],[385,111],[319,129]]}
ax.add_patch(patches.Polygon(nodes['decision']['polygon'],fc='#FFF6D9',ec=GREEN,lw=.75))
text(385,135.5,r'$d_t<0$ AND',8.5);text(385,123,r'$J_t\leq-\delta\ ?$',9.1)
arrow([(385,156),(385,147)],'score','decision',color=GREEN)
box(316,80,62,20,ORANGE,node='commit');net(327,90,5,ORANGE)
text(355,94,'Commit',8.2,True);text(355,84,r'$\widetilde f_t$',8.5)
box(392,80,63,20,BLUE,node='retain');net(403,90,5,BLUE)
text(431,94,'Retain',8.2,True);text(431,84,r'$f_{t-1}$',8.5)
text(336,108,'YES',8.0,True);text(433,108,'NO',8.0,True)
arrow([(319,129),(314,129),(314,103),(347,103),(347,100)],'decision','commit',color=GREEN)
arrow([(451,129),(456,129),(456,103),(424,103),(424,100)],'decision','retain',color=GREEN)
box(343,57,87,14,GREEN,node='deployed')
net(353,64,4.5,GREEN);text(397,64,'Next state '+r'$f_t$',8.3,True)
arrow([(347,80),(347,76),(369,76),(369,71)],'commit','deployed',color=GREEN)
arrow([(424,80),(424,76),(410,76),(410,71)],'retain','deployed',color=GREEN)

# Bottom strip: no duplicate deployed-state box and no current-gate feedback.
box(8,12,452,36,GREY,'#F2F4F6',node='audit_strip')
text(234,43,'Future Service and retrospective audit',8.5,True)
box(17,17,97,21,'#9AAEBE',node='service')
series(23,21,22,12,GREY);text(80,32,'Future Service',8.0,True);text(80,22,r'$S_t$',8.7)
box(129,17,110,21,'#9AAEBE',node='audit')
text(184,32,'Retrospective audit',8.1,True);text(184,22,'Sealed P/Q/action IDs',8.0)
box(254,17,197,21,'#9AAEBE',node='audit_metrics')
text(289,32,'Lifecycle',8.0,True);text(289,22,'MSE',8.0,True)
text(355,32,'Harmful',8.0,True);text(355,22,'commitment',8.0,True)
text(420,27,'Downside',8.0,True)
arrow([(386,57),(386,52),(65,52),(65,38)],'deployed','service','future_after_seal',color=GREY)
arrow([(114,27.5),(129,27.5)],'service','audit','retrospective',color=GREY)
arrow([(239,27.5),(254,27.5)],'audit','audit_metrics','retrospective',color=GREY)
arrow([(430,64),(465,64),(465,6),(2,6),(2,240),(8,240)],'deployed','parent_header','next_stage',color=INK,dashed=True)
text(234,6,'Next maintenance stage '+r'$(t+1)$',8.0,
 bbox={'facecolor':'white','edgecolor':'none','pad':1.2})

fig.canvas.draw();ren=fig.canvas.get_renderer()
outside=[]
for t in texts:
    b=t.get_window_extent(ren).transformed(ax.transData.inverted())
    if b.x0<0 or b.x1>W or b.y0<0 or b.y1>H:outside.append(t.get_text())
assert not outside,outside
assert min(t.get_fontsize()for t in texts)>=8
pdf=OUT/'fig2_joint_gate_final.pdf';svg=OUT/'fig2_joint_gate_final.svg'
fig.savefig(pdf,metadata={'Title':'RAVM-DT Joint Gate: current Verification and sealed Service',
 'Author':'RAVM-DT authors','Creator':'Matplotlib '+matplotlib.__version__})
fig.savefig(svg);fig.savefig(OUT/'fig2_preview_300dpi.png',dpi=300)
doc=fitz.open(pdf);p=doc[0]
pix=p.get_pixmap(dpi=1200,alpha=False)
im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
im.save(OUT/'fig2_joint_gate_final.tiff',compression='tiff_lzw',dpi=(1200,1200))
pix=p.get_pixmap(dpi=180,alpha=False);preview=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
preview.save(OUT/'fig2_final_size_review.png');ImageOps.grayscale(preview).save(OUT/'fig2_grayscale_review.png')
(OUT/'FIG2_CONNECTIONS.json').write_text(json.dumps({'nodes':nodes,'edges':edges,
 'labels':[{'text':t.get_text(),'fontsize_pt':t.get_fontsize(),
 'bounds_pt':list(t.get_window_extent(ren).transformed(ax.transData.inverted()).bounds)}for t in texts],
 'loss_roles':{'mean':'paired differences of losses in the same current windows',
 'rank':'one-sided MWU comparing two loss samples; not a paired-difference test'},
 'sealed_ids':'parent P, candidate Q and deployment action are sealed before Service access',
 'matured_data':'only protocol-eligible matured data may enter a later Update; no Service-to-current-gate edge'},indent=2),'utf8')
receipt={'status':'EXPORTED_PENDING_ACTUAL_VISUAL_REVIEW','width_pt':W,'height_pt':H,
 'width_mm':W/72*25.4,'height_mm':H/72*25.4,'font_min_pt':min(t.get_fontsize()for t in texts),
 'native_image_objects':len(p.get_images()),'vector_drawings':len(p.get_drawings()),
 'text_characters':len(p.get_text()),'label_count':len(texts),'edges':len(edges),
 'tiff_pixels':[im.width,im.height],'tiff_dpi':1200,'tiff_mode':im.mode,
 'python':platform.python_version(),'matplotlib':matplotlib.__version__,
 'all_labels_in_canvas':True,'no_raster_input':True,'new_training_steps':0,
 'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in [pdf,svg,OUT/'fig2_joint_gate_final.tiff',Path(__file__)]}}
assert receipt['native_image_objects']==0
(OUT/'FIG2_EXPORT_RECEIPT.json').write_text(json.dumps(receipt,indent=2),'utf8')
print(json.dumps(receipt),flush=True)
