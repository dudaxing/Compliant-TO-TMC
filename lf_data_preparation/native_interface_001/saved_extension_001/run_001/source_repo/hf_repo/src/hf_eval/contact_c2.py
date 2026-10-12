"""Uniform-only one-factor C2 diagnostic models; original C1 stays frozen."""
from dataclasses import dataclass
import numpy as np

from .split_state import SplitDisplacement
from .tmc import TMCModel


CASES = {
    "baseline_h0125": (0.125, 2.0, "driven"),
    "mesh_h00625": (0.0625, 2.0, "driven"),
    "padding_2p5": (0.125, 2.5, "driven"),
    "outer_free": (0.125, 2.0, "free"),
}


@dataclass(frozen=True)
class C2Problem:
    model: TMCModel
    arrays: dict
    groups: dict
    initial_state: SplitDisplacement
    targets: np.ndarray


def build_problem(case_id):
    if case_id not in CASES:
        raise ValueError("undeclared C2 diagnostic case")
    h, padding, policy = CASES[case_id]
    xmin, xmax, height = -padding, 2.0 + padding, 1.25
    nx, ny = int((xmax-xmin)/h), int(height/h)
    xx, yy = np.meshgrid(xmin + h*np.arange(nx+1), h*np.arange(ny+1))
    coordinates = np.column_stack((xx.ravel(), yy.ravel()))
    ll = (np.arange(ny)[:, None]*(nx+1) + np.arange(nx)).ravel()
    cells = ll[:, None] + np.array([0, 1, nx+2, nx+1])
    centre = coordinates[cells].mean(axis=1)
    solid = (centre[:, 0] > 0) & (centre[:, 0] < 2) & (centre[:, 1] < 1)
    E, nu = 100.0, 0.3
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    factor = np.where(solid, 1.0, 1e-6)
    kr = 1e-6*2.0**2*(E/(3*(1-2*nu)) + 4*mu/3)
    bottom = np.arange(nx+1, dtype=np.int64)
    top = ny*(nx+1) + bottom
    body = bottom[(coordinates[bottom, 0] >= 0) & (coordinates[bottom, 0] <= 2)]
    anchor = bottom[coordinates[bottom, 0] == 1.0].item()
    driven = bottom if policy == "driven" else body
    fixed = np.sort(np.r_[2*driven+1, 2*top+1, 2*anchor])
    model = TMCModel(coordinates, cells, lam*factor, mu*factor, kr, h, h, 1., solid, fixed)
    shape, direction = np.zeros(model.ndof), np.zeros(model.ndof)
    y = coordinates[:, 1]
    shape[1::2] = np.where(y <= 1., 1., 4*(1.25-y))
    direction[fixed] = shape[fixed]
    groups = {"top": np.zeros(model.ndof), "bottom": np.zeros(model.ndof)}
    groups["top"][2*top+1] = 1.
    groups["bottom"][2*driven+1] = 1.
    def mean(nodes, length):
        value = np.zeros(model.ndof)
        value[2*nodes+1] = h/length
        value[2*nodes[[0, -1]]+1] *= .5
        return value
    arrays = dict(coordinates=model.coordinates, connectivity=model.connectivity,
                  lam=model.lam, mu=model.mu, kr=np.asarray(model.kr),
                  fixed_dofs=model.fixed_dofs, solid=model.solid, F0=np.zeros(model.ndof),
                  base=np.zeros(model.ndof), direction=direction,
                  lift_origin=np.zeros(model.ndof), lift_shape=shape,
                  top_nodes=top, bottom_nodes=bottom, bottom_body_nodes=body,
                  measure_bottom_body=mean(body, 2.), measure_bottom_total=mean(bottom, xmax-xmin),
                  **{"group_"+name: value for name, value in groups.items()},
                  **{name: model.ops[name] for name in ("grad", "hessian", "weights")})
    return C2Problem(model, arrays, groups,
                     SplitDisplacement(np.zeros(model.ndof), np.zeros(model.ndof)),
                     np.array([0., .125, .21875, .25, .28125, .375, .5]))
