"""Independent one-dimensional normal-contact references for HF-4.

Only Python's standard library is used. This module does not import the
production material, FE operators, solver, JAX, or a previous TMC reference.
The assumed motion is F=diag(1,s,1), with lateral displacement constrained.
The two elastic blocks have the SAME actual solid Lame coefficients. The
intervening material has its own supplied actual binary64 coefficients; no
gamma product is reconstructed. All dimensions are reference dimensions.

Positive d is the bottom platen's motion toward the fixed top platen. Positive
force_N is the compression magnitude, also the actuator's +y force on the
bottom of this model. The force of the model on that actuator has opposite
sign. These are full synthetic-specimen forces, with no implicit half factor.

For nonnegative lambda, positive mu and 0<s<=1:
    p(s) = mu*(1/s-s) - lambda*ln(s)/s
    p'(s) = -mu*(1+1/s**2) - lambda*(1-ln(s))/s**2 < 0.
With H=H1+H2 and total solid shortening x, the finite-medium root is
    p_s(1-x/H) - p_v(1-(d-x)/gap) = 0.
Its bracket is max(0,d-gap) <= x <= min(d,H), and the root function is
strictly increasing. Singular zero-stretch endpoints are never evaluated.
Pure bracket bisection provides a reproducible root without an FE oracle.

The hard-contact reference instead imposes the independent unilateral law:
zero force before closure, zero gap after closure. Comparing the finite-medium
and hard references measures a model difference, not FE or floating-point
error. This affine-layer test has zero element-interior HuHu and cannot
certify nonuniform two-dimensional contact or the effect of regularization.

All physical public inputs are promoted with Decimal.from_float. Results are
JSON-compatible dictionaries with authoritative Decimal strings. The module
has no pass/fail thresholds, file writes, command-line actions, or import-time
calculations. A caller must freeze comparison scales/tolerances separately.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import math
from numbers import Real


INPUT_NAMES = ("lam_s", "mu_s", "lam_v", "mu_v", "width", "H1", "H2",
               "gap", "thickness", "d")
_ZERO = Decimal(0)
_ONE = Decimal(1)
_TWO = Decimal(2)


def _precision(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 30:
        raise ValueError("precision must be an integer of at least 30 digits")
    return value


def _binary64(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real binary64-compatible scalar")
    try:
        result = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be finite") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _inputs(values):
    if set(values) != set(INPUT_NAMES):
        raise ValueError(f"input names must be exactly {INPUT_NAMES}")
    floats = {name: _binary64(values[name], name) for name in INPUT_NAMES}
    exact = {name: Decimal.from_float(value) for name, value in floats.items()}
    for name in ("lam_s", "lam_v", "d"):
        if exact[name] < 0:
            raise ValueError(f"{name} must be nonnegative")
    for name in ("mu_s", "mu_v", "width", "H1", "H2", "gap", "thickness"):
        if exact[name] <= 0:
            raise ValueError(f"{name} must be positive")
    # Exact conversion alone is not enough: addition must not inherit the
    # caller's possibly low Decimal context. Binary64 sums are finite decimal
    # expansions with at most 1074 fractional and 309 integer decimal places.
    with localcontext() as context:
        context.prec = 1500
        if exact["d"] >= exact["H1"]+exact["H2"]+exact["gap"]:
            raise ValueError("d must be below H1+H2+gap (positive total height)")
    return floats, exact


def compressive_nominal_stress(stretch, lam, mu):
    """Decimal constitutive formula, evaluated in the caller's context.

    This low-level formula intentionally accepts Decimal values only. Its
    monotonicity contract is restricted to compression, 0<stretch<=1; no
    global tension/inversion behavior is inferred from the compression proof.
    """
    values = (stretch, lam, mu)
    if not all(isinstance(value, Decimal) and value.is_finite() for value in values):
        raise ValueError("stretch, lam and mu must be finite Decimal values")
    if not _ZERO < stretch <= _ONE or lam < 0 or mu <= 0:
        raise ValueError("require 0<stretch<=1, lam>=0, mu>0")
    # Factoring 1-s*s avoids a needless subtraction of reciprocal terms.
    return (mu*(_ONE-stretch)*(_ONE+stretch)-lam*stretch.ln())/stretch


def _energy(stretch, lam, mu):
    log_s = stretch.ln()
    return lam*log_s*log_s/_TWO + mu*((stretch-_ONE)*(stretch+_ONE)-_TWO*log_s)/_TWO


def _rounded(value, precision):
    with localcontext() as context:
        context.prec = precision
        return +value


def _text(value, precision):
    # Normalize signed zero for stable ordinary-data records.
    value = _rounded(value, precision)
    return "0" if value == 0 else str(value)


def _finite_root(data, precision):
    H = data["H1"]+data["H2"]
    gap, d = data["gap"], data["d"]
    if d == 0:
        return _ZERO, _ZERO, _ZERO, 0
    lo, hi = max(_ZERO, d-gap), min(d, H)
    length_tolerance = (H+gap)*Decimal(1).scaleb(-precision-8)
    stress_tolerance = (data["lam_s"]+_TWO*data["mu_s"])*Decimal(1).scaleb(-precision-6)
    iterations = 0
    for iterations in range(1, 8*(precision+24)+129):
        x = (lo+hi)/_TWO
        if x == lo or x == hi:
            raise ArithmeticError("Decimal root bracket exhausted before accuracy criteria")
        solid_stretch = _ONE-x/H
        medium_stretch = _ONE-(d-x)/gap
        if not 0 < solid_stretch <= 1 or not 0 < medium_stretch <= 1:
            raise ArithmeticError("reference precision cannot resolve a positive layer stretch")
        mismatch = (compressive_nominal_stress(solid_stretch, data["lam_s"], data["mu_s"])
                    - compressive_nominal_stress(medium_stretch, data["lam_v"], data["mu_v"]))
        if mismatch == 0:
            return x, x, x, iterations
        if hi-lo <= length_tolerance and abs(mismatch) <= stress_tolerance:
            return x, lo, hi, iterations
        if mismatch < 0:
            lo = x
        else:
            hi = x
    raise ArithmeticError(f"monotone reference root did not converge after {iterations} iterations")


def _finite_response(data, precision):
    H, gap = data["H1"]+data["H2"], data["gap"]
    area = data["width"]*data["thickness"]
    x, lo, hi, iterations = _finite_root(data, precision)
    # Residuals below are recomputed from the stretch values actually exported,
    # rather than from hidden higher-precision iterates with smaller residuals.
    ss = _rounded(_ONE-x/H, precision)
    sv = _rounded(_ONE-(data["d"]-x)/gap, precision)
    ps = compressive_nominal_stress(ss, data["lam_s"], data["mu_s"])
    pv = compressive_nominal_stress(sv, data["lam_v"], data["mu_v"])
    length_residual = H*ss+gap*sv-(H+gap-data["d"])
    stress_residual = ps-pv
    solid_energy = area*H*_energy(ss, data["lam_s"], data["mu_s"])
    medium_energy = area*gap*_energy(sv, data["lam_v"], data["mu_v"])
    values = dict(force_N=area*ps, force_from_medium_N=area*pv,
                  p_nominal_MPa=ps, p_medium_MPa=pv, s_s=ss, s_v=sv,
                  gap_mm=gap*sv, solid_shortening_mm=H*(_ONE-ss),
                  length_residual_mm=length_residual,
                  traction_residual_MPa=stress_residual,
                  normalized_length_residual=abs(length_residual)/(H+gap),
                  normalized_traction_residual=abs(stress_residual)/(data["lam_s"]+_TWO*data["mu_s"]),
                  minimum_J=min(ss, sv),
                  material_energy_solid_Nmm=solid_energy,
                  material_energy_medium_Nmm=medium_energy,
                  material_energy_total_Nmm=solid_energy+medium_energy)
    response = {name: _text(value, precision) for name, value in values.items()}
    response.update(model="finite_medium", phase="reference" if data["d"] == 0 else "compressed_medium",
                    residual_basis="exported_decimal_stretch_ratios",
                    root=dict(method="monotone_bracket_bisection", iterations=iterations,
                              # Retain guard digits: rounding a certified
                              # bracket inward would invalidate its enclosure.
                              solid_shortening_lower_mm=str(lo),
                              solid_shortening_upper_mm=str(hi),
                              work_precision_digits=precision+24))
    return response


def _hard_response(data, precision):
    H, d, gap = data["H1"]+data["H2"], data["d"], data["gap"]
    area = data["width"]*data["thickness"]
    if d <= gap:
        ss, remaining_gap, p = _ONE, gap-d, _ZERO
        phase = "separated" if d < gap else "touching_zero_force"
    else:
        ss = _rounded(_ONE-(d-gap)/H, precision)
        remaining_gap = _ZERO
        p = compressive_nominal_stress(ss, data["lam_s"], data["mu_s"])
        phase = "compressed_contact"
    values = dict(force_N=area*p, p_nominal_MPa=p, s_s=ss,
                  gap_mm=remaining_gap, solid_shortening_mm=H*(_ONE-ss),
                  length_residual_mm=H*ss+remaining_gap-(H+gap-d),
                  complementarity_MPa_mm=p*remaining_gap, minimum_J_solid=ss,
                  material_energy_solid_Nmm=area*H*_energy(ss, data["lam_s"], data["mu_s"]))
    response = {name: _text(value, precision) for name, value in values.items()}
    response.update(model="ideal_unilateral_hard_contact", phase=phase)
    return response


def evaluate_normal_reference(*, lam_s, mu_s, lam_v, mu_v, width, H1, H2,
                              gap, thickness, d, precision=50):
    """Return finite-medium and ideal-contact references at one fixed d.

    Material inputs are actual MPa coefficients, dimensions/d are mm, and
    thickness is the actual out-of-plane thickness. Inputs are binary64
    compatible scalars; strings and Decimal physical inputs are rejected so
    that callers cannot accidentally change the input-promotion convention.
    There is deliberately no gamma, E, nu, mesh or regularization argument.
    The finite-medium result uses lam_v/mu_v exactly as supplied, even when
    their ratios to the solid coefficients are not exactly equal.
    """
    precision = _precision(precision)
    floats, exact = _inputs(dict(lam_s=lam_s, mu_s=mu_s, lam_v=lam_v, mu_v=mu_v,
                                 width=width, H1=H1, H2=H2, gap=gap,
                                 thickness=thickness, d=d))
    with localcontext() as context:
        context.prec = precision+24
        finite, hard = _finite_response(exact, precision), _hard_response(exact, precision)
        area = exact["width"]*exact["thickness"]
        force_scale = area*(exact["lam_s"]+_TWO*exact["mu_s"])
        length_scale = exact["H1"]+exact["H2"]+exact["gap"]
        return dict(schema_version="hf4-normal-reference-1.0", precision_digits=precision,
                    inputs=dict(binary64_hex={key: value.hex() for key, value in floats.items()},
                                decimal={key: str(value) for key, value in exact.items()}),
                    units=dict(length="mm", nominal_stress="MPa", force="N", energy="N mm"),
                    scales=dict(force_N=_text(force_scale, precision),
                                length_mm=_text(length_scale, precision),
                                note="reference cross-precision scales; not physical acceptance tolerances"),
                    finite_gamma=finite, hard_contact=hard,
                    interpretation=dict(force="positive compression; actuator on bottom specimen in +y",
                                        hard_contact="independent unilateral law; model discrepancy is not FE error",
                                        regularization="element-interior HuHu vanishes for affine layers",
                                        physical_validation="not_evaluated"))


def crosscheck_normal_reference(inputs, low_precision=50, high_precision=80):
    """Recompute independently at two precisions and return exact-string errors.

    No numerical or physical pass threshold is embedded. Dimensional errors
    and nonzero reference scales are retained for the caller's frozen spec.
    In particular, the hard-contact zero force is never a relative denominator.
    """
    low_precision, high_precision = _precision(low_precision), _precision(high_precision)
    if high_precision <= low_precision:
        raise ValueError("high_precision must exceed low_precision")
    _, exact = _inputs(dict(inputs))
    low = evaluate_normal_reference(**inputs, precision=low_precision)
    high = evaluate_normal_reference(**inputs, precision=high_precision)
    with localcontext() as context:
        context.prec = high_precision+24
        force_scale = exact["width"]*exact["thickness"]*(exact["lam_s"]+_TWO*exact["mu_s"])
        length_scale = exact["H1"]+exact["H2"]+exact["gap"]
        errors = {}
        for model in ("finite_gamma", "hard_contact"):
            entries = {}
            fields = ("force_N", "gap_mm", "s_s", "s_v") if model == "finite_gamma" else ("force_N", "gap_mm", "s_s")
            for field in fields:
                difference = abs(Decimal(low[model][field])-Decimal(high[model][field]))
                scale = force_scale if field == "force_N" else length_scale if field == "gap_mm" else _ONE
                entries[field] = dict(absolute_error=str(difference), scale=str(scale),
                                      normalized_error=str(difference/scale))
            errors[model] = entries
        return dict(schema_version="hf4-normal-crossprecision-1.0", low=low, high=high,
                    errors=errors, threshold_applied=False)
