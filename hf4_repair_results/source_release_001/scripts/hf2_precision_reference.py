"""Independent Decimal reference for the fixed HF-2 Q1 weak residual.

This development helper imports no production kernel, automatic differentiation,
MATLAB, or LF code. Every input float is promoted with Decimal.from_float: it
evaluates the exact binary64 input values, not independently rounded physical
parameters. Quadrature weights include thickness. Both mixed Hessian entries
are retained. The direction derivative is analytic and is not an energy Hessian.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import numpy as np


def _real(value, name, shape=None):
    raw = np.asarray(value)
    if raw.dtype.kind not in 'iuf' or np.iscomplexobj(raw):
        raise ValueError(f'{name} must be a real numeric array')
    result = np.array(raw, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(result)):
        raise ValueError(f'{name} must be finite')
    if shape is not None and result.shape != shape:
        raise ValueError(f'{name} must have shape {shape}')
    return result


def _d(value):
    return Decimal.from_float(float(value))


def decimal_norm(values, precision=50):
    """Euclidean norm of Decimal values; no intermediate float conversion."""
    with localcontext() as context:
        context.prec = precision
        return sum((x*x for x in values), Decimal(0)).sqrt()


def compare_float_to_decimal(actual, reference, floor, *, indices=None, precision=50):
    """Compare a binary64 vector with an unrounded Decimal reference vector.

    `floor` is a Decimal or scalar in the same force units. The denominator is
    max(norm(reference), floor). `indices` selects full or free DOFs identically
    on both vectors. Decimal strings retain the high-precision error evidence.
    """
    actual = _real(actual, 'actual').ravel()
    if len(actual) != len(reference):
        raise ValueError('actual and reference vector lengths differ')
    selected = range(len(actual)) if indices is None else list(indices)
    with localcontext() as context:
        context.prec = precision
        target = [reference[i] for i in selected]
        error = [_d(actual[i])-reference[i] for i in selected]
        absolute = decimal_norm(error, precision)
        reference_norm = decimal_norm(target, precision)
        floor = floor if isinstance(floor, Decimal) else _d(floor)
        denominator = max(reference_norm, floor)
        if denominator <= 0:
            raise ValueError('comparison denominator must be positive')
        relative = absolute/denominator
        return dict(absolute_error=float(absolute), reference_norm=float(reference_norm),
                    denominator=float(denominator), relative_error=float(relative),
                    absolute_error_decimal=str(absolute), relative_error_decimal=str(relative))


class DecimalQ1Reference:
    """Frozen-operator Q1 reference with independently derived force/Jv.

    Fixture keys: grad(9,4,2), hessian(4,2,2), weights(9), lam(ne), mu(ne),
    kr scalar, connectivity(ne,4), F0(ndof), fixed_dofs(integer vector).
    Additional fixture keys are ignored. Arrays are copied on construction.

    evaluate(u, load_multiplier, direction=None, offset=0.0, derivative=True) evaluates the
    ideal Decimal state D(u)+D(offset)*D(direction). A nonzero offset requires
    direction. If supplied, direction also requests the analytic derivative
    with respect to its dimensionless multiplier at that evaluation state.
    Set keyword-only derivative=False to skip that derivative during ideal
    finite-difference residual evaluations; direction still defines the offset.

    Returned *_decimal lists are the authoritative force vectors. Float arrays
    are convenience views only. `residual` is rounded AFTER high-precision
    subtraction of the exact product D(load_multiplier)*D(F0), never formed by
    subtracting rounded internal forces. `relative_residual` is a Decimal string.
    All outputs are ordinary Python/NumPy values; this class never writes files.
    """

    def __init__(self, fixture: dict, precision=50):
        if isinstance(precision, bool) or not isinstance(precision, int) or precision < 30:
            raise ValueError('precision must be an integer of at least 30 digits')
        self.precision = precision
        self.grad = _real(fixture['grad'], 'grad', (9,4,2))
        self.hessian = _real(fixture['hessian'], 'hessian', (4,2,2))
        self.weights = _real(fixture['weights'], 'weights', (9,))
        if np.any(self.weights <= 0):
            raise ValueError('quadrature weights must be positive')
        conn = np.asarray(fixture['connectivity'])
        if conn.dtype.kind not in 'iu' or conn.ndim != 2 or conn.shape[1] != 4 or len(conn)==0:
            raise ValueError('connectivity must be a nonempty integer (ne,4) array')
        self.connectivity = conn.astype(np.int64, copy=True)
        self.ne = len(conn)
        self.F0 = _real(fixture['F0'], 'F0')
        if self.F0.ndim != 1 or len(self.F0)==0 or len(self.F0)%2:
            raise ValueError('F0 must be a nonempty even-length vector')
        self.ndof = len(self.F0)
        if np.any(conn < 0) or np.any(conn >= self.ndof//2):
            raise ValueError('connectivity contains an out-of-range node')
        if any(len(set(row)) != 4 for row in self.connectivity):
            raise ValueError('each Q1 element must have four distinct nodes')
        fixed = np.asarray(fixture['fixed_dofs'])
        if fixed.dtype.kind not in 'iu' or fixed.ndim != 1:
            raise ValueError('fixed_dofs must be an integer vector')
        if np.any(fixed < 0) or np.any(fixed >= self.ndof) or len(np.unique(fixed)) != len(fixed):
            raise ValueError('fixed_dofs contains repeated or out-of-range indices')
        self.fixed = fixed.astype(np.int64,copy=True)
        self.free = np.setdiff1d(np.arange(self.ndof),self.fixed)
        self.lam = _real(fixture['lam'], 'lam', (self.ne,))
        self.mu = _real(fixture['mu'], 'mu', (self.ne,))
        kr = _real(fixture['kr'], 'kr', ())
        if float(kr) < 0 or np.any(self.mu < 0) or np.any(self.lam+2*self.mu/3 < 0):
            raise ValueError('material shear/bulk moduli and kr must be nonnegative')
        self.kr = float(kr)
        self.dg = [[[_d(x) for x in row] for row in point] for point in self.grad]
        self.dh = [[[_d(x) for x in row] for row in node] for node in self.hessian]
        self.dw = [_d(x) for x in self.weights]
        self.dlam, self.dmu = [_d(x) for x in self.lam],[_d(x) for x in self.mu]
        self.dk = _d(self.kr)
        self.df0 = [_d(x) for x in self.F0]

    def evaluate(self, u, load_multiplier, direction=None, offset=0.0, *, derivative=True):
        u = _real(u, 'u', (self.ndof,))
        level = _real(load_multiplier, 'load_multiplier', ())
        offset = _real(offset, 'offset', ())
        if not isinstance(derivative, (bool,np.bool_)):
            raise ValueError('derivative must be boolean')
        if direction is None and float(offset) != 0:
            raise ValueError('nonzero offset requires a direction')
        v = None if direction is None else _real(direction, 'direction', (self.ndof,))
        with localcontext() as context:
            context.prec = self.precision
            zero, one, two = Decimal(0),Decimal(1),Decimal(2)
            du = [_d(x) for x in u]
            dv = None if v is None else [_d(x) for x in v]
            if dv is not None and float(offset) != 0:
                step = _d(offset)
                du = [a+step*b for a,b in zip(du,dv)]
            action_direction = dv if derivative else None
            material, regularization = [zero]*self.ndof,[zero]*self.ndof
            dmaterial, dregularization = [zero]*self.ndof,[zero]*self.ndof
            all_J, all_dJ, all_det_dF, energy = [],[],[],[]
            for e, conn in enumerate(self.connectivity):
                un = [[du[2*a+i] for i in range(2)] for a in conn]
                vn = None if action_direction is None else [[action_direction[2*a+i] for i in range(2)] for a in conn]
                Hu = [[[sum((un[a][i]*self.dh[a][j][k] for a in range(4)),zero)
                        for k in range(2)] for j in range(2)] for i in range(2)]
                Au = [[sum((self.dh[a][j][k]*Hu[i][j][k] for j in range(2) for k in range(2)),zero)
                       for i in range(2)] for a in range(4)]
                if vn is not None:
                    Hv = [[[sum((vn[a][i]*self.dh[a][j][k] for a in range(4)),zero)
                            for k in range(2)] for j in range(2)] for i in range(2)]
                    Av = [[sum((self.dh[a][j][k]*Hv[i][j][k] for j in range(2) for k in range(2)),zero)
                           for i in range(2)] for a in range(4)]
                ej, edj, edet = [],[],[]
                energy_e = zero
                for q in range(9):
                    grad = self.dg[q]
                    F = [[(one if i==j else zero)+sum((un[a][i]*grad[a][j] for a in range(4)),zero)
                          for j in range(2)] for i in range(2)]
                    J = F[0][0]*F[1][1]-F[0][1]*F[1][0]
                    if not J.is_finite() or J <= 0:
                        raise ValueError(f'Nonpositive or nonfinite J at element {e}, quadrature {q}')
                    ej.append(J)
                    T = [[F[1][1]/J,-F[1][0]/J],[-F[0][1]/J,F[0][0]/J]]
                    logJ = J.ln()
                    c = self.dlam[e]*logJ-self.dmu[e]
                    P = [[self.dmu[e]*F[i][j]+c*T[i][j] for j in range(2)] for i in range(2)]
                    reg = self.dk*self.dw[q]*(-5*J).exp()
                    energy_e += self.dw[q]*(self.dlam[e]*logJ**2+self.dmu[e]*(sum((x*x for row in F for x in row),zero)-two-two*logJ))/two
                    if vn is not None:
                        dF = [[sum((vn[a][i]*grad[a][j] for a in range(4)),zero)
                               for j in range(2)] for i in range(2)]
                        dJ = F[1][1]*dF[0][0]+F[0][0]*dF[1][1]-F[1][0]*dF[0][1]-F[0][1]*dF[1][0]
                        det_dF = dF[0][0]*dF[1][1]-dF[0][1]*dF[1][0]
                        dT = [[-sum((T[i][k]*dF[l][k]*T[l][j] for k in range(2) for l in range(2)),zero)
                               for j in range(2)] for i in range(2)]
                        dP = [[self.dmu[e]*dF[i][j]+self.dlam[e]*dJ/J*T[i][j]+c*dT[i][j]
                               for j in range(2)] for i in range(2)]
                        edj.append(dJ)
                        edet.append(det_dF)
                    for a, node in enumerate(conn):
                        for i in range(2):
                            dof = 2*node+i
                            material[dof] += self.dw[q]*sum((P[i][j]*grad[a][j] for j in range(2)),zero)
                            regularization[dof] += reg*Au[a][i]
                            if vn is not None:
                                dmaterial[dof] += self.dw[q]*sum((dP[i][j]*grad[a][j] for j in range(2)),zero)
                                dregularization[dof] += reg*(Av[a][i]-5*dJ*Au[a][i])
                all_J.append(ej)
                energy.append(energy_e)
                if vn is not None:
                    all_dJ.append(edj)
                    all_det_dF.append(edet)
            internal = [a+b for a,b in zip(material,regularization)]
            external = [_d(level)*x for x in self.df0]
            residual = [a-b for a,b in zip(internal,external)]
            force_scale = decimal_norm(external,self.precision)
            scale_reason = 'norm(load_multiplier*F0)'
            if force_scale == 0:
                force_scale = decimal_norm(self.df0,self.precision)
                scale_reason = 'zero load: norm(F0)'
            if force_scale == 0:
                force_scale,scale_reason = one,'zero F0: diagnostic unit scale'
            relative = decimal_norm([residual[i] for i in self.free],self.precision)/force_scale
            result = dict(internal=np.array(internal,dtype=np.float64),residual=np.array(residual,dtype=np.float64),
                J=np.array(all_J,dtype=np.float64),material_energy=np.array(energy,dtype=np.float64),
                relative_residual=str(relative),minimum_J=str(min(x for row in all_J for x in row)),
                force_scale_decimal=force_scale,relative_residual_scale_reason=scale_reason,
                internal_decimal=internal,residual_decimal=residual,external_decimal=external,
                material_internal=np.array(material,dtype=np.float64),regularization_internal=np.array(regularization,dtype=np.float64),
                material_internal_decimal=material,regularization_internal_decimal=regularization,
                J_decimal=all_J,material_energy_decimal=energy)
            if vn is not None:
                action = [a+b for a,b in zip(dmaterial,dregularization)]
                result.update(tangent_action=np.array(action,dtype=np.float64),
                    material_tangent_action=np.array(dmaterial,dtype=np.float64),regularization_tangent_action=np.array(dregularization,dtype=np.float64),
                    tangent_action_decimal=action,material_tangent_action_decimal=dmaterial,
                    regularization_tangent_action_decimal=dregularization,
                    dJ_decimal=all_dJ,det_dF_decimal=all_det_dF)
            return result
