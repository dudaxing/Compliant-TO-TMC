"""Render one new small-model figure from one ordinary validation summary.

No HF import, NPZ decoding, old media, new field evaluation or recomputation.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

BASE=Path(__file__).resolve().parent
RUN=BASE/'run_001'

def identity(path):
    raw=path.read_bytes()
    return dict(path=path.as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())

def main():
    started=time.monotonic()
    path=RUN/'artifacts/validation_summary.json'
    s=json.loads(path.read_bytes())
    if (s['schema']!='L-CTIPFRESUME1-small-model-validation-1.0'
            or s['all_twelve_methods_passed'] is not True
            or s['passed_methods']!=[f'V{i:02}' for i in range(1,13)]
            or s['counts']['real_16cell_paths']!=7
            or s['counts']['finite_oracle_injection_rejection_calls']>37):
        raise ValueError('Display requires the actual complete finite validation')
    rows=s['rows']; geom=s['geometry']; hist=s['histories']
    branches=['direct','prefix','child','grandchild']
    colors=dict(direct='#285b7a',prefix='#777777',child='#d07c22',grandchild='#008b80',reference='#8b6094')
    coordinates=np.asarray(geom['coordinates_mm'],float)
    cells=np.asarray(geom['connectivity'],int)
    body=np.asarray(geom['body_nodes'],int)
    solid=np.asarray(geom['solid'],bool)
    if coordinates.shape!=(25,2) or cells.shape!=(16,4):
        raise ValueError('Viewer scope must remain the new 16-cell model')
    direct=rows['direct']; final=rows['grandchild'][-1]
    actual=np.asarray(final['positions_mm'],float)
    rootP=float(direct[0]['P_target_half_N'])
    floor=1e-18
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,
        'axes.grid':True,'grid.alpha':.22,'figure.facecolor':'white'})
    fig,axes=plt.subplots(2,3,figsize=(18,11),layout='constrained')

    ax=axes[0,0]
    faces=np.where(solid,'#819eaf','#e5eef1').tolist()
    for k in np.flatnonzero(np.all(np.isin(cells,body),axis=1)):
        faces[k]='#edbb75'
    ax.add_collection(PolyCollection(actual[cells],facecolors=faces,edgecolors='#496478',linewidths=.7))
    ax.add_collection(PolyCollection(coordinates[cells],facecolors='none',edgecolors='#657780',linewidths=.5,linestyles='dotted'))
    dpos=np.asarray(direct[-1]['positions_mm'],float)
    ax.add_collection(PolyCollection(dpos[cells],facecolors='none',edgecolors=colors['direct'],linewidths=.9,linestyles='dashed'))
    delta=actual-coordinates
    ax.quiver(coordinates[:,0],coordinates[:,1],200*delta[:,0],200*delta[:,1],
        angles='xy',scale_units='xy',scale=1.,color='#ba4937',width=.0035)
    ax.set(xlim=(-.12,2.2),ylim=(-.12,2.2),xlabel='x (mm)',ylabel='y (mm)',
        title='Actual geometry x1; displacement arrows x200')
    ax.set_aspect('equal',adjustable='box')
    ax.text(.02,.98,'16 cells / 50 field DOF / thickness 2 mm\n'
        'Blue dashed: direct; filled: saved grandchild\n'
        f'Final unknown q={final["body_q_mm"]:.11g} mm',
        transform=ax.transAxes,va='top',fontsize=9,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))

    ax=axes[0,1]
    ref=rows['reference']
    ax.plot([r['body_q_mm']*1e3 for r in ref],[r['Q_drive_half_N']*1e9 for r in ref],
        '--s',color=colors['reference'],mfc='none',label='Given-q reference (not an initial guess)')
    for name,marker in zip(branches,['o','x','s','^']):
        rr=rows[name]
        ax.plot([r['body_q_mm']*1e3 for r in rr],[r['P_target_half_N']*1e9 for r in rr],
            marker+'-',color=colors[name],ms=5,mfc='none',label=name)
    ax.set(xlabel='Absolute body q (micrometres)',ylabel='Signed half-model P or Q (nN)',
        title='Same absolute loads; two nonzero saved anchors')
    ax.legend(fontsize=8)
    ax.text(.02,.02,'P increases while remaining negative in this fixture.\n'
        'No reset of q or preload at a segment boundary.',transform=ax.transAxes,fontsize=8)

    ax=axes[0,2]
    for name,marker in zip(branches,['o','x','s','^']):
        rr=rows[name]
        ax.plot([r['P_target_half_N']*1e9 for r in rr],[r['R_input_N']*1e6 for r in rr],
            marker+'-',color=colors[name],ms=5,mfc='none',label=name)
    ax.set(xlabel='Absolute signed P_half (nN)',ylabel='Signed input actuator R (microN)',
        title='R is inherited; it remains distinct from body P')
    ax.legend(fontsize=8)
    ax.text(.02,.02,'Fresh anchors: original split / q / P / R bits, check 1.\n'
        'No projection, repair or second addition of q.',transform=ax.transAxes,fontsize=8)

    ax=axes[1,0]
    pairs=s['comparisons']
    x=np.arange(len(pairs))
    for key,bound,label,color,marker in (
        ('q_abs_error_mm','q_and_state_bound_mm','q error / original bound','#285b7a','o'),
        ('physical_displacement_max_error_mm','q_and_state_bound_mm','all-DOF split error / bound','#d07c22','s'),
        ('R_abs_error_N','R_bound_N','R error / original bound','#008b80','^')):
        values=[max(float(p[key])/float(p[bound]),floor) for p in pairs]
        ax.semilogy(x,values,marker+'-',color=color,label=label,ms=4)
    ax.axhline(1.,ls='--',color='#a12f2f',label='Declared acceptance bound')
    ax.set(xticks=x,xticklabels=[f'{p["branch"][:2]}:{p["original_target_index"]}' for p in pairs],
        xlabel='Paired original target (branch:index)',ylabel='Dimensionless error / frozen bound',
        title='Same-P comparisons; no subtraction of display positions')
    ax.tick_params(axis='x',labelrotation=45,labelsize=8)
    ax.legend(fontsize=8)
    ax.text(.02,.02,'Exact zeros shown at 1e-18; raw JSON unchanged.\n'
        'q / full field bound = 1e-8 mm; R uses its N bound.',transform=ax.transAxes,fontsize=8)

    # The source records both base residuals and Armijo trial merit.  Trial
    # free residuals are not reconstructed from rounded merit values.
    panel=axes[1,1]; panel.axis('off')
    panel.set_title('All force-path base checks and line-search trials')
    ax=panel.inset_axes([.08,.42,.9,.51])
    trial_ax=panel.inset_axes([.08,.035,.9,.22])
    offset=0; trial_offset=0; trial_merit_points=0; trial_undefined_points=0
    for name in branches+['partial']:
        hh=hist[name]['newton_history']; n=len(hh)
        xx=np.arange(offset+1,offset+n+1)
        ax.semilogy(xx,[max(float(r['relative_residual']),floor) for r in hh],
            'o-',color='#285b7a',ms=3,label='free rho_F' if offset==0 else None)
        ax.semilogy(xx,[max(float(r['relative_generalized_force_residual']),floor) for r in hh],
            's--',color='#ba4937',ms=3,label='body rho_P' if offset==0 else None)
        if n:
            ax.text(float(xx.mean()),.97,name[:2].upper(),transform=ax.get_xaxis_transform(),
                ha='center',va='top',fontsize=7)
            ax.axvline(offset+.5,color='#b8c5ce',lw=.5)
        offset+=n
        tt=hist[name]['trials']
        for r in tt:
            trial_offset+=1
            if 'phi' in r and 'base_phi' in r:
                armijo=(1-2e-4*float(r['factor']))*float(r['base_phi'])
                ratio=float(r['phi'])/armijo if armijo>0 else 0.
                trial_ax.semilogy(trial_offset,max(ratio,floor),'o',ms=3,
                    color='#008b80' if r['accepted'] else '#ba4937')
                trial_merit_points+=1
            else:
                trial_undefined_points+=1
                trial_ax.plot(trial_offset,.94,'x',color='#ba4937',ms=5,
                    transform=trial_ax.get_xaxis_transform())
    ax.axhline(1e-9,ls=':',color='#a12f2f',label='both rho bounds')
    ax.set(xlabel='Concatenated actual base check (separate paths)',ylabel='Separate residuals')
    ax.tick_params(labelsize=8); ax.legend(fontsize=7,loc='lower left')
    trial_ax.axhline(1.,ls=':',color='#a12f2f')
    trial_ax.set(xlabel='All actual trial index; green accepted / red rejected',ylabel='phi / Armijo')
    trial_ax.tick_params(labelsize=7)
    if trial_undefined_points:
        trial_ax.text(.02,.95,'Top red x: undefined merit (not a phi value)',
            transform=trial_ax.transAxes,va='top',fontsize=7)

    panel=axes[1,2]; panel.axis('off')
    panel.set_title('Original root scale retained; actual medium response')
    scale_ax=panel.inset_axes([.12,.54,.82,.38])
    for name,marker in zip(branches,['o','x','s','^']):
        rr=rows[name]
        scale_ax.plot([r['P_target_half_N']*1e9 for r in rr],
            [r['generalized_force_scale_half_N']*1e9 for r in rr],marker+'-',
            color=colors[name],mfc='none',ms=4,label=name)
    scale_ax.set(xlabel='Signed P_half (nN)',ylabel='Original SP (nN)')
    scale_ax.tick_params(labelsize=8)
    scale_ax.text(.02,.96,f'root P0={rootP:.10g} N\nSP=max(|P|,|root P0|,Ffloor)',
        va='top',transform=scale_ax.transAxes,fontsize=8)
    scale_ax.legend(fontsize=7,loc='lower left',ncol=2)
    jax=panel.inset_axes([.08,.07,.37,.27]); hax=panel.inset_axes([.60,.07,.37,.27])
    # Plot the direct path and the actual saved chain, preserving every state.
    chain=rows['prefix']+rows['child'][1:]+rows['grandchild'][1:]
    for rr,color,style in ((direct,colors['direct'],'o--'),(chain,colors['grandchild'],'s-')):
        px=[r['P_target_half_N']*1e9 for r in rr]
        jax.plot(px,[r['minimum_J'] for r in rr],style,color=color,ms=3,mfc='none')
        hax.plot(px,[r['max_abs_Hu_per_mm'] for r in rr],style,color=color,ms=3,mfc='none')
    jax.set(xlabel='P_half (nN)',ylabel='min J')
    hax.set(xlabel='P_half (nN)',ylabel='max |Hu| (1/mm)')
    for a in (jax,hax): a.tick_params(labelsize=7)

    fig.suptitle('L-CTIPFRESUME1 | Saved force-state continuation: direct versus two saved segments\n'
        'New small-model validation only. Signed half-model N includes thickness; q remains an unknown.',fontsize=15)
    view=RUN/'view'; view.mkdir(exist_ok=False)
    png=view/'force_resume.png'; fig.savefig(png,dpi=125); plt.close(fig)
    receipt=dict(stage='L-CTIPFRESUME1',status='rendered_pending_root_visual_check',new_png_count=1,
        scientific_calls=0,NPZ_fields_decoded=0,old_media_reads=0,rerenders=0,source_json_files=[identity(path)],
        image=identity(png),actual_geometry_scale=1,displacement_arrow_scale=200,
        plotted_force_branches=branches+['partial'],base_checks_plotted=offset,trials_plotted=trial_offset,
        trial_merit_points=trial_merit_points,trial_undefined_markers=trial_undefined_points,
        elapsed_seconds=time.monotonic()-started,created_utc=datetime.now(timezone.utc).isoformat())
    with (view/'renderer_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=receipt['status'],image=str(png))),flush=True)

if __name__=='__main__':
    main()
