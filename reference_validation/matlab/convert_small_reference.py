"""Serialize MATLAB numerical outputs, preserving explicit source/canonical maps."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.sparse import issparse


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="small_001")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    run = base / args.run_id
    index = json.loads((run / "small_reference_index_matlab.json").read_text())
    index["validation_spec_sha256"] = sha(base / "validation_spec.json")
    index["schema_version"] = "hf2-numerical-reference-1.0"
    index["array_conventions"] = {
        "source_index_arrays": "connectivity_source/dof_connectivity_source are 1-based; all maps are 0-based",
        "global_canonical_order": "x-fast, y bottom to top; ux/uy interleaved",
        "element_order": "BL,BR,TR,TL with ux/uy interleaved",
        "tensor_shape": "J=(ne,9); F/stress_second_piola=(ne,9,2,2); element_* retain ne axis",
        "quadrature_order": "xi slow, eta fast",
        "u_residual_tangent": "element cases local corner order; global cases canonical global order",
        "decomposition": "material evaluated in original assembly with kr=0; regularization with gamma=0",
        "material_energy": "per canonical element, reference-volume quadrature weighted, external postprocessor",
    }
    scalar_names = {"lam_solid", "mu_solid", "kr", "material_energy_total"}
    vector_names = {"u", "residual", "material_residual", "regularization_residual", "weights", "gamma", "gamma_source", "material_energy"}
    vector_names |= {"u_source", "u_canonical", "residual_source", "residual_canonical", "material_residual_canonical", "regularization_residual_canonical"}
    for case in index["cases"]:
        mat = run / case["mat_path"]
        arrays = {k: v.toarray() if issparse(v) else np.asarray(v) for k, v in loadmat(mat).items() if not k.startswith("__")}
        for key in list(arrays):
            if key in scalar_names:
                arrays[key] = arrays[key].reshape(())
            elif key in vector_names or "_to_" in key:
                arrays[key] = arrays[key].reshape(-1)
            if "connectivity" in key or "_to_" in key:
                assert np.all(arrays[key] == np.round(arrays[key]))
                arrays[key] = arrays[key].astype(np.int64)
            assert arrays[key].dtype != object and np.all(np.isfinite(arrays[key]))
        ne = int(np.prod(case["mesh"]))
        assert arrays["J"].shape == (ne, 9)
        assert arrays["F"].shape == (ne, 9, 2, 2)
        assert np.allclose(arrays["residual"], arrays["material_residual"] + arrays["regularization_residual"], rtol=1e-14, atol=1e-14)
        assert np.allclose(arrays["tangent"], arrays["material_tangent"] + arrays["regularization_tangent"], rtol=1e-14, atol=1e-14)
        assert np.array_equal(arrays["coordinates_source"][arrays["canonical_to_source_nodes"]], arrays["coordinates"])
        assert np.array_equal(arrays["u_source"][arrays["canonical_to_source_dofs"]], arrays["u_canonical"])
        path = run / case["npz_path"]
        np.savez_compressed(path, **arrays)
        case.update(sha256=sha(path), mat_sha256=sha(mat), Lx=case["Lx_characteristic"],
                    field_index=case["field_id"], nx=case["mesh"][0], ny=case["mesh"][1],
                    lam_s=float(arrays["lam_solid"]), mu_s=float(arrays["mu_solid"]), kr=float(arrays["kr"]),
                    min_J=float(arrays["J"].min()), arrays={k: {"shape": list(a.shape), "dtype": str(a.dtype)} for k, a in arrays.items()})
    wrapper_raw = loadmat(run / "wrapper_equivalence.mat", struct_as_record=False, squeeze_me=True)
    fe = wrapper_raw["fe"]
    xy = fe.X
    node_c = (np.rint(xy[:, 1]) * 3 + np.rint(xy[:, 0])).astype(np.int64)
    can_node = np.argsort(node_c)
    dof_c = np.column_stack((2 * node_c, 2 * node_c + 1)).ravel()
    can_dof = np.argsort(dof_c)
    cell_centers = xy[np.asarray(fe.IX, dtype=int)-1].mean(axis=1)
    element_c = np.rint(cell_centers[:, 0] - .5).astype(np.int64)
    can_element = np.argsort(element_c)
    wrapper = {k: np.asarray(wrapper_raw[k].toarray() if issparse(wrapper_raw[k]) else wrapper_raw[k]) for k in ("Uonce", "U", "path", "targets", "fix", "K", "R")}
    wrapper.update(coordinates_source=fe.X, connectivity_source=np.asarray(fe.IX, dtype=np.int64),
                   dof_connectivity_source=np.asarray(fe.cDofMat, dtype=np.int64), load_source=fe.F0,
                   free_source=np.asarray(fe.free, dtype=np.int64),
                   source_to_canonical_nodes=node_c, canonical_to_source_nodes=can_node,
                   source_to_canonical_dofs=dof_c, canonical_to_source_dofs=can_dof,
                   source_to_canonical_elements=element_c, canonical_to_source_elements=can_element,
                   coordinates=xy[can_node], connectivity=node_c[np.asarray(fe.IX, dtype=np.int64)[can_element]-1],
                   u_canonical=np.asarray(wrapper_raw["U"])[can_dof], path_canonical=wrapper_raw["path"][can_dof],
                   load_canonical=np.asarray(fe.F0)[can_dof], fixed_dofs_canonical=dof_c[np.asarray(wrapper_raw["fix"], dtype=int)-1])
    wrapper_path = run / "wrapper_equivalence.npz"
    np.savez_compressed(wrapper_path, **wrapper)
    index["wrapper"].update(npz_path=wrapper_path.name, sha256=sha(wrapper_path), mat_sha256=sha(run / "wrapper_equivalence.mat"))
    index["process_record_path"] = "process_record.json"
    index["process_record_sha256"] = sha(run / "process_record.json")
    (run / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"cases": len(index["cases"]), "index": str(run / "index.json"), "min_J": min(c["min_J"] for c in index["cases"]), "wrapper": index["wrapper"]}, indent=2))


if __name__ == "__main__":
    main()
