"""One small-model figure from new ordinary JSON only; no HF/NPZ imports."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

BASE=Path(__file__).resolve().parent
RUN=BASE/'run_001'

def read(path):
    return json.loads(Path(path).read_bytes())

def identity(path):
    raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def main():
    started=time.monotonic()
    summary_file=RUN/'artifacts/validation_summary.json'
    summary=read(summary_file)
    force_file=Path(summary['force_result_file'])
    reference_file=Path(summary['probe_result_file'])
    for p in (force_file,reference_file):
        if not p.resolve().is_relative_to(RUN.resolve()):
            raise ValueError('Viewer reads only this new run')
    force,reference=read(force_file),read(reference_file)
    if force['status']!='success' or not summary['all_eight_new_methods_passed']:
        raise ValueError('Display requires successful new finite validation')
    rows=force['accepted_steps']
    refs=[r for r in reference['accepted_steps'] if r['is_original_target']]
    pairs=summary['cross_checks']
    coords=np.asarray(force['model']['coordinates_mm'])
    cells=np.asarray(force['model']['connectivity'],dtype=int)
    solid=np.asarray(force['model']['solid'],dtype=bool)
    body=np.asarray(force['model']['body_nodes'],dtype=int)
    actual=np.asarray(rows[-1]['positions_mm'])
    held=force['force_task']['held_input_mean_mm']
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,
                         'figure.facecolor':'white','axes.grid':True,'grid.alpha':.2})
    fig,axes=plt.subplots(2,3,figsize=(18,10.5),layout='constrained')
    ax=axes[0,0]
    colors=np.where(solid,'#809eae','#e4edf1').tolist()
    body_cells=np.all(np.isin(cells,body),axis=1)
    for i in np.flatnonzero(body_cells):
        colors[i]='#eab570'
    ax.add_collection(PolyCollection(actual[cells],facecolors=colors,edgecolors='#536777',linewidths=.65))
    ax.add_collection(PolyCollection(coords[cells],facecolors='none',edgecolors='#81909a',
                                     linewidths=.5,linestyles='dotted'))
    displacement=actual-coords
    ax.quiver(coords[:,0],coords[:,1],200*displacement[:,0],200*displacement[:,1],
        angles='xy',scale_units='xy',scale=1.,color='#c24f30',width=.004)
    ax.set(xlim=(-.1,2.2),ylim=(-.1,2.2),xlabel='x (mm)',ylabel='y (mm)',
        title='Actual geometry x1; displacement arrows x200')
    ax.set_aspect('equal',adjustable='box')
    ax.text(.02,.98,f'16 cells / 50 field DOF; thickness 2 mm\n'
        f'Input mean held {held:.7g} mm\nUnknown final q = {rows[-1]["body_q_mm"]:.10g} mm',
        transform=ax.transAxes,va='top',fontsize=9,
        bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))

    ax=axes[0,1]
    ax.plot([r['body_q_mm']*1e3 for r in refs],[r['Q_drive_half_N']*1e6 for r in refs],
        '--s',color='#487d98',label='Given q: measured Q (reference)',mfc='none')
    ax.plot([r['body_q_mm']*1e3 for r in rows],[r['P_target_half_N']*1e6 for r in rows],
        'o',color='#b9472e',label='Given P: independently solved q',ms=6)
    ax.set(xlabel='Body q (micrometres)',ylabel='Signed half-model P or Q (microN)',
           title='Force-control / displacement-control cross-check')
    ax.legend(fontsize=8)

    ax=axes[0,2]
    x=np.arange(len(pairs))
    ax.bar(x-.17,[r['q_abs_error_mm']*1e6 for r in pairs],width=.34,
           color='#487d98',label='q difference')
    ax.bar(x+.17,[r['physical_displacement_max_error_mm']*1e6 for r in pairs],width=.34,
           color='#d89c4a',label='Maximum field displacement difference')
    ax.axhline(1e-2,color='#a3322b',ls='--',label='Declared 1e-8 mm bound')
    ax.set(xticks=x,xticklabels=[f'Target {i}' for i in x],ylabel='Absolute difference (nm)',
           title='Same absolute load; reference q never prescribed')
    ax.legend(fontsize=8)

    ax=axes[1,0]
    P=np.asarray([r['P_target_half_N'] for r in rows])
    Q=np.asarray([r['generalized_body_internal_force_half_N'] for r in rows])
    material=np.asarray([-r['force_on_body_N']['material'][0] for r in rows])
    hu=np.asarray([-r['force_on_body_N']['regularization'][0] for r in rows])
    ax.plot(P*1e6,Q*1e6,'o-',label='Internal generalized total Q')
    ax.plot(P*1e6,material*1e6,'s--',label='Material part')
    ax.plot(P*1e6,hu*1e6,'^--',label='Hu part')
    ax.set(xlabel='Applied signed P_half (microN)',ylabel='Signed internal component (microN)',
           title='Nonzero preload and total-force components')
    ax.legend(fontsize=8)
    ax2=ax.twinx()
    ax2.plot(P*1e6,[r['R_input_N'] for r in rows],'x:',color='#635387')
    ax2.set_ylabel('Input actuator R (N)',color='#635387')
    ax2.grid(False)

    ax=axes[1,1]
    history=force['newton_history']
    index=np.arange(1,len(history)+1)
    floor=1e-18
    for key,label,style in (('relative_residual','Free-force residual','o-'),
                           ('relative_generalized_force_residual','Body-load residual','s--')):
        ax.semilogy(index,[(float(r[key]) if float(r[key]) > 0 else floor) for r in history],style,label=label,ms=4)
    ax.axhline(1e-9,color='#a3322b',ls=':',label='Both acceptance bounds')
    ax.set(xlabel='Actual force-path Newton base check',ylabel='Separate dimensionless residuals',
           title='All actual force-path base checks; zeros shown at 1e-18')
    ax.legend(fontsize=8)

    ax=axes[1,2]
    ax.plot(P*1e6,[r['minimum_J'] for r in rows],'o-',color='#487d98',label='Minimum J')
    ax.set(xlabel='Applied signed P_half (microN)',ylabel='Minimum J (positive)',
           title='Actual medium deformation and curvature')
    ax2=ax.twinx()
    ax2.plot(P*1e6,[r['max_abs_Hu_per_mm'] for r in rows],'^--',color='#b9472e')
    ax2.set_ylabel('Maximum |Hu| (1/mm)',color='#b9472e')
    ax2.grid(False)
    ax.text(.02,.02,f'Force accepted states: {len(rows)}\n'
        f'Max rigid/zero error: {max(r["max_abs_prescribed_error_mm"] for r in rows):.3g} mm\n'
        f'Max relative global balance: {max(r["relative_global_force_balance"] for r in rows):.3g}',
        transform=ax.transAxes,fontsize=8,va='bottom',
        bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
    fig.suptitle('L-CTIPFLOAD1 | New small-model guided axial force control\n'
        'Signed half-model N includes 2 mm thickness; q is unknown. Not a full-size gripper capacity test.',fontsize=15)
    view=RUN/'view'
    view.mkdir(exist_ok=False)
    png=view/'force_control.png'
    fig.savefig(png,dpi=120)
    plt.close(fig)
    receipt=dict(stage='L-CTIPFLOAD1',status='rendered_pending_root_visual_check',
        new_png_count=1,scientific_calls=0,NPZ_fields_decoded=0,old_media_reads=0,
        source_json_files=[identity(p) for p in (summary_file,force_file,reference_file)],
        image=identity(png),accepted_force_states=len(rows),actual_geometry_scale=1,
        displacement_arrow_scale=200,elapsed_seconds=time.monotonic()-started,
        created_utc=datetime.now(timezone.utc).isoformat())
    with (view/'renderer_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'],image=str(png))),flush=True)

if __name__=='__main__':
    main()
