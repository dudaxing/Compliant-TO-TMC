"""Once: existing focused tests, cached T44 full/chunk, fresh HP80/120 actions."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
from decimal import Decimal, localcontext, Inexact
import argparse, gzip, json, sys
import numpy as np
import psutil

def main():
    p=argparse.ArgumentParser()
    for k in ('repo','protocol','output'): p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args(); root=a.repo.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',qualification=False,cached_tangent_started=0,cached_tangent_completed=0,
        HP_calls_started=0,HP_calls_completed=0,cached_force_calls=0,formal_solver_calls=0,
        scope='Captured failed state is not an equilibrium or contact qualification',peak_sampled_RSS_bytes=0)
    pins={}; process=psutil.Process()
    def write(path,data): path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def digest(path): return sha256(path.read_bytes()).hexdigest()
    def check():
        m=process.memory_info(); report['peak_sampled_RSS_bytes']=max(report['peak_sampled_RSS_bytes'],m.rss,getattr(m,'peak_wset',m.rss))
        assert perf_counter()-STARTED<=300 and report['peak_sampled_RSS_bytes']<=8*1024**3
        assert not (a.protocol.parent/'stop_requested.txt').exists()
    def bind(path,pin):
        assert digest(path)==pin; pins[path]=pin
    try:
        protocol=json.loads(a.protocol.read_text(encoding='utf-8'))
        for n,pin in protocol['bindings'].items(): bind(root/n,pin)
        check(); sys.path.insert(0,str(root/'hf_repo/src')); sys.path.insert(0,str(root/'hf_repo/scripts'))
        import pytest, xml.etree.ElementTree as ET
        test_paths=[root/'hf_repo/tests'/n for n in ('test_split_numpy_tangent.py','test_split_numpy_tangent_chunked.py')]
        report['pytest_invocations']=1
        code=pytest.main([*(str(x) for x in test_paths),'-q','--maxfail=1','--junitxml='+str(out/'tests.xml')])
        report['pytest_exit_code']=int(code)
        suites=ET.parse(out/'tests.xml').getroot(); totals={k:sum(int(x.get(k,0)) for x in suites.iter('testsuite')) for k in ('tests','errors','failures','skipped')}
        report['tests']=totals; check()
        assert int(code)==0 and totals['tests']>0 and totals['errors']==totals['failures']==totals['skipped']==0
        from hf_eval import split_numpy_tangent as tangent
        from hf_eval.tangent_action import apply_element_tangent_numpy
        from audit_native_force import norm, D, write_gzip
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        captured=root/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/first_tangent_range_input'
        with np.load(captured/'input.npz',allow_pickle=False) as z: inputs={k:z[k].copy() for k in z.files}
        with np.load(captured/'force_fields.npz',allow_pickle=False) as z: fields={k:z[k].copy() for k in z.files}
        ops={k:inputs[k] for k in ('grad','hessian','weights','points')}
        report['product_selector']=bool(tangent._small_product_branch((fields['G_hi'],fields['G_lo']),fields['small_branch'].astype(bool),
            (ops['grad'],ops['hessian'],ops['weights'],inputs['lam'],inputs['mu'],inputs['kr'])))
        report['direction_selector']=tangent._direction_scale_branch(fields['small_branch'].astype(bool),
            (ops['grad'],ops['hessian'],ops['weights'],inputs['lam'],inputs['mu'],inputs['kr']))
        assert not report['product_selector'] and report['direction_selector']
        tensors=[]; report['tangent_archives']={}
        for name in ('_tangent','_tangent_chunked'):
            check(); report['cached_tangent_started']+=1
            with np.errstate(all='ignore'):
                result=getattr(tangent,name)(fields,ops,inputs['lam'],inputs['mu'],float(inputs['kr']))
            report['cached_tangent_completed']+=1; tensors.append(result)
            archive=out/(name+'_tensors.npz'); np.savez_compressed(archive,**result)
            report['tangent_archives'][name]=dict(path=archive.name,sha256=digest(archive)); check()
        assert set(tensors[0])==set(tensors[1])=={'total_tangent','material_tangent','regularization_tangent'}
        assert all(tensors[0][n].tobytes()==tensors[1][n].tobytes() and tensors[0][n].strides==tensors[1][n].strides for n in tensors[0])
        np.savez_compressed(out/'tangents.npz',**tensors[1]); report['full_chunk_all_tensors_byte_equal']=True
        ne=len(inputs['connectivity']); edofs=inputs['edofs']; ndof=len(inputs['lift'])
        # Non-port direction varies by node and component and excites the failed columns.
        rng=np.random.default_rng(20261004); direction=rng.standard_normal(ndof); direction[inputs['fixed_dofs']]=0
        assert direction[edofs[1981,3]]!=direction[edofs[1981,5]]
        np.savez_compressed(out/'direction.npz',direction=direction,edofs=edofs)
        report['direction_sha256']=sha256(direction.tobytes()).hexdigest()
        report['failed_cell_column_values']={str(k):float(direction[edofs[1981,k]]) for k in (3,5)}
        fixture={k:inputs[k] for k in ('grad','hessian','weights','kr','lam','mu')}
        fixture.update(connectivity=np.arange(4*ne,dtype=np.int64).reshape(ne,4),F0=np.zeros(8*ne),fixed_dofs=np.empty(0,dtype=np.int64))
        ll,ww,vv=(x[edofs].ravel() for x in (inputs['lift'],inputs['fluctuation'],direction))
        refs={}
        keys=('tangent_action_decimal','material_tangent_action_decimal','regularization_tangent_action_decimal')
        for precision in (80,120):
            check(); report['HP_calls_started']+=1
            hp=DecimalSplitQ1Reference(fixture,precision=precision).evaluate(ll,ww,tangent_direction=vv,derivative=True)
            report['HP_calls_completed']+=1; refs[precision]={k:hp[k] for k in keys}
            write_gzip(out/f'hp{precision}_local.json.gz',dict(precision=precision,values=refs[precision]))
            check()
        limits={'total':'1e-10','material':'1e-9','regularization':'1e-9'}
        report['checks']={}; checks=0
        with localcontext() as ctx:
            ctx.prec=120
            for part,key in zip(limits,keys):
                actual=apply_element_tangent_numpy(tensors[1][part+'_tangent'],direction[edofs])
                np.savez_compressed(out/(part+'_local_action.npz'),local=actual)
                worst=Decimal(0); agreement=Decimal(0)
                for e in range(ne):
                    if e%256==0: check()
                    ref=refs[80][key][8*e:8*e+8]; other=refs[120][key][8*e:8*e+8]
                    den=max(norm(ref),Decimal('1e-10'))
                    err=norm([D(x)-y for x,y in zip(actual[e],ref)])/den
                    gap=norm([x-y for x,y in zip(ref,other)])/den
                    if not (err<=Decimal(limits[part]) and gap<=Decimal('1e-40')):
                        report['first_failed_action']=dict(part=part,cell=e,error=str(err),HP_agreement=str(gap),scope='local')
                        raise AssertionError('Original local tangent action gate failed')
                    worst=max(worst,err); agreement=max(agreement,gap); checks+=1
                # Local actions are independently scattered on all original shared DOFs.
                global_actual=np.zeros(ndof); np.add.at(global_actual,edofs.ravel(),actual.ravel())
                globals_={}
                for precision in (80,120):
                    with localcontext() as scatter:
                        scatter.prec=3000; scatter.traps[Inexact]=True
                        values=[Decimal(0)]*ndof
                        for e,dofs in enumerate(edofs):
                            for j,dof in enumerate(dofs): values[dof]+=refs[precision][key][8*e+j]
                    globals_[precision]=values
                den=max(norm(globals_[80]),Decimal('1e-10'))
                err=norm([D(x)-y for x,y in zip(global_actual,globals_[80])])/den
                gap=norm([x-y for x,y in zip(globals_[80],globals_[120])])/den
                np.savez_compressed(out/(part+'_actions.npz'),local=actual,global_action=global_actual)
                write_gzip(out/(part+'_global_references.json.gz'),globals_)
                if not (err<=Decimal(limits[part]) and gap<=Decimal('1e-40')):
                    report['first_failed_action']=dict(part=part,error=str(err),HP_agreement=str(gap),scope='global')
                    raise AssertionError('Original global tangent action gate failed')
                checks+=1
                report['checks'][part]=dict(local_worst=str(worst),local_HP_agreement=str(agreement),global_error=str(err),global_HP_agreement=str(gap),limit=limits[part])
        report.update(status='pass',local_and_global_checks=checks,all_cells=ne,all_DOFs=ndof,
            all_columns_qualified=False,failed_T44_equilibrium_qualified=False,production_force_changed=False,
            range_guards_changed=False,formal_physical_path_runs=0)
        check()
    except BaseException as error:
        report.update(status='not_pass',error=repr(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,all_bindings_unchanged=all(digest(p)==h for p,h in pins.items()))
        if not report['all_bindings_unchanged']:
            report.update(status='not_pass',error='Final source/input binding drift')
        write(out/'receipt.json',report)
    assert report['all_bindings_unchanged']; print(json.dumps(report),flush=True)

if __name__=='__main__': main()
