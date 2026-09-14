"""Read-only three-state floating-point sensitivity probe; never solves a path.

The Decimal diagnostic holds binary64 displacements, operators and material
coefficients fixed, then evaluates the same weak residual at 50 digits. It is
not another production implementation or a changed convergence tolerance.
"""
from decimal import Decimal, localcontext
from pathlib import Path
from time import perf_counter
import hashlib
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def read(path):
    with np.load(path, allow_pickle=False) as src:
        return {key: src[key] for key in src.files}


def norm(a):
    return float(np.linalg.norm(np.asarray(a).ravel()))


def prep(spec, model):
    nx, ny = spec['cshape']['cells']
    lx, ly = spec['cshape']['domain']
    hx, hy = lx/nx, ly/ny
    points = np.array([(x, y) for x in (-1., 0., 1.) for y in (-1., 0., 1.)])
    signs = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
    grad = np.empty((9, 4, 2))
    for a, (sx, sy) in enumerate(signs):
        grad[:, a, 0] = sx*(1+sy*points[:, 1])/(2*hx)
        grad[:, a, 1] = sy*(1+sx*points[:, 0])/(2*hy)
    univariate = {-1.:1/3, 0.:4/3, 1.:1/3}
    weights = np.array([univariate[x]*univariate[y]*hx*hy/4 for x,y in points])
    E, nu, alpha = (spec['material'][k] for k in ('E', 'nu', 'alpha'))
    lam = E*nu/((1+nu)*(1-2*nu))*model['gamma']
    mu = E/(2*(1+nu))*model['gamma']
    kr = alpha*lx**2*(E/(3*(1-2*nu))+4*(E/(2*(1+nu)))/3)
    h = signs[:,0]*signs[:,1]/(hx*hy)
    edofs = (2*model['connectivity'][...,None]+np.arange(2)).reshape(-1, 8)
    return grad, weights, lam, mu, kr, h, edofs


def assemble(fe, edofs, ndof):
    result = np.zeros(ndof)
    np.add.at(result, edofs.ravel(), fe.ravel())
    return result


def numpy_forms(u, model, ops):
    grad, w, lam, mu, kr, h, edofs = ops
    nodal = u.reshape(-1,2)[model['connectivity']]
    grad_u = np.einsum('eai,qaj->eqij', nodal, grad)
    F = np.eye(2)+grad_u
    J = F[...,0,0]*F[...,1,1]-F[...,0,1]*F[...,1,0]
    C = np.einsum('eqki,eqkj->eqij', F, F)
    det_c = C[...,0,0]*C[...,1,1]-C[...,0,1]**2
    inv_c = np.empty_like(C)
    inv_c[...,0,0], inv_c[...,1,1] = C[...,1,1], C[...,0,0]
    inv_c[...,0,1], inv_c[...,1,0] = -C[...,0,1], -C[...,1,0]
    inv_c /= det_c[...,None,None]
    coeff = lam[:,None]*np.log(J)-mu[:,None]
    S = lam[:,None,None,None]*np.log(J)[...,None,None]*inv_c + mu[:,None,None,None]*(np.eye(2)-inv_c)
    Pfs = np.einsum('eqij,eqjk->eqik', F, S)
    inverse_t = np.empty_like(F)
    inverse_t[...,0,0], inverse_t[...,1,1] = F[...,1,1], F[...,0,0]
    inverse_t[...,0,1], inverse_t[...,1,0] = -F[...,1,0], -F[...,0,1]
    inverse_t /= J[...,None,None]
    Pdirect = mu[:,None,None,None]*F+coeff[...,None,None]*inverse_t
    inv_c_j2 = inv_c*(det_c/J**2)[...,None,None]
    S_j2 = lam[:,None,None,None]*np.log(J)[...,None,None]*inv_c_j2 + mu[:,None,None,None]*(np.eye(2)-inv_c_j2)
    Pfs_j2 = np.einsum('eqij,eqjk->eqik', F, S_j2)

    # Source engineering-Green strain operator B1 = B0 + Aq G.
    G = np.zeros((9,4,8))
    G[:,0,0::2], G[:,1,1::2] = grad[:,:,0], grad[:,:,0]
    G[:,2,0::2], G[:,3,1::2] = grad[:,:,1], grad[:,:,1]
    B0 = np.zeros((9,3,8))
    B0[:,0,0::2], B0[:,1,1::2] = grad[:,:,0], grad[:,:,1]
    B0[:,2,0::2], B0[:,2,1::2] = grad[:,:,1], grad[:,:,0]
    Aq = np.zeros((*J.shape,3,4))
    Aq[:,:,0,0:2], Aq[:,:,1,2:4] = grad_u[:,:,:,0], grad_u[:,:,:,1]
    Aq[:,:,2,0:2], Aq[:,:,2,2:4] = grad_u[:,:,:,1], grad_u[:,:,:,0]
    B1 = B0+np.einsum('eqij,qjk->eqik', Aq, G)
    Svoigt = np.stack((S[...,0,0], S[...,1,1], S[...,0,1]), axis=-1)
    material = {
        'direct_piola':np.einsum('q,qaj,eqij->eai',w,grad,Pdirect),
        'source_FS':np.einsum('q,qaj,eqij->eai',w,grad,Pfs),
        'source_B1TS':np.einsum('q,eqia,eqi->ea',w,B1,Svoigt).reshape(-1,4,2),
        'FS_with_J_squared_denominator':np.einsum('q,qaj,eqij->eai',w,grad,Pfs_j2),
    }
    mixed = np.einsum('a,eai->ei',h,nodal)
    regularization = 2*kr*(np.exp(-5*J)@w)[:,None,None]*h[None,:,None]*mixed[:,None,:]
    internal = {name:assemble(value+regularization,edofs,len(u)) for name,value in material.items()}
    svf = np.linalg.svd(F, compute_uv=False)
    svc = np.linalg.svd(C, compute_uv=False)
    cond_f, cond_c = svf[...,0]/svf[...,1], svc[...,0]/svc[...,1]
    rel_det_error = np.abs(det_c-J**2)/J**2
    cancellation = (np.abs(C[...,0,0]*C[...,1,1])+np.abs(C[...,0,1]**2))/np.abs(det_c)
    piola_error = np.linalg.norm(Pfs-Pdirect,axis=(-1,-2))
    location = np.unravel_index(np.argmax(rel_det_error),J.shape)
    conditioning = dict(min_J=float(J.min()), max_cond_F=float(cond_f.max()), max_cond_C=float(cond_c.max()),
        max_cond_F_squared=float((cond_f**2).max()), max_relative_detC_minus_J_squared=float(rel_det_error.max()),
        max_determinant_cancellation_factor=float(cancellation.max()),
        determinant_worst_element=int(location[0]), determinant_worst_q=int(location[1]),
        determinant_worst_gamma=float(model['gamma'][location[0]]),
        max_P_FS_minus_direct_absolute=float(piola_error.max()),
        material_element_force_norm=norm(material['direct_piola']),
        regularization_element_force_norm=norm(regularization),
        material_global_force_norm=norm(assemble(material['direct_piola'],edofs,len(u))),
        regularization_global_force_norm=norm(assemble(regularization,edofs,len(u))))
    raw = dict(F=F,J=J,det_C=det_c,cond_F=cond_f,cond_C=cond_c,
               determinant_relative_difference=rel_det_error,piola_difference=Pfs-Pdirect)
    return internal, conditioning, raw


def decimal_direct(u, model, ops, level):
    """50-digit weak residual for the exact binary64 values of frozen inputs."""
    grad, weights, lam, mu, kr, h, edofs = ops
    D = Decimal.from_float
    with localcontext() as ctx:
        ctx.prec = 50
        zero, one, two = Decimal(0), Decimal(1), Decimal(2)
        dg = [[[D(float(x)) for x in row] for row in q] for q in grad]
        dw, dh = [D(float(x)) for x in weights], [D(float(x)) for x in h]
        dk = D(float(kr))
        result = [zero for _ in u]
        Jminimum = None
        for e, conn in enumerate(model['connectivity']):
            un = [[D(float(u[2*a+i])) for i in range(2)] for a in conn]
            dl, dm = D(float(lam[e])), D(float(mu[e]))
            force = [[zero,zero] for _ in range(4)]
            integral = zero
            for q in range(9):
                F = [[(one if i==j else zero)+sum((un[a][i]*dg[q][a][j] for a in range(4)),zero)
                      for j in range(2)] for i in range(2)]
                J = F[0][0]*F[1][1]-F[0][1]*F[1][0]
                if J <= zero:
                    raise ValueError('Decimal diagnostic encountered nonpositive J')
                Jminimum = J if Jminimum is None else min(Jminimum,J)
                c = dl*J.ln()-dm
                Pi = [[dm*F[0][0]+c*F[1][1]/J,dm*F[0][1]-c*F[1][0]/J],
                      [dm*F[1][0]-c*F[0][1]/J,dm*F[1][1]+c*F[0][0]/J]]
                for a in range(4):
                    for i in range(2):
                        force[a][i] += dw[q]*(Pi[i][0]*dg[q][a][0]+Pi[i][1]*dg[q][a][1])
                integral += dw[q]*(-5*J).exp()
            mixed = [sum((dh[a]*un[a][i] for a in range(4)),zero) for i in range(2)]
            for a in range(4):
                for i in range(2):
                    result[2*conn[a]+i] += force[a][i]+two*dk*integral*dh[a]*mixed[i]
        external = [D(float(level))*D(float(x)) for x in model['F0']]
        residual = [a-b for a,b in zip(result,external)]
        free = np.setdiff1d(np.arange(len(u)),model['fixed_dofs'])
        abs_residual = sum((residual[i]**2 for i in free),zero).sqrt()
        load_norm = sum((x*x for x in external),zero).sqrt()
        data = dict(precision_decimal_digits=50, relative_free_residual=str(abs_residual/load_norm),
                    absolute_free_residual=str(abs_residual), force_scale=str(load_norm),minimum_J=str(Jminimum),
                    definition='Exact binary64 input values promoted to Decimal; arithmetic, logarithm, exponential, integration and assembly at 50 decimal digits')
        return np.array([float(x) for x in result]),np.array([float(x) for x in residual]),data


def main():
    started = perf_counter()
    spec_path = ROOT/'hf_repo/validation/hf2/validation_spec.json'
    spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
    ma_path = ROOT/'reference_validation/matlab/cshape_001/cshape_path.npz'
    py_path = ROOT/'hf2_results/cshape_python_001/cshape_path.npz'
    ma, py = read(ma_path), read(py_path)
    model = {key:ma[key] for key in ('connectivity','gamma','F0','fixed_dofs')}
    model['connectivity'] = model['connectivity'].astype(np.int64)
    for key in ('gamma','F0','fixed_dofs'):
        model[key] = model[key].ravel()
    model['fixed_dofs'] = model['fixed_dofs'].astype(np.int64)
    ops = prep(spec,model)
    module_spec = importlib.util.spec_from_file_location('offline_comparison',ROOT/'hf_repo/scripts/compare_cshape.py')
    comparison = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(comparison)
    reports = []
    for side,index in [('python',72),('matlab',75),('matlab',98)]:
        payload = py if side=='python' else ma
        key = 'lambda' if side=='python' else 'targets'
        level, u = float(payload[key].ravel()[index]),payload['U'][index]
        free = np.setdiff1d(np.arange(len(u)),model['fixed_dofs'])
        external = level*model['F0']
        scale = norm(external)
        internals,conditioning,raw = numpy_forms(u,model,ops)
        independent = comparison.independent_state(u,model,spec)['internal']
        internals['comparison_independent_state'] = independent
        if side=='matlab':
            internals['stored_MATLAB_source'] = payload['internal_force'][index]
        decimal_i,decimal_r,decimal_report = decimal_direct(u,model,ops,level)
        internals['decimal50_direct'] = decimal_i
        stored_key = 'relative_residual' if side=='python' else 'relative_free_residual'
        report = dict(side=side,target_index=index+1,load_multiplier=level,
                      stored_relative_free_residual=float(payload[stored_key][index]),
                      force_scale=scale,force_total_y=float(external[1::2].sum()),
                      absolute_free_residual_tolerance=1e-8*scale, relative_free_residual_tolerance=1e-8,
                      conditioning=conditioning, decimal50=decimal_report,forms={},differences={})
        for name,internal in internals.items():
            residual = decimal_r if name=='decimal50_direct' else internal-external
            absolute = norm(residual[free])
            report['forms'][name] = dict(absolute_free_residual=absolute,relative_free_residual=absolute/scale,
                passes_unchanged_tolerance=absolute/scale<=1e-8,internal_force_norm=norm(internal),
                residual_fixed_norm=norm(residual[model['fixed_dofs']]))
            raw[name+'_internal'] = internal
            raw[name+'_residual'] = residual
            for ref in ('direct_piola','decimal50_direct'):
                if ref in internals:
                    delta = internal-internals[ref]
                    report['differences'][name+'_minus_'+ref] = dict(full_norm=norm(delta),
                        free_norm=norm(delta[free]),free_norm_over_external=norm(delta[free])/scale,
                        full_max_absolute=float(np.max(np.abs(delta))))
        raw.update(U=u,external=external,free_dofs=free,lambda_value=level)
        filename = f'{side}_{index+1:03d}.npz'
        np.savez_compressed(OUT/filename,**raw)
        report['raw_arrays'] = filename
        reports.append(report)
        print(side,level,{k:v['relative_free_residual'] for k,v in report['forms'].items()},flush=True)
    result = dict(schema_version='hf2-residual-sensitivity-1.0',scope='Three frozen states; no solve; no changed tolerance or path',
        units_mode='source_numeric',decimal_scope='Diagnostic exact-arithmetic approximation of fixed binary64 inputs, not an independent physical benchmark',
        cases=reports,wall_seconds=perf_counter()-started,
        source_zip_sha256=spec['source_zip_sha256'],
        inputs_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            spec_path,ma_path,py_path,ROOT/'reference_validation/matlab/source/assembleKtFi.m',
            ROOT/'hf_repo/src/hf_eval/tmc_kernel.py',ROOT/'hf_repo/scripts/compare_cshape.py',Path(__file__))},
        scientific_status='All three independent Piola over-threshold observations retained; evaluate source-expression agreement and arithmetic sensitivity separately')
    (OUT/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('Finished read-only sensitivity probe in',result['wall_seconds'],'seconds',flush=True)


if __name__=='__main__':
    main()
