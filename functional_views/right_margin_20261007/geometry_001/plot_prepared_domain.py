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
    for ax,row in zip(axes,protocol['cases']):
        with np.load(root/row['model_file'],allow_pickle=False) as model:
            xy = model['coordinates'];conn = model['connectivity']
            assert xy[model['workpiece_nodes']][:,0].min() == 62. and xy[:,0].max() == row['width_mm']
            body_nodes = xy[model['workpiece_nodes']]
            body_box = [float(body_nodes[:,0].min()),float(body_nodes[:,0].max()),float(body_nodes[:,1].min()),float(body_nodes[:,1].max())]
            assert body_box == [62.,80.,31.,40.]
            tip_nodes = np.flatnonzero(np.all(xy == [80.,30.],axis=1))
            assert len(tip_nodes) == 1
            tip = int(tip_nodes[0])
            gap = body_box[2]-float(xy[tip,1])
            assert gap == 1.
            for reflected in (False,True):
                coordinates = xy.copy()
                if reflected:coordinates[:,1] = 80.-coordinates[:,1]
                ax.add_collection(PolyCollection(coordinates[conn[model['solid']]],facecolors='#457b9d',edgecolors='none'))
                ax.add_collection(PolyCollection(coordinates[conn[model['workpiece_cells']]],facecolors='#bbbbbb',edgecolors='none'))
            if row['width_mm'] > 80:
                ax.add_patch(Rectangle((80,0),row['width_mm']-80,80,facecolor='#e6c676',alpha=.35))
            ax.add_patch(Rectangle((0,0),row['width_mm'],80,fill=False,edgecolor='#555555',linewidth=.8))
            ax.axhline(40,color='#888888',linestyle=':',linewidth=.7)
            ax.scatter(80,30,c='#e09113',s=20,zorder=5)
            ax.annotate(f'Initial tip gap {gap:g} mm',xy=(xy[tip,0],xy[tip,1]+gap/2),xytext=(46,18),fontsize=8,
                arrowprops=dict(arrowstyle='->',color='#7e6025'))
            ax.set(xlim=(-2,85),ylim=(-2,82),xlabel='x [mm]',ylabel='y [mm]',title=row['label'])
            ax.set_aspect('equal')
            cases.append(dict(label=row['label'],model_file=row['model_file'],model_sha256=digest(root/row['model_file']),
                cells=len(conn),nodes=len(xy),DOFs=2*len(xy),tip_reference_mm=[80.,30.],actual_tip_node=tip,
                body_box_lower_half_mm=body_box,initial_tip_gap_mm=gap,right_margin_mm=row['width_mm']-body_box[1]))
    fig.suptitle('Actual undeformed geometry | fixed square side 18 mm, centre (71,40) mm\nRight medium margin: 0 vs 2 mm; displacement magnification x1',fontsize=11)
    fig.savefig(output/'prepared_domain.png',dpi=180)
    plt.close(fig)
    check()
    unchanged = all(digest(root/name) == pin for name,pin in protocol['bindings'].items())
    png_sha = digest(output/'prepared_domain.png')
    check()
    assert unchanged
    receipt = dict(status='pass',schema_version='right-margin-prepared-view-1.0',cases=cases,
        new_F=0,new_T=0,new_solver=0,new_HP=0,new_model_constructions=0,
        qualification='Undeformed prepared geometry only; no response or contact qualification',
        elapsed_seconds=perf_counter()-STARTED,peak_sampled_helper_RSS_bytes=peak,all_bindings_unchanged=unchanged,
        png_sha256=png_sha)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    main()
