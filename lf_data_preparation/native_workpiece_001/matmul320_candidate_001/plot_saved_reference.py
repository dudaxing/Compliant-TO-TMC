"""Visualize only saved candidate-reference gates; no mechanics evaluation."""
from pathlib import Path
from time import perf_counter
import gzip
import hashlib
import json

STARTED=perf_counter()
STAGE=Path(__file__).resolve().parent


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import psutil

    source=STAGE/'check/reference/result.json'
    summary=json.loads(source.read_text(encoding='utf-8'))
    assert summary['status']=='pass'
    checks_file=source.with_name('checks.json.gz')
    assert hashlib.sha256(checks_file.read_bytes()).hexdigest()==summary['files']['checks.json.gz']
    with gzip.open(checks_file, 'rt', encoding='utf-8') as stream:
        checks=json.load(stream)
    assert len(checks)==summary['local_gate_count']+summary['global_gate_count']
    assert all(row['pass_gate'] for row in checks)
    output=STAGE/'saved_reference_view'
    output.mkdir()
    labels=['Total', 'Material', 'Hu regularization']
    parts=['total','material','regularization']
    fig, axes=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
    plotted=[]
    for ax,kind,title in zip(axes,['force','action','CSC_action'],
                            ['Complete weak force','Declared direction Jv','Full CSC action'],strict=True):
        scopes=['local','global'] if kind!='CSC_action' else ['global']
        for scope in scopes:
            selected=[max((row for row in checks if row['scope']==scope and row['kind']==kind
                           and row['component']==part),key=lambda row:float(row['normalized_error']))
                      for part in parts]
            values=[float(row['normalized_error'])/float(row['limit']) for row in selected]
            plotted.extend(dict(scope=scope,kind=kind,component=part,
                normalized_error=row['normalized_error'],limit=row['limit'],error_over_gate=value)
                for part,row,value in zip(parts,selected,values,strict=True))
            display=np.maximum(values,1e-30)
            ax.plot(labels,display,'o-' if scope=='local' else 's--',label=scope)
        ax.axhline(1,color='#bb3333',ls=':',label='acceptance boundary')
        ax.set(yscale='log',ylim=(1e-30,10),title=title,ylabel='saved normalized error / original gate')
        ax.tick_params(axis='x',rotation=18)
        ax.grid(True,axis='y',alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('Captured F36: matmul320 candidate vs independent HP80/120\n'
                 '3200 elements, 6642 DOFs; one declared direction; no equilibrium/contact qualification',fontsize=11)
    fig.text(.5,.002,'Zero or <1e-30 ratios use 1e-30 only for display; raw saved values remain unchanged.',
             ha='center',fontsize=8)
    image=output/'reference_error_gates.png'
    fig.savefig(image,dpi=180)
    plt.close(fig)
    info=psutil.Process().memory_info()
    peak=max(info.rss,getattr(info,'peak_wset',info.rss))
    elapsed=perf_counter()-STARTED
    assert elapsed<=120 and peak<=8*1024**3 and not (STAGE/'stop_requested.txt').exists()
    report=dict(status='pass',scope='Saved reference display only; no new force/tangent/solver/HP',
        elapsed_seconds=elapsed,sampled_peak_RSS_bytes=peak,
        source_result_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        checks_sha256=hashlib.sha256(checks_file.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        plotted_rows=plotted,image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
        display_floor_error_over_gate=1e-30,new_mechanics_calls=0)
    (output/'view_metadata.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('status','elapsed_seconds','sampled_peak_RSS_bytes','new_mechanics_calls')}))


if __name__=='__main__':
    main()
