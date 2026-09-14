"""Convert verbatim MATLAB C-shape setup to canonical plain numeric data."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = Path(__file__).resolve().parent
    run = base / "setup_002"
    problem = loadmat(run / "cshape_setup.mat", struct_as_record=False, squeeze_me=True)["problem"]
    fe = problem.fe
    nx, ny = int(problem.nx), int(problem.ny)
    hx, hy = problem.Lx / nx, problem.Ly / ny
    nn, ne = len(fe.X), len(fe.IX)
    node_c = (np.rint(fe.X[:, 1] / hy) * (nx+1) + np.rint(fe.X[:, 0] / hx)).astype(np.int64)
    can_node = np.argsort(node_c)
    dof_c = np.column_stack((2*node_c, 2*node_c+1)).ravel()
    can_dof = np.argsort(dof_c)
    ix_source = np.asarray(fe.IX, dtype=np.int64)
    centers = fe.X[ix_source-1].mean(axis=1)
    element_c = (np.rint(centers[:, 1] / hy - .5)*nx + np.rint(centers[:, 0] / hx - .5)).astype(np.int64)
    can_element = np.argsort(element_c)
    fixed_source = np.asarray(problem.fixed_dofs_source, dtype=np.int64)
    loaded_source = np.asarray(problem.loaded_dofs_source, dtype=np.int64)
    fixed = np.sort(dof_c[fixed_source-1])
    loaded = dof_c[loaded_source-1]
    arrays = dict(targets=problem.targets, coordinates=fe.X[can_node], connectivity=node_c[ix_source[can_element]-1],
                  gamma=problem.gamma_source[can_element], F0=fe.F0[can_dof], fixed_dofs=fixed,
                  loaded_dofs=loaded, loaded_nodes=loaded//2, free_dofs=np.setdiff1d(np.arange(2*nn),fixed),
                  coordinates_source=fe.X, connectivity_source=ix_source, dof_connectivity_source=np.asarray(fe.cDofMat,dtype=np.int64),
                  gamma_source=problem.gamma_source, F0_source=fe.F0, fixed_dofs_source=fixed_source,
                  loaded_dofs_source=loaded_source, loaded_nodes_source=loaded_source//2,
                  source_to_canonical_nodes=node_c, canonical_to_source_nodes=can_node,
                  source_to_canonical_dofs=dof_c, canonical_to_source_dofs=can_dof,
                  source_to_canonical_elements=element_c, canonical_to_source_elements=can_element)
    assert np.array_equal(np.sort(node_c), np.arange(nn))
    assert np.array_equal(np.sort(element_c), np.arange(ne))
    assert np.count_nonzero(arrays["gamma"]==1)==828 and np.count_nonzero(arrays["gamma"]==1e-6)==1032
    assert len(arrays["targets"])==100 and len(loaded)==6
    assert abs(arrays["F0"][1::2].sum()+3)<1e-14
    path = run / "cshape_setup.npz"
    np.savez_compressed(path, **arrays)
    meta = dict(schema_version="hf2-cshape-setup-1.0",kind="setup_only_no_solve",units_mode="source_numeric",
                source_zip_sha256=json.loads((base/"validation_spec.json").read_text())["source_zip_sha256"],
                setup_origin="Verbatim setup substring of uploaded cshapeTMC.m between USER-DEFINED DATA and PERFORM NONLINEAR ANALYSIS sentinels",
                source_script_sha256=sha(base/"source/cshapeTMC.m"),validation_spec_sha256=sha(base/"validation_spec.json"),
                source_indexing="1-based",canonical_indexing="0-based xfast bottom-up, ux/uy interleaved",
                local_corner_order="BL_BR_TR_TL",mapping_indices="both directions 0-based",
                targets_origin="Original solveIncrIter linspace(nl.lambdaMax/nl.nIncr,nl.lambdaMax,nl.nIncr) evaluated in MATLAB",
                npz_path=path.name,sha256=sha(path),mat_sha256=sha(run/"cshape_setup.mat"),
                domain=[float(problem.Lx),float(problem.Ly)],nx=nx,ny=ny,hx=hx,hy=hy,E=float(problem.E),nu=float(problem.nu),
                alpha=float(problem.alpha),kv=float(problem.kv),thickness_factor=1,
                lam_s=float(fe.lam),mu_s=float(fe.mu),kr=float(fe.kr),solid_cells=828,medium_cells=1032,
                arrays={k:{"shape":list(v.shape),"dtype":str(v.dtype)} for k,v in arrays.items()},
                process_record_path="process_record.json",process_record_sha256=sha(run/"process_record.json"))
    (run/"cshape_setup.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"sha256":meta["sha256"],"loaded_nodes":arrays["loaded_nodes"].tolist(),"fixed_dofs":len(fixed)},indent=2))


if __name__=="__main__":
    main()
