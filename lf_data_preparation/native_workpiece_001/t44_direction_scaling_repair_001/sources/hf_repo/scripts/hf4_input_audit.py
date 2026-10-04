"""Independent ordinary-data binding of a saved HF-4 model to its frozen task.

No production FE, task adapter or AD code is imported. Coordinates,
connectivity, layer labels, constraints and Q1 Lobatto operators are tabulated
directly from the specified physical problem. Validation never substitutes
the expected arrays for the saved primitives used by the Decimal reference.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json

import numpy as np


def _canonical(value):
    """Independent implementation of the documented float.hex JSON identity."""
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("metadata object keys must be strings")
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            raise ValueError("nonfinite metadata number")
        return (0.0 if number == 0 else number).hex()
    if isinstance(value, np.integer):
        return int(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise ValueError("metadata must contain ordinary JSON-compatible values")


def _identity(value):
    return sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _tabulated_operators(h, thickness):
    # N_a=(1+sx*xi)(1+sy*eta)/4, physical dx/dxi=dy/deta=h/2.
    # The tensor Lobatto rule has integer numerator weights 1,4,1 over 3.
    signs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    points, gradients, weights = [], [], []
    for xi, wx in ((-1.0, 1), (0.0, 4), (1.0, 1)):
        for eta, wy in ((-1.0, 1), (0.0, 4), (1.0, 1)):
            points.append([xi, eta])
            gradients.append([[sx*(1+sy*eta)/(2*h), sy*(1+sx*xi)/(2*h)] for sx, sy in signs])
            # With the frozen dyadic geometry and numerator powers of two,
            # multiplying before /36 has the same binary64 rounding as the
            # production /36 followed by numerator multiplication.
            weights.append((wx*wy)*h*h*thickness/36)
    hessian = np.zeros((4, 2, 2), dtype=np.float64)
    for a, (sx, sy) in enumerate(signs):
        hessian[a, 0, 1] = hessian[a, 1, 0] = sx*sy/(h*h)
    return dict(points=np.array(points), grad=np.array(gradients),
                hessian=hessian, weights=np.array(weights))


def validate_inputs(spec, meta, m, source_freeze=None):
    """Return serializable successful checks, or raise ValueError on mismatch.

    ``spec`` is the caller's frozen JSON document, ``meta`` is metadata.json,
    and ``m`` is a dictionary of actual model.npz arrays. The caller separately
    binds the bytes of these files and this script. No files are opened here.
    ``source_freeze`` optionally contains ``files`` mapping relative paths to
    SHA256 strings. Its src/hf_eval/*.py subset must match the corresponding
    metadata.source_files subset exactly; development scripts are not runtime
    source. An omitted freeze is recorded explicitly as not_requested.

    The test is exact in array shape, discrete ordering and binary64 values.
    This scope requires the frozen dyadic h and physical lengths. It does not
    introduce tolerances, run a solve, evaluate forces or alter input arrays.
    """
    if not all(isinstance(value, Mapping) for value in (spec, meta, m)):
        raise ValueError("spec, meta and m must be mappings")
    checks = []

    def check(name, passed, detail=None):
        if not bool(passed):
            raise ValueError("HF4 input binding failed: "+name)
        row = dict(name=name, status="pass")
        if detail is not None:
            row["detail"] = detail
        checks.append(row)

    def same_json(name, actual, expected):
        check(name, _canonical(actual) == _canonical(expected))

    def array(name, expected, kind="real"):
        check("present_"+name, name in m)
        actual = np.asarray(m[name])
        expected = np.asarray(expected)
        check("shape_"+name, actual.shape == expected.shape, list(expected.shape))
        allowed = "iu" if kind == "integer" else "biu" if kind == "binary" else "f"
        check("dtype_"+name, actual.dtype.kind in allowed and
              (kind != "real" or actual.dtype.itemsize == 8), str(actual.dtype))
        check("finite_"+name, np.all(np.isfinite(actual)))
        check("values_"+name, np.array_equal(actual, expected))

    try:
        same_json("embedded_spec", meta["spec"], spec)
        for field, values in (("gamma_index", spec["gammas"]), ("mesh_index", spec["mesh_sizes_mm"])):
            index = meta[field]
            check(field, not isinstance(index, bool) and isinstance(index, (int, np.integer))
                  and 0 <= index < len(values))
        gamma = float(spec["gammas"][meta["gamma_index"]])
        h = float(spec["mesh_sizes_mm"][meta["mesh_index"]])
        geom = {key: float(value) for key, value in spec["geometry"].items()}
        material = spec["material"]
        E, nu = float(material["E_MPa"]), float(material["nu"])
        alpha, length = (float(spec["regularization"][name]) for name in ("alpha", "length_mm"))
        check("physical_parameter_domain", 0 < gamma <= 1 and h > 0 and E > 0
              and 0 <= nu < .5 and alpha >= 0 and length > 0 and all(value > 0 for value in geom.values())
              and material["formulation"] == "plane_strain")
        units = dict(length="mm", force="N", stress="MPa", energy="N mm")
        expected_task = dict(schema_version="hf-normal-contact-task-1.0", units=units,
            geometry=deepcopy(spec["geometry"]), material=deepcopy(material),
            gamma=spec["gammas"][meta["gamma_index"]], regularization=deepcopy(spec["regularization"]),
            mesh_size_mm=spec["mesh_sizes_mm"][meta["mesh_index"]], targets_mm=list(spec["targets_mm"]),
            constraints=dict(ux="all_zero", top_uy="zero", bottom_uy="d"))
        same_json("task_from_frozen_spec", meta["task"], expected_task)
        same_json("solver_settings", meta["settings"], spec["solver"])
        check("task_sha256", meta["task_sha256"] == _identity(expected_task))
        same_json("force_scale_per_length", meta["force_scale_per_length"], E*geom["thickness_mm"])

        counts = []
        for key in ("width_mm", "lower_height_mm", "gap_mm", "upper_height_mm"):
            ratio = geom[key]/h
            check("integer_cells_"+key, np.isfinite(ratio) and ratio == int(ratio)
                  and int(ratio) > 0 and int(ratio)*h == geom[key])
            counts.append(int(ratio))
        nx, nlow, ngap, nup = counts
        ny = nlow+ngap+nup
        check("bounded_fixture_size", nx*ny <= 100000)
        # Require h to be a power of two for this frozen exact-geometry audit.
        mantissa, _ = np.frexp(h)
        check("dyadic_grid_spacing", mantissa == .5)
        coordinates = np.array([[ix*h, iy*h] for iy in range(ny+1) for ix in range(nx+1)])
        connectivity, labels = [], []
        for iy in range(ny):
            for ix in range(nx):
                first = iy*(nx+1)+ix
                connectivity.append([first, first+1, first+nx+2, first+nx+1])
                labels.append(1 if iy < nlow else 0 if iy < nlow+ngap else 2)
        labels = np.array(labels, dtype=np.int64)
        ne, nn = nx*ny, (nx+1)*(ny+1)
        ndof = 2*nn
        array("coordinates", coordinates)
        array("connectivity", np.array(connectivity), "integer")
        array("body_ids", labels, "integer")
        array("solid", labels != 0, "binary")
        for name, value in (("hx", h), ("hy", h), ("thickness", geom["thickness_mm"])):
            array(name, np.array(value))
        identity = dict(schema_version="hf-normal-geometry-1.0", units=units, geometry=geom)
        mesh = dict(geometry=identity, hx=h, hy=h, nx=nx, ny=ny, ordering="x_fast_bottom_up_BL_BR_TR_TL")
        check("geometry_id", meta["geometry_id"] == _identity(identity))
        check("mesh_id", meta["mesh_id"] == _identity(mesh))

        lam_s = E*nu/((1+nu)*(1-2*nu))
        mu_s = E/(2*(1+nu))
        lam_v, mu_v = lam_s*gamma, mu_s*gamma
        array("lam", np.array([lam_s if body else lam_v for body in labels]))
        array("mu", np.array([mu_s if body else mu_v for body in labels]))
        expected_kr = alpha*length**2*(E/(3*(1-2*nu))+4*mu_s/3)
        array("kr", np.array(expected_kr))
        for name, expected in _tabulated_operators(h, geom["thickness_mm"]).items():
            array(name, expected)

        bottom = list(range(nx+1))
        top = list(range(ny*(nx+1), nn))
        lower = list(range(nlow*(nx+1), (nlow+1)*(nx+1)))
        upper = list(range((nlow+ngap)*(nx+1), (nlow+ngap+1)*(nx+1)))
        fixed = np.array(sorted(set(range(0, ndof, 2)) | {2*n+1 for n in bottom+top}))
        array("fixed_dofs", fixed, "integer")
        base, direction, top_motion = np.zeros(ndof), np.zeros(ndof), np.zeros(ndof)
        direction[[2*n+1 for n in bottom]] = 1
        top_motion[[2*n+1 for n in top]] = 1
        array("base", base)
        array("direction", direction)
        check("reaction_group_names", {key for key in m if key.startswith("group_")}
              == {"group_bottom_platen", "group_top_platen"})
        array("group_bottom_platen", direction)
        array("group_top_platen", top_motion)
        weights = [1/(2*nx) if i in (0, nx) else 1/nx for i in range(nx+1)]
        gap_vector = np.zeros(ndof)
        for lo, up, weight in zip(lower, upper, weights):
            gap_vector[2*lo+1], gap_vector[2*up+1] = -weight, weight
        array("gap_vector", gap_vector)
        expected_regions = dict(bottom_nodes=bottom, top_nodes=top, lower_interface_nodes=lower,
            upper_interface_nodes=upper, interface_weights=weights,
            body_labels={"0":"third_medium", "1":"lower_elastic", "2":"upper_elastic"},
            reference_normal=[0, 1], all_ux_zero=True, full_model=True, force_multiplier=1)
        same_json("regions", meta["regions"], expected_regions)
        reference = dict(lam_s=lam_s, mu_s=mu_s, lam_v=lam_v, mu_v=mu_v,
                         width=geom["width_mm"], H1=geom["lower_height_mm"], H2=geom["upper_height_mm"],
                         gap=geom["gap_mm"], thickness=geom["thickness_mm"])
        same_json("reference_actual_primitives", meta["reference_inputs"], reference)
        if "F0" in m:
            array("F0", np.zeros(ndof))

        source_binding = "not_requested"
        if source_freeze is not None:
            check("source_freeze_mapping", isinstance(source_freeze, Mapping)
                  and isinstance(source_freeze.get("files"), Mapping))
            declared = meta["source_files"]
            check("source_metadata_mapping", isinstance(declared, Mapping))
            runtime = lambda values: {key: value for key, value in values.items()
                                      if key.startswith("src/hf_eval/") and key.endswith(".py")}
            expected_files, actual_files = runtime(source_freeze["files"]), runtime(declared)
            check("source_runtime_nonempty", bool(expected_files))
            check("source_sha256_syntax", all(isinstance(v, str) and len(v) == 64
                  and all(c in "0123456789abcdef" for c in v) for v in expected_files.values()))
            same_json("runtime_source_freeze", actual_files, expected_files)
            source_binding = "checked"
        return dict(schema_version="hf4-input-audit-1.0", status="pass", checks=checks,
                    node_count=nn, element_count=ne, dof_count=ndof,
                    source_binding=source_binding, scope="frozen uniform normal task input mapping")
    except KeyError as error:
        raise ValueError("HF4 input binding is missing field: "+str(error)) from error
