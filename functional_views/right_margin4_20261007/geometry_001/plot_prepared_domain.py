"""Plot the two actual undeformed model packages; no response is evaluated."""
from time import perf_counter
STARTED = perf_counter()
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    args = parser.parse_args()
    root,protocol_file = args.repo.resolve(),args.protocol.resolve()
    stage = protocol_file.parent
    protocol = json.loads(protocol_file.read_text(encoding='utf-8'))
    assert len(protocol['cases']) == 2
    digest = lambda p:sha256(p.read_bytes()).hexdigest()
    assert all(digest(root/name) == pin for name,pin in protocol['bindings'].items())
    output = stage/'view'
    output.mkdir(exist_ok=False)
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    import psutil
    process = psutil.Process()
    peak = 0

    def check():
        nonlocal peak
        peak = max(peak,process.memory_info().rss)
        assert perf_counter()-STARTED <= 60 and peak <= protocol['sampled_RSS_bytes']
        assert not (stage/'stop_requested.txt').exists()

    check()
    fig,axes = plt.subplots(1,2,figsize=(12,6),layout='constrained')
    cases = []
    parent_width = None
    for ax,row in zip(axes,protocol['cases']):
        metadata = json.loads((root/row['model_json']).read_text(encoding='utf-8'))
        assert digest(root/row['model_file']) == metadata['arrays']['sha256']
        with np.load(root/row['model_file'],allow_pickle=False) as model:
            xy = model['coordinates'];conn = model['connectivity']
            width = float(xy[:,0].max())
            assert width == row['expected_width_mm']
            if parent_width is None:parent_width = width
            mirror_y = float(xy[:,1].max())
            assert mirror_y == 40.
            assert len(xy) == metadata['region_metadata']['counts']['nodes']
            assert len(conn) == metadata['region_metadata']['counts']['cells']
            body_nodes = xy[model['workpiece_nodes']]
            body_box = [float(body_nodes[:,0].min()),float(body_nodes[:,0].max()),float(body_nodes[:,1].min()),float(body_nodes[:,1].max())]
            assert body_box == [62.,80.,31.,40.]
            tip_nodes = np.flatnonzero(np.all(xy == [80.,30.],axis=1))
            assert len(tip_nodes) == 1
            tip = int(tip_nodes[0])
            gap = body_box[2]-float(xy[tip,1])
            assert gap == 1.
            margin = width-body_box[1]
            label = f"{row['role']} domain x={width:g} | right margin {margin:g} mm"
            for reflected in (False,True):
                coordinates = xy.copy()
                if reflected:coordinates[:,1] = 2*mirror_y-coordinates[:,1]
                ax.add_collection(PolyCollection(coordinates[conn[model['solid']]],facecolors='#457b9d',edgecolors='none'))
                ax.add_collection(PolyCollection(coordinates[conn[model['workpiece_cells']]],facecolors='#bbbbbb',edgecolors='none'))
            if width > parent_width:
                ax.add_patch(Rectangle((parent_width,0),width-parent_width,2*mirror_y,facecolor='#e6c676',alpha=.35))
            ax.add_patch(Rectangle((0,0),width,2*mirror_y,fill=False,edgecolor='#555555',linewidth=.8))
            ax.axhline(40,color='#888888',linestyle=':',linewidth=.7)
            ax.scatter(80,30,c='#e09113',s=20,zorder=5)
            ax.annotate(f'Initial tip gap {gap:g} mm',xy=(xy[tip,0],xy[tip,1]+gap/2),xytext=(46,18),fontsize=8,
                arrowprops=dict(arrowstyle='->',color='#7e6025'))
            ax.set(ylim=(-2,2*mirror_y+2),xlabel='x [mm]',ylabel='y [mm]',title=label)
            ax.set_aspect('equal')
            cases.append(dict(label=label,role=row['role'],model_json=row['model_json'],model_file=row['model_file'],model_sha256=digest(root/row['model_file']),domain_right_mm=width,
                highlighted_added_strip_mm=[parent_width,width] if width>parent_width else None,
                cells=len(conn),nodes=len(xy),DOFs=2*len(xy),tip_reference_mm=[80.,30.],actual_tip_node=tip,
                body_box_lower_half_mm=body_box,initial_tip_gap_mm=gap,right_margin_mm=margin))
    for ax in axes:ax.set_xlim(-2,max(case['domain_right_mm'] for case in cases)+2)
    margins = ' vs '.join(f"{case['right_margin_mm']:g}" for case in cases)
    fig.suptitle(f'Actual undeformed geometry | fixed square side 18 mm, centre (71,40) mm\nRight medium margin: {margins} mm; displacement magnification x1',fontsize=11)
    fig.savefig(output/'prepared_domain.png',dpi=180)
    plt.close(fig)
    check()
    unchanged = all(digest(root/name) == pin for name,pin in protocol['bindings'].items())
    png_sha = digest(output/'prepared_domain.png')
    check()
    assert unchanged
    receipt = dict(status='pass',schema_version='right-margin-prepared-view-1.0',cases=cases,
        new_F=0,new_T=0,new_solver=0,new_HP=0,new_model_constructions=0,
        new_geometry_observations=0,new_nodal_force_observations=0,
        qualification='Undeformed prepared geometry only; no response or contact qualification',
        elapsed_seconds=perf_counter()-STARTED,peak_sampled_helper_RSS_bytes=peak,all_bindings_unchanged=unchanged,
        png_sha256=png_sha)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    main()
