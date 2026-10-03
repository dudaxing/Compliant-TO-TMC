"""Classify saved actions and exact saved-matrix products; no mechanics calls."""
from pathlib import Path
from time import perf_counter
from decimal import Decimal, Inexact, localcontext
import gzip
import hashlib
import json

STARTED=perf_counter()
STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
OLD=ROOT/'lf_data_preparation/native_workpiece_001/matmul320_candidate_001'
PARTS=('total','material','regularization')
KEYS=('tangent_action_decimal','material_tangent_action_decimal','regularization_tangent_action_decimal')
PEAK=0


def norm(v):
    return sum((x*x for x in v),Decimal(0)).sqrt()


def main():
    import numpy as np
    import psutil
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output=STAGE/'evidence'
    output.mkdir()
    protocol=json.loads((STAGE/'protocol.json').read_text(encoding='utf-8'))
    pins=protocol['bindings']
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    def checkpoint():
        global PEAK
        info=psutil.Process().memory_info()
        PEAK=max(PEAK,info.rss,getattr(info,'peak_wset',info.rss))
        if perf_counter()-STARTED>120 or PEAK>8*1024**3 or (STAGE/'stop_requested.txt').exists():
            raise RuntimeError('New saved-action diagnostic budget closed; no retry')
    def write(name,data):
        (output/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    report=dict(status='running',qualification=False,new_force_calls=0,new_tangent_kernel_calls=0,
        new_solver_calls=0,new_HP_mechanics_calls=0,scope='Saved-array arithmetic and rendering only')
    write('result.json',report)
    try:
        assert all(sha(ROOT/path)==pin for path,pin in pins.items())
        assert json.loads((OLD/'check/reference/result.json').read_text())['status']=='fail'
        with np.load(OLD/'check/candidate/arrays.npz',allow_pickle=False) as a:
            arrays={name:a[name].copy() for name in a.files}
        with np.load(OLD/'check/candidate/fixture.npz',allow_pickle=False) as a:
            edofs=a['edofs'].copy(); local_v=a['local_direction'].copy()
        hp={}
        for precision in (80,120):
            with gzip.open(OLD/f'check/reference/hp{precision}.json.gz','rt',encoding='utf-8') as stream:
                values=json.load(stream)['values']
            hp[precision]={key:list(map(Decimal,values[key])) for key in KEYS}
        checkpoint()
        rows=[]; global_rows=[]; examples={}; layout={}
        fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
        for part,key,ax in zip(PARTS,KEYS,axes,strict=True):
            K=arrays[part+'_tangent']; observed=arrays[part+'_action']
            original_view=K.swapaxes(1,2).copy(order='C').swapaxes(1,2)
            replay=np.einsum('eij,ej->ei',original_view,local_v)
            contiguous=np.einsum('eij,ej->ei',K.copy(order='C'),local_v)
            layout[part]=dict(saved_action_equal_recreated_view_bytes=replay.tobytes()==observed.tobytes(),
                view_strides=list(original_view.strides),C_strides=list(K.strides))
            exact_global=[Decimal(0)]*6642; hp_global={p:[Decimal(0)]*6642 for p in (80,120)}
            errors=[]; exact_errors=[]
            for e in range(3200):
                if e%64==0:checkpoint()
                with localcontext() as context:
                    context.prec=3000; context.traps[Inexact]=True
                    dv=list(map(lambda x:Decimal.from_float(float(x)),local_v[e]))
                    exact=[sum((Decimal.from_float(float(K[e,i,j]))*dv[j] for j in range(8)),Decimal(0)) for i in range(8)]
                    for i,dof in enumerate(edofs[e]):
                        exact_global[int(dof)]+=exact[i]
                        for p in (80,120):hp_global[p][int(dof)]+=hp[p][key][8*e+i]
                with localcontext() as context:
                    context.prec=120; context.traps[Inexact]=False
                    ref=hp[120][key][8*e:8*e+8]; other=hp[80][key][8*e:8*e+8]
                    original=list(map(lambda x:Decimal.from_float(float(x)),observed[e]))
                    den=max(norm(ref),Decimal('1e-10')); limit=Decimal('1e-10' if part=='total' else '1e-9')
                    err=norm([a-b for a,b in zip(original,ref)])/den
                    err_exact=norm([a-b for a,b in zip(exact,ref)])/den
                    agree=norm([a-b for a,b in zip(ref,other)])/den
                    err_C=norm([Decimal.from_float(float(a))-b for a,b in zip(contiguous[e],ref)])/den
                    rows.append(dict(element=e,component=part,saved_error=str(err),exact_saved_tensor_error=str(err_exact),
                        denominator=str(den),original_limit=str(limit),HP80_120_agreement=str(agree),
                        C_layout_error=str(err_C),HPagreement_exceeds_original_gate=agree>Decimal('1e-40'),
                        saved_exceeds_original_gate=err>limit,exact_exceeds_original_gate=err_exact>limit,
                        C_layout_exceeds_original_gate=err_C>limit))
                    errors.append(float(err));exact_errors.append(float(err_exact))
                    if e in (0,1275,1348):
                        examples[f'{part}_{e}']=dict(direction=local_v[e].tolist(),saved_action=list(map(str,original)),
                            exact_saved_tensor_action=list(map(str,exact)),HP120_action=list(map(str,ref)),
                            C_layout_action=contiguous[e].tolist())
            with localcontext() as context:
                context.prec=120;context.traps[Inexact]=False
                ref=hp_global[120]; den=max(norm(ref),Decimal('1e-10'))
                agreement=norm([a-b for a,b in zip(ref,hp_global[80])])/den
                for label,actual in [('saved_global',arrays['global_'+part+'_action']),('saved_CSC',arrays['CSC_'+part+'_action']),('exact_local_scatter',exact_global)]:
                    values=actual if label=='exact_local_scatter' else list(map(lambda x:Decimal.from_float(float(x)),actual))
                    error=norm([a-b for a,b in zip(values,ref)])/den
                    global_rows.append(dict(component=part,action=label,normalized_error=str(error),denominator=str(den),
                        original_limit=str(limit),HP80_120_agreement=str(agreement),reference_limit='1e-40',
                        HPagreement_exceeds_original_gate=agreement>Decimal('1e-40')))
            ax.plot(np.maximum(errors,1e-30),'.',ms=2,alpha=.6,label='original saved action')
            ax.plot(np.maximum(exact_errors,1e-30),'.',ms=2,alpha=.6,label='exact saved K x v (diagnostic)')
            ax.axhline(float(limit),ls=':',color='red',label='original gate')
            ax.set(yscale='log',xlabel='element index',ylabel='normalized error',title=part)
            ax.legend(fontsize=7);ax.grid(alpha=.2)
        fig.suptitle('Closed reference failure: saved contraction vs exact saved-matrix action\n'
                     'Diagnostic only; no new force, derivative evaluation, HP mechanics or qualification',fontsize=11)
        fig.text(.5,.002,'Display floor 1e-30 only; original failure and all raw saved values retained.',ha='center',fontsize=8)
        fig.savefig(output/'saved_action_differences.png',dpi=180);plt.close(fig)
        with gzip.open(output/'element_classification.json.gz','wt',encoding='utf-8') as stream:json.dump(rows,stream)
        write('examples.json',examples);write('global_diagnostic.json',global_rows)
        report.update(status='diagnostic_completed',element_component_rows=len(rows),layout=layout,
            counts={part:dict(saved_exceeds=sum(r['saved_exceeds_original_gate'] for r in rows if r['component']==part),
                            exact_exceeds=sum(r['exact_exceeds_original_gate'] for r in rows if r['component']==part),
                            C_layout_exceeds=sum(r['C_layout_exceeds_original_gate'] for r in rows if r['component']==part),
                            HPagreement_exceeds=sum(r['HPagreement_exceeds_original_gate'] for r in rows if r['component']==part)) for part in PARTS},
            exact_precision=3000,exact_Inexact_trap=True,comparison_precision=120,display_floor=1e-30)
        checkpoint()
        assert all(sha(ROOT/path)==pin for path,pin in pins.items())
    except Exception as error:
        report.update(status='failed',error=repr(error))
        raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=PEAK,
            bindings_unchanged=all(sha(ROOT/path)==pin for path,pin in pins.items()))
        write('result.json',report)
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
