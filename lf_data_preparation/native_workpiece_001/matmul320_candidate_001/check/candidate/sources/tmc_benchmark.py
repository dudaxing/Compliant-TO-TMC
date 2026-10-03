"""One versioned C-shape code benchmark; explicit source units and path evidence."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import uuid

import numpy as np

from .data import canonical_hash
from .evaluation import implementation_hash
from .tmc import rectangular_model, NewtonSettings, solve_path, TMCError
from .tmc_kernel import KERNEL_VERSION

SOURCE_HASH = "58f203ff1dba3c64c64d5fa2de12d4bdd3a711be69ee83a4ddd3335680e3eb08"
SOLVER_PROFILE = "hf2_precision_v2"


def cshape_settings(time_limit_seconds=1200.0):
    """Benchmark-specific precision margin; generic Newton defaults are unchanged."""
    return NewtonSettings(tolerance=1e-9, time_limit_seconds=time_limit_seconds)


def cshape_preset():
    """Independent transcription of the uploaded source configuration only."""
    nx, ny, Lx, Ly = 62, 30, 100.0, 50.0
    yy, xx = np.indices((ny, nx))
    solid = ((((yy < 6) | (yy >= 24)) & (xx < 60)) | (xx < 6)).ravel()
    factors = np.where(solid, 1.0, 1e-6)
    fixed_nodes = np.arange(ny + 1) * (nx + 1)
    fixed = (2 * fixed_nodes[:, None] + np.arange(2)).ravel()
    model = rectangular_model(nx, ny, Lx, Ly, factors=factors, solid=solid, fixed_dofs=fixed)
    loaded_nodes = ny * (nx + 1) + np.arange(55, 61)
    force = np.zeros(model.ndof)
    force[2 * loaded_nodes + 1] = [-.3, -.6, -.6, -.6, -.6, -.3]
    targets = np.linspace(.01, 1.0, 100)
    config = {"benchmark_id":"p26_uploaded_cshape_62x30_source_v1", "source_zip_sha256":SOURCE_HASH,
              "units_mode":"source_numeric", "control":"force_multiplier", "domain":[Lx,Ly],
              "cells":[nx,ny], "E":100.0,"nu":0.3,"kv":1e-6,"alpha":1e-6,
              "thickness_factor":1.0,"kr":model.kr,"solid_cells":int(solid.sum()),
              "medium_cells":int((~solid).sum()),"total_force":force.reshape(-1,2).sum(axis=0).tolist(),
              "loaded_nodes":loaded_nodes.tolist(),"loaded_coordinates":model.coordinates[loaded_nodes].tolist(),
              "loaded_force_y":force[2*loaded_nodes+1].tolist(),
              "targets_origin":"numpy_linspace_default; external source setup can supply exact MATLAB target values"}
    assert model.ne == 1860 and model.ndof == 3906 and solid.sum() == 828
    return model, force, targets, loaded_nodes, config


def _scalar_record(record):
    return {key: value for key, value in record.items() if key not in {"u", "J", "support_reaction", "internal_force"}}


def validate_source_setup(path):
    """Compare the independent preset with ordinary exported reference arrays."""
    model, force, expected_targets, loaded, _ = cshape_preset()
    with np.load(path, allow_pickle=False) as source:
        for name in ('connectivity','loaded_nodes','gamma','fixed_dofs','coordinates','F0','targets'):
            value = source[name]
            if np.iscomplexobj(value) or not np.issubdtype(value.dtype,np.number) or not np.all(np.isfinite(value)):
                raise TMCError(f"source setup {name} must be finite real numeric data")
        exact = {"connectivity":model.connectivity,"loaded_nodes":loaded,
                 "gamma":np.where(model.solid,1.0,1e-6)}
        for name, expected in exact.items():
            if source[name].shape != expected.shape or not np.array_equal(source[name],expected):
                raise TMCError(f"source setup {name} differs from frozen preset")
        if not np.array_equal(np.sort(source['fixed_dofs']),model.fixed_dofs):
            raise TMCError("source setup fixed DOFs differ from frozen preset")
        for name, expected in {"coordinates":model.coordinates,"F0":force}.items():
            if source[name].shape != expected.shape or not np.allclose(source[name],expected,rtol=0,atol=1e-12):
                raise TMCError(f"source setup {name} differs from frozen preset")
        targets = source['targets'].copy()
        if targets.shape != expected_targets.shape or not np.allclose(targets,expected_targets,rtol=0,atol=2e-15):
            raise TMCError("source target multipliers differ from frozen preset")
    return targets


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k:_json(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [_json(v) for v in value]
    return value


def run_cshape(output_directory, *, source_targets=None, time_limit_seconds=1200.0):
    """Run exactly the preset; optional targets carry source-generated float values."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    model, force, targets, loaded_nodes, config = cshape_preset()
    if source_targets is not None:
        raw_targets = np.asarray(source_targets)
        if np.iscomplexobj(raw_targets) or not np.issubdtype(raw_targets.dtype,np.number):
            raise TMCError("source targets must be real numeric values")
        received = np.asarray(raw_targets, dtype=float)
        if received.shape != (100,) or not np.all(np.isfinite(received)) or not np.allclose(received,targets,atol=2e-15,rtol=0):
            raise TMCError("source targets do not match the frozen 100-step preset")
        targets = received.copy()
        config["targets_origin"] = "source_exported_exact_values"
    settings = cshape_settings(time_limit_seconds)
    config["targets"] = targets.tolist()
    config["solver"] = asdict(settings)
    config.update(solver_profile=SOLVER_PROFILE, kernel_version=KERNEL_VERSION,
                  internal_newton_tolerance=settings.tolerance, external_free_residual_tolerance=1e-8,
                  independent_verification="separate offline evidence; not inferred from production success")
    (output/'config.json').write_text(json.dumps(config,indent=2,allow_nan=False),encoding='utf-8')
    np.savez_compressed(output/'model.npz', coordinates=model.coordinates, connectivity=model.connectivity,
                        solid=model.solid, factors=np.where(model.solid,1.0,1e-6), fixed_dofs=model.fixed_dofs,
                        F0=force, loaded_nodes=loaded_nodes, targets=targets,
                        lam=model.lam,mu=model.mu,kr=np.array(model.kr),
                        hx=np.array(model.hx),hy=np.array(model.hy),thickness=np.array(model.thickness),**model.ops)
    progress_path = output/'accepted_steps.jsonl'
    step_directory = output/'steps'
    step_directory.mkdir()
    count = 0

    def on_accept(record):
        nonlocal count
        count += 1
        name = f'step_{count:04d}.npz'
        np.savez_compressed(step_directory/name, u=record['u'], J=record['J'],
                            support_reaction=record['support_reaction'],
                            internal_force=record['internal_force'],
                            load_multiplier=np.array(record['lambda']))
        brief = _scalar_record(record)
        brief['arrays_file'] = 'steps/' + name
        brief['loaded_displacements'] = record['u'].reshape(-1,2)[loaded_nodes].tolist()
        with progress_path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(_json(brief),allow_nan=False)+'\n')
            stream.flush()
        print(f"accepted lambda={record['lambda']:.8f} minJ={record['minimum_J']:.6g} "
              f"residual={record['relative_residual']:.3e} checks={record['newton_checks']}", flush=True)

    result = solve_path(model,force,targets,settings,on_accept=on_accept)
    accepted = result['accepted_steps']
    fields = {"lambda":np.array([r['lambda'] for r in accepted]),
              "original_target":np.array([r['is_original_target'] for r in accepted]),
              "U":np.array([r['u'] for r in accepted]).reshape(-1,model.ndof),
              "J":np.array([r['J'] for r in accepted]).reshape(-1,model.ne,9),
              "support_reaction":np.array([r['support_reaction'] for r in accepted]).reshape(-1,model.ndof),
              "internal_force":np.array([r['internal_force'] for r in accepted]).reshape(-1,model.ndof),
              "solid_material_energy":np.array([r['solid_material_energy'] for r in accepted]),
              "medium_material_energy":np.array([r['medium_material_energy'] for r in accepted]),
              "relative_residual":np.array([r['relative_residual'] for r in accepted]),
              "minimum_J":np.array([r['minimum_J'] for r in accepted]),
              "newton_checks":np.array([r['newton_checks'] for r in accepted]),
              "elapsed_seconds":np.array([r['elapsed_seconds'] for r in accepted])}
    np.savez_compressed(output/'cshape_path.npz',**fields)
    import jax
    from importlib.metadata import version
    summary = {key:value for key,value in result.items() if key not in {'u','target_metrics','accepted_steps'}}
    summary.update(schema_version='hf-tmc-code-benchmark-1.0',evaluation_id=str(uuid.uuid4()),
                   created_at_utc=datetime.now(timezone.utc).isoformat(),
                   benchmark_config=config,benchmark_config_sha256=canonical_hash(config),
                   source_code_sha256=implementation_hash(),
                   units={'length':'source_length','force':'source_force','stress':'source_stress','energy':'source_energy'},
                   model_extent='full_domain; no symmetry force factor',
                   functionality={'status':'not_assessed'}, contact_accuracy={'status':'not_validated'},
                   accepted_step_count=len(accepted),original_targets_reached=int(fields['original_target'].sum()),
                   accepted_steps=[_scalar_record(r) for r in accepted],
                   target_metrics=_scalar_record(result['target_metrics']) if result['target_metrics'] is not None else None,
                   environment={'python':platform.python_version(),'versions':{n:version(n) for n in ['numpy','scipy','jax','jaxlib','matplotlib']},
                                'backend':jax.default_backend(),'x64':bool(jax.config.read('jax_enable_x64'))})
    (output/'result.json').write_text(json.dumps(_json(summary),indent=2,allow_nan=False),encoding='utf-8')
    try:
        plot_benchmark(model,force,loaded_nodes,fields,output)
        summary['visualization'] = {'status':'success'}
    except (ValueError,OSError,RuntimeError) as error:
        summary['visualization'] = {'status':'failed','reason':str(error)}
    (output/'result.json').write_text(json.dumps(_json(summary),indent=2,allow_nan=False),encoding='utf-8')
    return summary


def plot_benchmark(model,force,loaded_nodes,path,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    polygons = model.coordinates[model.connectivity]
    colors = np.where(model.solid[:,None], np.array([.15,.23,.32,1]), np.array([.85,.92,.96,.55]))

    def meshplot(ax,coordinates,title):
        ax.add_collection(PolyCollection(coordinates[model.connectivity],facecolors=colors,edgecolors='none'))
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.set_title(title,fontsize=10)
        ax.set_xlabel('source length x')
        ax.set_ylabel('source length y')

    fig,axes=plt.subplots(1,2,figsize=(12,4.7))
    local=np.array([[0,0],[model.hx,0],[model.hx,model.hy],[0,model.hy]])
    axes[0].plot(*local[[0,1,2,3,0]].T,color='#253b50')
    for i,point in enumerate(local):
        axes[0].annotate(f'{i}: ux,uy',point,xytext=(6,5),textcoords='offset points')
    qp=(model.ops['points']+1)*np.array([model.hx,model.hy])/2
    axes[0].scatter(*qp.T,c='#c96632',s=40)
    axes[0].set_aspect('equal'); axes[0].set_title('Q1 corners / 9 Lobatto points')
    axes[0].set_xlabel('source length x'); axes[0].set_ylabel('source length y')
    meshplot(axes[1],model.coordinates,'Source preset: 828 solid / 1032 medium cells')
    axes[1].scatter(*model.coordinates[np.unique(model.fixed_dofs//2)].T,s=8,c='#c96632',label='fixed x,y')
    nodes=model.coordinates[loaded_nodes]
    axes[1].quiver(nodes[:,0],nodes[:,1],np.zeros(6),force[2*loaded_nodes+1],angles='xy',scale_units='xy',scale=.08,color='#bb4429')
    axes[1].legend(loc='lower right')
    fig.tight_layout();fig.savefig(output/'operators_and_regions.png',dpi=160,bbox_inches='tight');plt.close(fig)
    count=len(path['lambda'])
    if not count:
        return
    chosen=np.unique(np.linspace(0,count-1,min(4,count)).astype(int))
    fig,axes=plt.subplots(1,len(chosen),figsize=(4.3*len(chosen),4.2),squeeze=False)
    for ax,index in zip(axes.flat,chosen):
        deformed=model.coordinates+path['U'][index].reshape(-1,2)
        meshplot(ax,deformed,f"lambda={path['lambda'][index]:.3f}; min J={path['minimum_J'][index]:.4g}\nactual deformation, factor 1")
    fig.tight_layout();fig.savefig(output/'cshape_deformation_levels.png',dpi=160,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    mean_uy=path['U'][:,2*loaded_nodes+1].mean(axis=1)
    axes[0].plot(path['lambda'],mean_uy,color='#226b88');axes[0].set_ylabel('mean loaded-node uy (source length)')
    axes[1].plot(path['lambda'],path['minimum_J'],color='#226b88');axes[1].set_ylabel('minimum J across full domain')
    axes[2].semilogy(path['lambda'],np.maximum(path['relative_residual'],1e-18),color='#226b88')
    axes[2].axhline(1e-8,color='#c96632',ls='--',label='external threshold 1e-8')
    axes[2].axhline(1e-9,color='#668657',ls=':',label='internal stopping 1e-9')
    axes[2].set_ylabel('relative free-force residual');axes[2].legend(fontsize=7)
    for ax in axes:
        ax.set_xlabel('load multiplier');ax.grid(alpha=.2)
    fig.suptitle('Accepted states only; source numeric code benchmark')
    fig.tight_layout();fig.savefig(output/'cshape_path_diagnostics.png',dpi=160,bbox_inches='tight');plt.close(fig)
