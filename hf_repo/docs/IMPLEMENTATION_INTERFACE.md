# HF-1 internal implementation interface (frozen for this stage)

Only a diagnostic linear evaluator, no LF code, nonlinear TMC or optimization.

Package `hf_eval`, source layout, independent wheel. Root owns packaging, CLI/evaluate/result/plotting/integration scripts. Data agent owns data.py, regions.py, their tests and DATA_FORMAT.md. Mechanics agent owns linear.py and mechanics tests. Export agent owns lf_data_preparation and geometry_dataset (uses public writer, never adds LF code in HF).

`data.py` exports `ARRAY_NAMES=('solid','design','passive_solid','passive_void')`, `GeometryError(ValueError)`, `Geometry(metadata:dict, arrays:dict[str,np.ndarray], path:Path)`, `load_geometry(path)->Geometry`, `write_geometry(directory, metadata, arrays)->Path`, `geometry_id(metadata,arrays)->str`, `canonical_hash(obj)->str`. Geometry has properties `solid`, `grid`, `geometry_id`. `path` points to geometry.json. Writer deep copies metadata, validates arrays before uint8 conversion, writes geometry.npz and geometry.json, computes byte hashes/content identities. Source metadata unrelated to geometry must not enter geometry_id. Input files read with allow_pickle=False, no paths outside package root; same directory relative arrays.path is enough v1.

Metadata schema:

```json
{
 "schema_version":"hf-geometry-1.0", "case_family":"inverter",
 "geometry_id":"computed", "grid":{"shape_yx":[40,80],"origin_mm":[0.0,0.0],"cell_size_mm":[1.0,1.0],"axes":[[1,0],[0,1]],"extent_mm":[80.0,40.0],"array_order":"C_yx_bottom_up","value_location":"cell"},
 "thickness_mm":20.0,
 "model_extent":{"kind":"lower_half","symmetry_axis":{"normal":[0,1],"offset_mm":40.0}},
 "region_tags":{
   "support":{"points_mm":[[0,0],[0,8]],"components":[0,1]},
   "symmetry":{"points_mm":[[0,40],[80,40]],"components":[1]},
   "input":{"points_mm":[[0,38],[0,40]],"direction":[1,0],"averaging":"normalized_reference_arclength_trapezoid"},
   "output":{"points_mm":[[80,38],[80,40]],"direction":[-1,0],"averaging":"normalized_reference_arclength_trapezoid"}
 },
 "source_record_ids":[], "processing":{}, "arrays":{"path":"geometry.npz","sha256":"computed","fields":{}},
 "descriptor_sha256":"computed"
}
```

Hash: authority canonical header + fixed named binary arrays (uint8 C order). Float canonicalization to float.hex strings recursively, excluding provenance; header includes schema, grid, thickness, model_extent; arrays include all four masks. descriptor_sha256 covers metadata except descriptor_sha256 (thus includes tags/processing/source ids). Canonical JSON sorted keys compact UTF8, allow_nan=False. Validate finite values and axes/partition/binary invariants, grid shape exact, dimensions positive, exact unit semantics mm, descriptor/file/hash mismatches rejected. Original authority immutable; mesh refinements separately identified.

`regions.py` exports `node_coordinates(geometry)->(nnode,2)` x-fast bottom-up; `element_connectivity(geometry)->(ny*nx,4)` BL BR TR TL; `active_nodes(geometry)->bool[nnode]`; `region_nodes(geometry, tag:dict)->int[]` axis-aligned segment endpoints must coincide with nodes; `port_vector(geometry, tag:dict)->(b:float[2*nnode], nodes:int[], weights:float[])`; `qualify_geometry(geometry, criteria:dict|None=None)->dict`. Shared-edge 4-connectivity and 8 count, local diagonal patterns, physical area/volumes and attached support/input/output; physical thresholds unknown=>pending, explicit connectivity fail=>fail. Input/output missing solid attachments=>fail. Support only needs at least two distinct attached nodes for this interface smoke, reported as smoke criterion not universal manufacturing rule. Qualification reports component ids linking all ports and actual support; no cleanup.

Task JSON (one per case family): `schema_version='hf-task-1.0'`, `task_id`, `case_family`, `purpose='linear_interface_smoke_only'`, `parameter_origin='authorized_pilot_not_research_task'`, `material={E_MPa:1.0,nu:0.3,formulation:'plane_strain'}`, `input={tag:'input',displacement_mm:1e-6}`, `output={tag:'output',spring_N_per_mm:0.0}`, `constraints=[{tag:'support',components:[0,1]},{tag:'symmetry',components:[1]}]`, `support_selection='solid_incident_nodes_only'`, `input_auxiliary_spring_N_per_mm=0`, `workpiece=null`, `third_medium=null`, `qualification_criteria={max_design_volume_fraction:null,min_feature_mm:null}`, `reference_state='undeformed'`. No implicit inheritance from LF. Synthetic marker not passed to real mechanics by default.

Solver JSON: `schema_version='hf-solver-1.0'`, `solver_id='hf1_q1_solid_linear_v1'`, `analysis='solid_linear_q1'`, `quadrature='gauss_2x2'`, `dtype='float64'`, `linear_solver='scipy_superlu'`, `relative_force_tolerance=1e-9`, `constraint_relative_tolerance=1e-10`, `constraint_scale_floor_mm=1e-6`, `time_limit_seconds=300`. Reject unsupported config, don't silently ignore changed semantics.

`linear.py` exports `element_stiffness(E,nu,hx,hy,thickness)->(8,8)`, `solve_average_system(K,b,d,fixed_dofs,k_out=0,b_out=None, force_scale_floor=...)->dict` for small analytic tests (full DOF system), `analyze(geometry,task,solver)->(result:dict, arrays:dict)`. Runtime: only solid Q1 elements, active nodes compacted, support/symmetry on solid incident nodes only. KKT sign K u+k b_out q_out-b_in R=0, b_in^T u=d, R actuator force on structure. Output original full-grid u flattened x/y interleaved with inactive DOFs zero and explicit active_nodes mask, coordinates, solid connectivity, port b/weights and fixed DOFs. Include q_in_mm, q_out_mm, R_in_N, output_load_N (force ON structure=-k*q), strain_energy_N_mm, spring_energy_N_mm, input_work_N_mm=0.5*R*d, residual metrics/normalization, reached_input_mm, material strain/stress arrays, timing. Report actual force and constraint convergence, never substitute failure with zeros. Numeric failure should raise specific `AnalysisError` for root wrapper to serialize; qualification can remain pending after success. No calls to plotting or file writes in linear.py.

Result wrapper/CLI root owns: load file, task+solver hash, UUID evaluation, separate readability/qualification/numerics/functionality, diagnostic-only status, save JSON/NPZ/figures, no geometry mutation; one CLI `python -m hf_eval inspect GEOMETRY`, `... evaluate GEOMETRY --task TASK --solver SOLVER --output DIRECTORY`.
