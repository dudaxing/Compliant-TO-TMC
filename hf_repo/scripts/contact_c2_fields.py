"""Independent saved-field algebra; no production mechanics or AD imports.

Residuals use frozen volume quadrature primitives. Direct boundary projections
use the physical reference rectangle, thickness, and their own quadrature.
Their difference is a diagnostic, never an equality or a contact-law test.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from functools import lru_cache
from math import cos, pi

import numpy as np

from hf4_split_precision_reference import DecimalSplitQ1Reference

ZERO = Decimal(0)
ONE = Decimal(1)


def dec(value):
    return Decimal.from_float(float(value))


def flatten(value):
    if isinstance(value, (list, tuple)):
        return [item for row in value for item in flatten(row)]
    return [value]


def comparison(actual, reference, *, unit, precision=120, limit="1e-45"):
    """Norm error / max(norm(reference), one declared unit)."""
    a, b = flatten(actual), flatten(reference)
    if len(a) != len(b) or not a:
        raise ValueError("comparison shape mismatch or empty input")
    with localcontext() as ctx:
        ctx.prec = precision
        if any(not x.is_finite() for x in a+b):
            raise ValueError("nonfinite Decimal comparison")
        absolute = sum(((x-y)**2 for x, y in zip(a, b)), ZERO).sqrt()
        norm = sum((x*x for x in b), ZERO).sqrt()
        relative = absolute / max(norm, ONE)
        return dict(absolute_error=str(absolute), reference_norm=str(norm),
                    denominator=str(max(norm, ONE)), normalized_error=str(relative),
                    unit=unit, limit=limit, status="pass" if relative <= Decimal(limit) else "not_pass")


def shape_grad(xi, eta, hx, hy):
    n = [(ONE-xi)*(ONE-eta)/4, (ONE+xi)*(ONE-eta)/4,
         (ONE+xi)*(ONE+eta)/4, (ONE-xi)*(ONE+eta)/4]
    g = [[(eta-ONE)/(2*hx), (xi-ONE)/(2*hy)],
         [(ONE-eta)/(2*hx), -(ONE+xi)/(2*hy)],
         [(ONE+eta)/(2*hx), (ONE+xi)/(2*hy)],
         [-(ONE+eta)/(2*hx), (ONE-xi)/(2*hy)]]
    return n, g


def point_response(un, grad, lam, mu):
    F = [[(ONE if i == j else ZERO) + sum((un[a][i]*grad[a][j] for a in range(4)), ZERO)
          for j in range(2)] for i in range(2)]
    J = F[0][0]*F[1][1]-F[0][1]*F[1][0]
    if not J.is_finite() or J <= 0:
        raise ValueError("nonpositive/nonfinite J in saved-field reconstruction")
    inv_t = [[F[1][1]/J, -F[1][0]/J], [-F[0][1]/J, F[0][0]/J]]
    c = lam*J.ln()-mu
    P = [[mu*F[i][j]+c*inv_t[i][j] for j in range(2)] for i in range(2)]
    return F, J, P


@lru_cache(maxsize=16)
def gauss_legendre(order, precision):
    """Decimal Newton roots/weights; binary64 cosine supplies seeds only."""
    if order not in (8, 16, 32, 64):
        raise ValueError("only predeclared Gauss orders 8/16/32/64")
    with localcontext() as ctx:
        ctx.prec = precision + 12
        def polynomials(x):
            old, p = ONE, x
            for k in range(2, order+1):
                old, p = p, ((2*k-1)*x*p-(k-1)*old)/k
            derivative = order*(x*p-old)/(x*x-ONE)
            return p, derivative
        rows = []
        tolerance = Decimal(10) ** (-precision-5)
        for k in range(1, order//2+1):
            x = dec(cos(pi*(k-.25)/(order+.5)))
            for _ in range(32):
                p, dp = polynomials(x)
                step = p/dp
                x -= step
                if abs(step) <= tolerance:
                    break
            else:
                raise ArithmeticError("Gauss root Newton did not converge")
            _, dp = polynomials(x)
            weight = 2/((ONE-x*x)*dp*dp)
            rows.extend([(-x, weight), (x, weight)])
        return tuple(sorted(rows))


def reconstruct(fixture, lift, fluctuation, virtuals, *, precision=80, thickness=1.0):
    """Element residuals, direct top projection and virtual work from saved split.

    Virtual fields contain physical displacement components in mm. Volume
    virtual work is N mm. Top projections are the internal (+P N) sign;
    negate them when displaying the force exerted on the external plane.
    """
    ref = DecimalSplitQ1Reference(fixture, precision=precision)
    coords = np.asarray(fixture["coordinates"], dtype=float)
    top = set(map(int, fixture["top_nodes"]))
    solid = np.asarray(fixture["solid"], dtype=bool)
    if coords.shape != (ref.ndof//2, 2) or not np.all(np.isfinite(coords)):
        raise ValueError("invalid reference coordinates")
    L, w = np.asarray(lift), np.asarray(fluctuation)
    if L.shape != (ref.ndof,) or w.shape != L.shape or not np.all(np.isfinite(L)) or not np.all(np.isfinite(w)):
        raise ValueError("invalid split arrays")
    if not np.isfinite(thickness) or thickness <= 0:
        raise ValueError("invalid physical thickness")
    for name, v in virtuals.items():
        if np.shape(v) != L.shape or not np.all(np.isfinite(v)):
            raise ValueError("invalid virtual displacement: "+name)
    with localcontext() as ctx:
        ctx.prec = 3000
        u = [dec(a)+dec(b) for a,b in zip(L,w)]
        current = [[dec(coords[n,i])+u[2*n+i] for i in range(2)] for n in range(len(coords))]
    with localcontext() as ctx:
        ctx.prec = precision
        dv = {name: list(map(dec,v)) for name,v in virtuals.items()}
        material, regularization = [ZERO]*ref.ndof, [ZERO]*ref.ndof
        work = {name: dict(material=ZERO, regularization=ZERO) for name in virtuals}
        edges = {key: [ZERO]*ref.ndof for key in ("simpson3", "gauss8", "gauss16", "gauss32", "gauss64")}
        elements, edge_rows = [], []
        rules = {"simpson3": ((-ONE, ONE/3), (ZERO, Decimal(4)/3), (ONE, ONE/3))}
        rules.update({"gauss"+str(n): gauss_legendre(n, precision) for n in (8,16,32,64)})
        for e, conn in enumerate(ref.connectivity):
            cn = list(map(int,conn))
            xy = coords[cn]
            hx, hy = dec(xy[1,0])-dec(xy[0,0]), dec(xy[3,1])-dec(xy[0,1])
            if hx <= 0 or hy <= 0 or not np.array_equal(xy, np.array([[xy[0,0],xy[0,1]],
                    [xy[1,0],xy[0,1]], [xy[1,0],xy[3,1]], [xy[0,0],xy[3,1]]])):
                raise ValueError("diagnostic supports canonical axis-aligned Q4 reference cells only")
            # Avoid silently applying rectangular boundary gradients to a different
            # volume interpolation. Saved binary64 operator arithmetic is retained.
            for q,(xi,eta) in enumerate(( (x,y) for x in (-ONE,ZERO,ONE) for y in (-ONE,ZERO,ONE) )):
                _, expected_grad = shape_grad(xi,eta,hx,hy)
                if any(float(expected_grad[a][j]) != ref.grad[q,a,j] for a in range(4) for j in range(2)):
                    raise ValueError("saved gradients do not match reference rectangle")
            un = [[u[2*n+i] for i in range(2)] for n in cn]
            Hu = [[[sum((un[a][i]*ref.dh[a][j][k] for a in range(4)),ZERO)
                    for k in range(2)] for j in range(2)] for i in range(2)]
            Au = [[sum((ref.dh[a][j][k]*Hu[i][j][k] for j in range(2) for k in range(2)),ZERO)
                   for i in range(2)] for a in range(4)]
            em, er = [[ZERO]*2 for _ in cn], [[ZERO]*2 for _ in cn]
            vlocal = {name:[[v[2*n+i] for i in range(2)] for n in cn] for name,v in dv.items()}
            Hv = {name:[[[sum((vn[a][i]*ref.dh[a][j][k] for a in range(4)),ZERO)
                         for k in range(2)] for j in range(2)] for i in range(2)] for name,vn in vlocal.items()}
            points = []
            for q in range(9):
                F,J,P = point_response(un,ref.dg[q],ref.dlam[e],ref.dmu[e])
                coefficient = ref.dk*(-5*J).exp()
                for a in range(4):
                    for i in range(2):
                        em[a][i] += ref.dw[q]*sum((P[i][j]*ref.dg[q][a][j] for j in range(2)),ZERO)
                        er[a][i] += ref.dw[q]*coefficient*Au[a][i]
                for name,vn in vlocal.items():
                    gradv = [[sum((vn[a][i]*ref.dg[q][a][j] for a in range(4)),ZERO) for j in range(2)] for i in range(2)]
                    work[name]["material"] += ref.dw[q]*sum((P[i][j]*gradv[i][j] for i in range(2) for j in range(2)),ZERO)
                    work[name]["regularization"] += ref.dw[q]*coefficient*sum((Hu[i][j][k]*Hv[name][i][j][k] for i in range(2) for j in range(2) for k in range(2)),ZERO)
                xi, eta = (-ONE,ZERO,ONE)[q//3], (-ONE,ZERO,ONE)[q%3]
                n,_ = shape_grad(xi,eta,hx,hy)
                xc = [sum((n[a]*current[cn[a]][i] for a in range(4)),ZERO) for i in range(2)]
                points.append(dict(xi=xi,eta=eta,F=F,J=J,P=P,current_coordinate_mm=xc))
            for a,n in enumerate(cn):
                for i in range(2):
                    material[2*n+i] += em[a][i]
                    regularization[2*n+i] += er[a][i]
            row = dict(element=e,connectivity=cn,solid=bool(solid[e]),Hu=Hu,
                       material_internal_N=em,regularization_internal_N=er,quadrature=points)
            elements.append(row)
            if cn[2] in top and cn[3] in top:
                edge = dict(element=e,minimum_J={},maximum_J={},normal_Pyy_range={},projection={},endpoints=[])
                for key, rule in rules.items():
                    local = [[ZERO]*2 for _ in cn]
                    js, pyys = [], []
                    for xi,weight in rule:
                        n,g = shape_grad(xi,ONE,hx,hy)
                        F,J,P = point_response(un,g,ref.dlam[e],ref.dmu[e])
                        if key=="simpson3" and abs(xi)==ONE:
                            edge["endpoints"].append(dict(xi=xi,F=F,J=J,P=P))
                        js.append(J); pyys.append(P[1][1])
                        for a in (2,3):
                            for i in range(2):
                                local[a][i] += dec(thickness)*hx/2*weight*n[a]*P[i][1]
                    for a in (2,3):
                        for i in range(2):
                            edges[key][2*cn[a]+i] += local[a][i]
                    edge["minimum_J"][key],edge["maximum_J"][key] = min(js),max(js)
                    edge["normal_Pyy_range"][key] = [min(pyys),max(pyys)]
                    edge["projection"][key] = local
                left,right=edge["endpoints"]
                conditions=dict(nonnegative_lam_positive_mu=ref.dlam[e]>=0 and ref.dmu[e]>0,
                    flat_top_Fyx_zero=left["F"][1][0]==0 and right["F"][1][0]==0,
                    positive_constant_Fxx=left["F"][0][0]==right["F"][0][0] and left["F"][0][0]>0,
                    positive_endpoint_Fyy=left["F"][1][1]>0 and right["F"][1][1]>0,
                    negative_endpoint_Pyy=left["P"][1][1]<0 and right["P"][1][1]<0)
                edge["full_edge_material_compression_certificate"]=dict(conditions=conditions,
                    certified=all(conditions.values()),
                    argument="For a flat Q1 top, Fxx is constant, Fyx=0 and Fyy is affine. Pyy*Fyy=mu*(Fyy^2-1)+lam*ln(Fxx*Fyy) increases with positive Fyy. Negative endpoint Pyy proves negative Pyy throughout this element top edge; this is material nominal stress, not a unilateral contact law.")
                edge_rows.append(edge)
        total = [a+b for a,b in zip(material,regularization)]
        identities = {}
        for name,v in dv.items():
            nodal = {key:sum((x*y for x,y in zip(v,array)),ZERO) for key,array in
                     (("material",material),("regularization",regularization),("total",total))}
            work[name]["total"] = work[name]["material"]+work[name]["regularization"]
            identities[name] = dict(nodal_N_mm=nodal,integrated_N_mm=work[name],
                checks={key:comparison([nodal[key]],[work[name][key]],unit="N mm",precision=precision)
                        for key in nodal})
        return dict(material=material,regularization=regularization,total=total,elements=elements,
                    edge_projections=edges,edge_elements=edge_rows,virtual_work=identities,
                    current=current,physical_displacement=u)
