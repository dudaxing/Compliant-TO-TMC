"""Plot immutable S0 file/ZIP quantities; this is not a mechanics calculation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'build_receipt.json').read_text())
plan=json.loads((HERE/'migration_candidate.json').read_text())
labels={'c0_runs':'C0 runs','c1_runs':'C1 runs','c2_runs':'C2 runs',
        'c2_readback_details':'C2 readback details','historical_repair_details':'HF4 repair details',
        'historical_hf4_details':'HF4 earlier details'}
groups=sorted(data['groups'],key=lambda x:x['first_copy']['verified_uncompressed_bytes'],reverse=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,(left,right)=plt.subplots(1,2,figsize=(12,5.4),gridspec_kw={'width_ratios':[1,1.8]})
values=[plan['tracked_baseline_bytes']/1e6,plan['retained_old_file_bytes_before_new_indexes']/1e6]
left.barh([1,0],values,color=['#62748a','#137f80'],height=.48)
left.set_yticks([1,0],['Original tree','Retained original files'])
left.set_xlim(0,1500);left.set_xlabel('MB (1,000,000 bytes)')
for y,v in zip([1,0],values):left.text(v+22,y,f'{v:,.2f}',va='center',fontsize=11)
left.set_title('89.88% of original payload externalized',loc='left',pad=18,fontsize=11)
fig.text(.15,.12,'New tools, indexes and reports add overhead.\nThis is not a Git-history size reduction.',fontsize=9,color='#475569')
y=np.arange(len(groups))
raw=[g['first_copy']['verified_uncompressed_bytes']/1e6 for g in groups]
compressed=[g['first_copy']['bytes']/1e6 for g in groups]
right.barh(y-.17,raw,height=.29,color='#62748a',label='Original file bytes')
right.barh(y+.17,compressed,height=.29,color='#137f80',label='Lossless ZIP bytes')
right.set_yticks(y,[labels[g['group']] for g in groups]);right.invert_yaxis()
right.set_xlabel('MB (1,000,000 bytes)');right.set_xlim(0,max(raw)*1.2)
right.set_title('Six archives: 358.12 MB per verified copy',loc='left',pad=18,fontsize=11)
for ypos,v in zip(y+.17,compressed):right.text(v+3,ypos,f'{v:.2f}',va='center',fontsize=8)
right.legend(frameon=False,loc='lower right')
fig.suptitle('HF4-C2-S0 | storage changes; scientific states unchanged',x=.04,ha='left',fontsize=15,fontweight='bold')
fig.text(.04,.03,'1,099 files retained byte for byte. Two copies and empty-directory restoration verified. C2 remains 58/59 states passed.',fontsize=9,color='#475569')
fig.tight_layout(rect=(0,.20,1,.93),w_pad=3)
fig.savefig(HERE/'storage_layout.png',dpi=160,bbox_inches='tight')
fig.savefig(HERE/'storage_layout.svg',bbox_inches='tight',metadata={'Date':None})
svg=HERE/'storage_layout.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
