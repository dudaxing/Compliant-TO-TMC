"""Bounded fixed-state HF-2 precision gate; no nonlinear solve or path update.

All numerical policy comes from the pre-frozen precision specification. The
three archived states are not required to be equilibrated under the repaired
expression. This gate measures arithmetic error, component forces, and the
actual Jacobian action at those unchanged states.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from time import perf_counter

import numpy as np

from hf2_precision_reference import DecimalQ1Reference, compare_float_to_decimal, decimal_norm


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(value):
    return float(np.linalg.norm(np.asarray(value).ravel()))


def decimal_error(actual, reference, floor, precision=80):
    with localcontext() as context:
        context.prec = precision
        absolute = decimal_norm([a-b for a,b in zip(actual,reference)],precision)
        denominator = max(decimal_norm(reference,precision),floor)
        if denominator <= 0:
            raise ValueError('Nonpositive precision comparison scale')
        return dict(absolute_error_decimal=str(absolute),relative_error_decimal=str(absolute/denominator),
                    absolute_error=float(absolute),denominator=float(denominator),relative_error=float(absolute/denominator))


def _selected(values, indices):
    return values if indices is None else [values[i] for i in indices]


def domain_step(reference_state, precision):
    """Predeclared determinant bound; never examines a residual or FD error."""
    with localcontext() as context:
        context.prec = precision
        bound = Decimal(1)
        for jrow,arow,brow in zip(reference_state['J_decimal'],reference_state['dJ_decimal'],reference_state['det_dF_decimal']):
            for J,a,b in zip(jrow,arow,brow):
                if a:
                    bound = min(bound,J/(8*abs(a)))
                if b:
                    bound = min(bound,(J/(8*abs(b))).sqrt())
        h0 = float(Decimal('0.99')*bound)
        if not np.isfinite(h0) or h0 <= 0:
            raise ValueError('Determinant-domain step is not representable as positive binary64')
        return h0


class FloatEvaluator:
    """Actual local JAX response plus x-fast global accumulation.

    Global forces use np.bincount, as the production assembler. Jacobian
    actions are local K_e v_e followed by the identical nodal accumulation.
    No stiffness symmetrization or nonlinear solver is used.
    """
    def __init__(self,kernel,fixture):
        self.kernel = kernel
        self.ops = {k:fixture[k] for k in ('grad','hessian','weights')}
        self.ops['points'] = fixture['points']
        self.lam,self.mu,self.kr = fixture['lam'],fixture['mu'],float(fixture['kr'])
        self.ndof = len(fixture['F0'])
        self.edofs = (2*fixture['connectivity'][...,None]+np.arange(2)).reshape(-1,8)

    def assemble(self,local):
        return np.bincount(self.edofs.ravel(),weights=np.asarray(local).ravel(),minlength=self.ndof)

    def assemble_fsum(self,local):
        """Independent summation of the same local binary64 force entries."""
        contributions = [[] for _ in range(self.ndof)]
        for dof,value in zip(self.edofs.ravel(),np.asarray(local).ravel()):
            contributions[dof].append(float(value))
        return np.array([math.fsum(values) for values in contributions])

    def response(self,u,*,tangent=False,component='total',direction=None,assembly_diagnostic=False):
        lam,mu,kr = self.lam,self.mu,self.kr
        if component=='material':
            kr = 0.
        elif component=='regularization':
            lam,mu = np.zeros_like(lam),np.zeros_like(mu)
        elif component!='total':
            raise ValueError('Unknown component')
        fields = self.kernel.batch_response(u[self.edofs],self.ops,lam,mu,kr,tangent=tangent)
        result = {'internal':self.assemble(fields['residual']),'J':fields['J'],
                  'material_internal':self.assemble(fields['material_residual']),
                  'regularization_internal':self.assemble(fields['regularization_residual'])}
        if direction is not None:
            if not tangent:
                raise ValueError('A Jacobian action requires tangent=True')
            action = np.einsum('eij,ej->ei',fields['tangent'],direction[self.edofs])
            result['tangent_action'] = self.assemble(action)
        if assembly_diagnostic:
            result['fsum_internal'] = self.assemble_fsum(fields['residual'])
        return result

    def determinants(self,u):
        return self.kernel.determinants(u[self.edofs],self.ops)


def force_budget(actual, hp, force_scale, free, precision):
    result = compare_float_to_decimal(actual,hp,force_scale,indices=free,precision=precision)
    with localcontext() as context:
        context.prec = precision
        value = Decimal(result['absolute_error_decimal'])/force_scale
    result['error_over_load_norm'] = float(value)
    result['error_over_load_norm_decimal'] = str(value)
    return result


def j_diagnostic(actual,reference,precision):
    """Pointwise errors versus unrounded HP J; diagnostic only."""
    with localcontext() as context:
        context.prec = precision
        targets = [x for row in reference for x in row]
        actual_flat = np.asarray(actual).ravel()
        errors = [abs(Decimal.from_float(float(a))-r)/abs(r) for a,r in zip(actual_flat,targets)]
        worst = max(range(len(errors)),key=errors.__getitem__)
        absolute = abs(Decimal.from_float(float(actual_flat[worst]))-targets[worst])
        return dict(maximum_relative_error=float(errors[worst]),maximum_relative_error_decimal=str(errors[worst]),
                    absolute_error_at_worst_relative=float(absolute),worst_element=worst//9,worst_quadrature=worst%9,
                    double_J_at_worst=float(actual_flat[worst]),HP_J_at_worst_decimal=str(targets[worst]))


def validate(fixture_path,spec_path,output,legacy_kernel=None):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    started = perf_counter()
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8-sig'))
    precision = spec['precision']
    with np.load(fixture_path,allow_pickle=False) as source:
        fixture = {key:source[key] for key in source.files}
    reference = DecimalQ1Reference(fixture,precision=precision)
    if fixture['U'].shape!=(3,reference.ndof) or fixture['levels'].shape!=(3,) or fixture['directions'].shape!=(2,reference.ndof):
        raise ValueError('The frozen precision gate requires three states and two full-grid directions')
    for name in ('grad','hessian','weights','lam','mu','kr','F0','U','levels','directions'):
        value = fixture[name]
        if value.dtype != np.dtype('float64') or not np.all(np.isfinite(value)):
            raise ValueError(f'{name} must be finite binary64')
    if not np.all(fixture['directions'][:,reference.fixed]==0):
        raise ValueError('Frozen directions must vanish on all fixed DOFs')
    if len(spec['case_ids'])!=3 or len(spec['direction_ids'])!=2:
        raise ValueError('Specification case/direction identifiers have wrong lengths')
    if spec['fd_multipliers'] != [1,.1,.01,.001,.0001]:
        raise ValueError('Unexpected finite-difference multiplier schedule')
    import jax
    jax.config.update('jax_enable_x64',True)
    if jax.default_backend()!='cpu':
        raise ValueError('Precision validation requires CPU')
    from hf_eval import tmc_kernel as kernel
    floating = FloatEvaluator(kernel,fixture)
    legacy = None
    if legacy_kernel is not None:
        module_spec = importlib.util.spec_from_file_location('hf2_legacy_precision_kernel',legacy_kernel)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        legacy = FloatEvaluator(module,fixture)
    high = DecimalQ1Reference(fixture,precision=spec['reference_precision_check'])
    checks,curves,records,raw = [],[],[],{}
    def record_check(name,value,tolerance,**extra):
        passed = bool(np.isfinite(value) and value<=tolerance)
        checks.append(dict(check=name,value=float(value),tolerance=float(tolerance),status='pass' if passed else 'fail',**extra))
        return passed
    for case_index,(u,level) in enumerate(zip(fixture['U'],fixture['levels'])):
        case_id = spec['case_ids'][case_index]
        hp = reference.evaluate(u,level)
        hp_high = high.evaluate(u,level)
        scale = hp['force_scale_decimal']
        floor = Decimal('1e-8')*scale
        case = dict(case_id=case_id,load_multiplier=float(level),
                    old_state_high_precision_relative_residual=hp['relative_residual'],
                    note='The unchanged old state is not gated for equilibrium',minimum_J=hp['minimum_J'],modes={},legacy={})
        # This compares unrounded Decimal vectors, including energies and J.
        precision_fields = ('internal_decimal','material_internal_decimal','regularization_internal_decimal','residual_decimal','material_energy_decimal')
        for field in precision_fields:
            error = decimal_error(hp[field],hp_high[field],floor,spec['reference_precision_check'])
            record_check(f'{case_id}:decimal50_80:{field}',error['relative_error'],spec['reference_precision_tolerance'])
        for field in ('internal_decimal','material_internal_decimal','regularization_internal_decimal'):
            for selection,indices in (('full',None),('free',reference.free)):
                with localcontext() as context:
                    context.prec = spec['reference_precision_check']
                    a,b = _selected(hp[field],indices),_selected(hp_high[field],indices)
                    absolute = decimal_norm([x-y for x,y in zip(a,b)],spec['reference_precision_check'])
                    relative = absolute/hp_high['force_scale_decimal']
                record_check(f'{case_id}:decimal50_80:{field}:{selection}:force_over_load',float(relative),spec['reference_precision_tolerance'],
                             absolute_error_decimal=str(absolute),error_over_load_norm_decimal=str(relative))
        j50,j80 = [x for row in hp['J_decimal'] for x in row],[x for row in hp_high['J_decimal'] for x in row]
        error = decimal_error(j50,j80,Decimal('1e-30'),spec['reference_precision_check'])
        record_check(f'{case_id}:decimal50_80:J',error['relative_error'],spec['reference_precision_tolerance'])
        modes = {}
        for tangent in (True,False):
            mode = 'tangent_true' if tangent else 'tangent_false'
            response = floating.response(u,tangent=tangent,assembly_diagnostic=True)
            modes[mode] = response
            mode_report = {}
            assembly_delta = response['internal']-response['fsum_internal']
            mode_report['assembly_diagnostic'] = dict(
                full_difference_norm=norm(assembly_delta),free_difference_norm=norm(assembly_delta[reference.free]),
                full_difference_over_load_norm=norm(assembly_delta)/float(scale),
                free_difference_over_load_norm=norm(assembly_delta[reference.free])/float(scale),
                maximum_absolute_difference=float(np.max(np.abs(assembly_delta))),gated=False,
                method='Same local binary64 force entries: production np.bincount versus independent per-DOF math.fsum')
            mode_report['J_diagnostic'] = j_diagnostic(response['J'],hp['J_decimal'],precision)
            mode_report['J_diagnostic']['gated'] = False
            raw[f'{case_id}_{mode}_fsum_internal'] = response['fsum_internal']
            for component,key in (('total','internal'),('material','material_internal'),('regularization','regularization_internal')):
                for selection,indices in (('full',None),('free',reference.free)):
                    error = compare_float_to_decimal(response[key],hp[key+'_decimal'],floor,indices=indices,precision=precision)
                    mode_report[f'{component}_{selection}'] = error
                    record_check(f'{case_id}:{mode}:{component}:{selection}:force',error['relative_error'],spec['component_force_tolerance'])
                raw[f'{case_id}_{mode}_{component}_internal'] = response[key]
            for selection in spec['force_budget_applies_to']:
                if selection not in ('full','free'):
                    raise ValueError('Unknown force budget DOF selection')
                indices = None if selection=='full' else reference.free
                budget = force_budget(response['internal'],hp['internal_decimal'],scale,indices,precision)
                record_check(f'{case_id}:{mode}:{selection}_force_arithmetic_budget',budget['error_over_load_norm'],spec['residual_force_budget'])
                mode_report[selection+'_force_arithmetic_budget'] = budget
            case['modes'][mode] = mode_report
        for selection in spec['force_budget_applies_to']:
            delta = modes['tangent_true']['internal']-modes['tangent_false']['internal']
            mode_delta = norm(delta if selection=='full' else delta[reference.free])/float(scale)
            record_check(f'{case_id}:true_false_{selection}_force_budget',mode_delta,spec['residual_force_budget'])
            case['true_false_'+selection+'_force_error_over_load_norm'] = mode_delta
        raw[f'{case_id}_hp_residual'] = hp['residual']
        raw[f'{case_id}_hp_J'] = hp['J']
        for component,key in (('total','internal'),('material','material_internal'),('regularization','regularization_internal')):
            raw[f'{case_id}_hp_{component}_internal_decimal'] = np.array([str(x) for x in hp[key+'_decimal']])
        if legacy is not None:
            legacy_modes = {}
            for tangent in (True,False):
                name = 'tangent_true' if tangent else 'tangent_false'
                response = legacy.response(u,tangent=tangent)
                legacy_modes[name] = response
                case['legacy'][name] = {
                    selection:force_budget(response['internal'],hp['internal_decimal'],scale,None if selection=='full' else reference.free,precision)
                    for selection in ('full','free')}
                case['legacy'][name]['J_diagnostic'] = j_diagnostic(response['J'],hp['J_decimal'],precision)
                raw[f'{case_id}_legacy_{name}_internal'] = response['internal']
            for selection in ('full','free'):
                delta = legacy_modes['tangent_true']['internal']-legacy_modes['tangent_false']['internal']
                case['legacy']['true_false_'+selection+'_force_error_over_load_norm'] = norm(delta if selection=='full' else delta[reference.free])/float(scale)
            case['legacy']['gated'] = False
        for direction_index,direction in enumerate(fixture['directions']):
            direction_id = spec['direction_ids'][direction_index]
            prefix = f'{case_id}_{direction_id}'
            hp_action = reference.evaluate(u,level,direction=direction)
            h0 = domain_step(hp_action,precision)
            raw[prefix+'_direction'] = direction
            for component,key in (('total','tangent_action'),('material','material_tangent_action'),('regularization','regularization_tangent_action')):
                actual = floating.response(u,tangent=True,component=component,direction=direction)['tangent_action']
                raw[prefix+'_'+component+'_Jv'] = actual
                raw[prefix+'_'+component+'_hp_Jv_decimal'] = np.array([str(x) for x in hp_action[key+'_decimal']])
                for selection,indices in (('full',None),('free',reference.free)):
                    error = compare_float_to_decimal(actual,hp_action[key+'_decimal'],floor,indices=indices,precision=precision)
                    record_check(f'{prefix}:{component}:{selection}:Jv',error['relative_error'],spec['directional_tolerance'])
            fd_decimal_errors,fd_float_errors = [],[]
            for step_index,multiplier in enumerate(spec['fd_multipliers']):
                h = float(h0*multiplier)
                plus,minus = u+h*direction,u-h*direction
                jp,jm = floating.determinants(plus),floating.determinants(minus)
                legal = bool(np.all(jp>=spec['positive_J_ratio']*hp['J']) and np.all(jm>=spec['positive_J_ratio']*hp['J']))
                record_check(f'{prefix}:step{step_index}:positive_J_domain',0. if legal else 1.,0.)
                tag = prefix+f'_step{step_index}'
                raw[tag+'_u_plus'],raw[tag+'_u_minus'] = plus,minus
                raw[tag+'_J_plus'],raw[tag+'_J_minus'] = jp,jm
                dhp = reference.evaluate(u,level,direction=direction,offset=h,derivative=False)
                dhm = reference.evaluate(u,level,direction=direction,offset=-h,derivative=False)
                with localcontext() as context:
                    context.prec = precision
                    denominator = 2*Decimal.from_float(h)
                    fd = [(a-b)/denominator for a,b in zip(dhp['internal_decimal'],dhm['internal_decimal'])]
                dec_error = decimal_error(fd,hp_action['tangent_action_decimal'],floor,precision)
                fd_decimal_errors.append(dec_error['relative_error'])
                raw[tag+'_hp_ideal_J_plus'],raw[tag+'_hp_ideal_J_minus'] = dhp['J'],dhm['J']
                raw[tag+'_hp_ideal_fd_decimal'] = np.array([str(x) for x in fd])
                row = dict(case_id=case_id,direction_id=direction_id,step_index=step_index,h0=h0,h=h,h_hex=h.hex(),
                           minimum_J_plus=float(jp.min()),minimum_J_minus=float(jm.min()),positive_J_domain=legal,
                           decimal_ideal_fd_error=dec_error['relative_error'],double_fd_error=None,
                           effective_direction_relative_difference=norm((plus-minus)/(2*h)-direction)/norm(direction),
                           midpoint_shift_norm=norm((plus/2+minus/2)-u))
                if legal:
                    rp,rm = floating.response(plus)['internal'],floating.response(minus)['internal']
                    fd_float = (rp-rm)/(2*h)
                    float_error = compare_float_to_decimal(fd_float,hp_action['tangent_action_decimal'],floor,precision=precision)
                    row['double_fd_error'] = float_error['relative_error']
                    fd_float_errors.append(float_error['relative_error'])
                    raw[tag+'_double_fd'] = fd_float
                curves.append(row)
            for name,errors,tolerance in (
                ('decimal',fd_decimal_errors,spec['fd_decimal_best_tolerance']),
                ('double',fd_float_errors,spec['fd_double_best_tolerance'])):
                complete = len(errors)==len(spec['fd_multipliers'])
                record_check(f'{prefix}:{name}:FD_complete',0. if complete else 1.,0.)
                if complete:
                    record_check(f'{prefix}:{name}:FD_best',min(errors),tolerance)
                    if errors[0]>spec['fd_early_applies_above']:
                        # Express required improvement as an upper-bound test.
                        record_check(f'{prefix}:{name}:FD_early_reduction',errors[1]/errors[0],1/spec['fd_early_reduction'])
            case.setdefault('directions',[]).append(dict(direction_id=direction_id,h0=h0,h0_hex=h0.hex(),
                step_rule='.99 min(1,J/(8|dJ|),sqrt(J/(8|det(dF)|))); zero terms omitted'))
        records.append(case)
        print('Finished fixed state',case_id,'elapsed',perf_counter()-started,flush=True)
    np.savez_compressed(output/'raw_precision_arrays.npz',**raw)
    with (output/'directional_error_curves.csv').open('w',encoding='utf-8',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(curves[0]))
        writer.writeheader()
        writer.writerows(curves)
    make_plot(curves,output)
    inputs = [Path(fixture_path),Path(spec_path),Path(__file__),Path(__file__).with_name('hf2_precision_reference.py'),Path(kernel.__file__)]
    if legacy_kernel is not None:
        inputs.append(Path(legacy_kernel))
    summary = dict(schema_version='hf2-fixed-state-precision-validation-1.0',status='pass' if all(c['status']=='pass' for c in checks) else 'not_pass',
        checks=checks,cases=records,directional_curves=curves,wall_seconds=perf_counter()-started,
        runtime=dict(jax_version=jax.__version__,x64_enabled=jax.config.x64_enabled,backend=jax.default_backend()),
        inputs_sha256={str(p.resolve()):digest(p) for p in inputs},
        scope='Frozen old states; no equilibrium acceptance for old U; no nonlinear path solve',
        direction_error_denominator='max(norm(Decimal reference vector),1e-8*norm(exact level*F0))',
        force_budget_denominator='norm(exact Decimal(level)*Decimal(F0)); unrounded HP force subtraction',
        fd_definition='Decimal uses ideal u+D(h)D(v); double uses saved rounded samples. Effective direction and midpoint shift retained.',
        component_semantics='Material and regularization Jv independently evaluated with kr=0 or lam=mu=0; total retains nonconservative HuHu.',
        legacy_semantics='Legacy errors are diagnostic only and never decide repaired precision gate')
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return summary


def make_plot(curves,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    groups = list(dict.fromkeys((r['case_id'],r['direction_id']) for r in curves))
    fig,axes = plt.subplots(3,2,figsize=(11,11))
    for axis,(case,direction) in zip(axes.ravel(),groups):
        rows = [r for r in curves if r['case_id']==case and r['direction_id']==direction]
        axis.loglog([r['h'] for r in rows],[r['decimal_ideal_fd_error'] for r in rows],'o-',label='Decimal ideal FD')
        valid = [r for r in rows if r['double_fd_error'] is not None]
        axis.loglog([r['h'] for r in valid],[r['double_fd_error'] for r in valid],'s-',label='binary64 rounded FD')
        axis.set_title(f'{case} / {direction}')
        axis.set_xlabel('Dimensionless step h')
        axis.set_ylabel('Relative Jv error')
        axis.grid(True,which='both',alpha=.25)
        axis.legend()
    fig.tight_layout()
    fig.savefig(output/'directional_error_curves.png',dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture',required=True)
    parser.add_argument('--spec',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--legacy-kernel')
    args = parser.parse_args()
    summary = validate(args.fixture,args.spec,args.output,args.legacy_kernel)
    print(json.dumps(dict(status=summary['status'],checks=len(summary['checks']),wall_seconds=summary['wall_seconds'])))
    raise SystemExit(0 if summary['status']=='pass' else 2)


if __name__=='__main__':
    main()
