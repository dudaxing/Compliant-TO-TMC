"""Plot saved validation records only; never call a mechanics implementation."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path, bindings):
    bindings[str(path.resolve())] = sha(path)
    return json.loads(path.read_text(encoding='utf-8'))


def ratio(check):
    return float(Decimal(check['value']) / Decimal(check['limit']))


def save(fig, out, name):
    for suffix in ('png', 'svg'):
        fig.savefig(out/(name+'.'+suffix), dpi=170, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manufactured', type=Path, required=True)
    parser.add_argument('--saved', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False,
                         'axes.spines.right':False, 'svg.hashsalt':'c2-stable-f-validation'})
    bindings = {}
    read(args.manufactured/'summary.json', bindings)
    read(args.saved/'summary.json', bindings)
    fields = [read(path, bindings) for path in sorted(args.manufactured.glob('*/result.json'))]
    states = [read(path, bindings) for path in sorted(args.saved.glob('*/result.json'))]
    if fields:
        fig, axes = plt.subplots(1, 2, figsize=(12, max(7, len(fields)*.25)), sharey=True)
        y = np.arange(len(fields))
        for ax, family in zip(axes, ('force', 'tangent')):
            values = []
            for field in fields:
                checks = [c for direction in field['directions'] for c in direction['checks']
                          if ((c['name'].startswith(('candidate_', 'force_only_')) and family in c['name'])
                              or (family == 'tangent' and c['name'] in
                                  ('residual_only_jvp_vs_independent', 'returned_Kv_vs_residual_only_jvp')))]
                values.append(max(ratio(c) for c in checks))
            ax.scatter(np.maximum(values, 1e-18), y, c=['#bd3c35' if v>1 else '#245e8d' for v in values], s=25)
            ax.axvline(1, color='#bd3c35', linestyle='--', linewidth=1)
            ax.set_xscale('log'); ax.grid(axis='x', alpha=.18)
            ax.set_title('Full force (both evaluation modes)' if family=='force' else 'Jv (components + consistency)')
            ax.set_xlabel('Maximum error / unchanged gate, across two directions')
        axes[0].set_yticks(y, [f['case'].replace('__', ' / ') for f in fields])
        axes[0].invert_yaxis()
        fig.suptitle('Manufactured fields: values above 1 fail the original gate', y=1.01)
        fig.text(.5, -.015, 'Fixed fields only. No equilibrium solve or path admission. Exact zero plotted at 1e-18.', ha='center', fontsize=9)
        fig.tight_layout()
        save(fig,args.output,'manufactured_gates')
    if states:
        selected = [s for s in states if not s['case'].startswith(('mesh_h00625','outer_free','padding_2p5'))
                    or s['case'] in ('mesh_h00625__019','mesh_h00625__020','outer_free__018','padding_2p5__018')]
        fig, axes = plt.subplots(1, 2, figsize=(12,6), sharey=True)
        for ax, family in zip(axes, ('force','tangent')):
            new = [ratio(next(c for c in s['checks'] if c['name']=='candidate_total_'+family)) for s in selected]
            old = [ratio(next(c for c in s['original_checks'] if c['name']=='production_vs_hp80_total_'+family)) for s in selected]
            y = np.arange(len(selected))
            ax.scatter(np.maximum(old,1e-18), y+.11, marker='x', s=45, c='#b06930', label='Original implementation')
            ax.scatter(np.maximum(new,1e-18), y-.11, s=32, c='#245e8d', label='Candidate, same saved inputs')
            ax.axvline(1,color='#bd3c35',linestyle='--',linewidth=1)
            ax.set_xscale('log'); ax.grid(axis='x',alpha=.18)
            ax.set_title('Total internal force' if family=='force' else 'Total tangent action')
            ax.set_xlabel('Error / unchanged gate'); ax.legend(fontsize=8,loc='best')
        axes[0].set_yticks(np.arange(len(selected)),[s['case'].replace('__',' / ') for s in selected])
        axes[0].invert_yaxis()
        fig.suptitle('Selected saved states: original failure remains in historical evidence')
        fig.text(.5,.015,'This compares candidate evaluations at unchanged states; it does not admit a new equilibrium path.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.04,1,.96))
        save(fig,args.output,'saved_state_comparison')
    curves = []
    for mesh in ('unit','dyadic_rect','nondyadic_rect'):
        path = args.manufactured/(mesh+'__compression_hu')/'fd_0.json'
        if path.exists():
            curves.append((mesh,read(path,bindings)))
    if curves:
        fig, axes = plt.subplots(1,len(curves),figsize=(4*len(curves),4),squeeze=False)
        for ax,(mesh,data) in zip(axes[0],curves):
            steps = [r['step_binary64'] for r in data['rows']]
            for key,label,color in (('ideal_relative_error','Independent Decimal ideal perturbation','#245e8d'),
                                    ('binary_relative_error','Actual binary64 perturbation','#b06930')):
                ax.loglog(steps,np.maximum([float(r[key]) for r in data['rows']],1e-100),'o-',color=color,label=label)
            ax.set_title(mesh); ax.set_xlabel('Step size'); ax.grid(alpha=.2)
        axes[0,0].set_ylabel('Relative difference from independent analytic Jv')
        axes[0,-1].legend(fontsize=7)
        fig.suptitle('Compression + nonzero Hu: all prescribed difference steps retained')
        fig.tight_layout()
        save(fig,args.output,'directional_difference_curves')
    receipt = dict(schema='c2-stable-f-plot-record-v1', scope='Saved record visualization only',
        source_script_sha256=sha(Path(__file__)),input_sha256=bindings,
        output_sha256={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()})
    with (args.output/'plot_receipt.json').open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,indent=2); stream.write('\n')
    print(json.dumps(dict(plots=len(receipt['output_sha256'])//2,output=str(args.output))))


if __name__ == '__main__':
    main()
