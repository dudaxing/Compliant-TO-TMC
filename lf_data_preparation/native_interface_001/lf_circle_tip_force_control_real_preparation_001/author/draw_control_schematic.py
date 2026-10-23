"""Preparation schematic only: no FE shapes, scientific arrays or solver calls."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE=Path(__file__).resolve().parent
source=json.loads((HERE/'SOURCE_BINDING.json').read_bytes())
loads=source['reference_binding']['load_candidates_half_N']
fig=plt.figure(figsize=(15,8),facecolor='white')
ax=fig.add_axes([.02,.04,.96,.88]); ax.set_xlim(0,15); ax.set_ylim(0,8); ax.axis('off')
blue='#24678c'; orange='#b65b28'; green='#386b50'; ink='#243440'
fig.suptitle('Formal r9 force-control cross-check | PREPARATION ONLY',fontsize=21,color=ink,y=.98)
ax.text(7.5,7.75,'Control schematic, not FE geometry. No new force-controlled r9 solution.',ha='center',fontsize=12,color='#576775')
def box(x,y,w,h,text,color=blue,fs=12):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.10',facecolor='#f4f7f9',edgecolor=color,linewidth=1.5))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,color=ink,linespacing=1.65)
def arrow(x0,y0,x1,y1,color=blue):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=15,color=color,linewidth=1.7))
box(.3,5.05,3.45,1.9,'Existing LOW1 fixed parent\n0 -> 0.25 -> 0.50 mm\nChoose state index 2\nOriginal split + signed R')
arrow(3.95,6.0,4.55,6.0)
box(4.7,5.05,3.9,1.9,'Fresh anchor at q = 0\nP0 = 3.68642113e-5 N\nNew F/T; check 1 must pass\nNo projection / repair',green)
arrow(8.8,6.0,9.4,6.0,orange)
box(9.55,5.05,4.75,1.9,'Only prescribe axial force P1\nP1 = 4.32723069e-5 N\nSolve unknown w, q and R\nInput mean held at 0.50 mm',orange)
ax.add_patch(Circle((10.6,3.72),.55,facecolor='#f4d4ae',edgecolor=orange,linewidth=2))
arrow(11.2,3.72,12.9,3.72,orange)
ax.text(12.05,4.1,'P along +x',ha='center',color=orange,fontsize=13)
ax.text(10.6,2.87,'Rigid guided body: uy = 0, rotation = 0',ha='center',fontsize=12,color=ink)
ax.text(10.6,3.72,'q = ?',ha='center',va='center',fontsize=17,color=orange)
box(.3,2.85,7.55,1.35,'Half-model N already includes 20 mm thickness\nKeep r9 / center(80,40) / right92 / Lr80 / alpha2.5e-7\nNo body remask; total force retains material + Hu',blue,11.5)
arrow(11.8,2.6,11.8,2.05,orange)
box(.3,.3,7.55,1.6,'Success gates on every accepted state\nFree and body-load residuals <= 1e-9; original mean gate\nJ > 0; global <= 1e-6; rigid/zero <= 8e-11 mm',green,11.5)
box(8.25,.3,6.05,1.6,'Then compare to existing given-q reference\nq = 0.025 mm is NOT an input to the new solve\nq / field difference <= 1e-6 mm; separate R gate',orange,11.5)
fig.savefig(HERE/'control_schematic.png',dpi=150)
fig.savefig(HERE/'control_schematic.svg')
plt.close(fig)
(HERE/'SCHEMATIC_RENDER.json').write_text(json.dumps(dict(stage='L-CTIPFREALPREP1',
    status='schematic_rendered_pending_QA',new_png=1,new_svg=1,not_FE_geometry=True,
    scientific_arrays_read=0,HF_imports=0,force_calls=0,tangent_calls=0,solver_calls=0,
    HP_calls=0,source='SOURCE_BINDING.json; existing ordinary metadata only'),indent=2)+'\n',encoding='utf-8')
