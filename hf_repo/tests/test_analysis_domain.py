"""Independent physical-coordinate tests for HF right-medium domain padding.

Future bounded test run only: two small native-project constructions (36/48
cells), no constitutive response, tangent, equilibrium or deformed observations.
"""
from copy import deepcopy
from hashlib import sha256

import numpy as np
import pytest

from hf_eval.analysis_domain import write_right_medium_geometry
from hf_eval.data import ARRAY_NAMES, GeometryError, load_geometry, write_geometry
from hf_eval.native_map import prepare_native_geometry
from hf_eval.native_project import build_native_project


def parent_package(tmp_path):
    """Explicit nonzero origin and unequal h; four distinct nonuniform masks."""
    solid = np.array([
        [1,1,1,1,0,0], [1,1,1,1,0,0], [1,1,1,1,0,0],
        [1,1,0,0,0,0], [1,1,0,0,0,0], [1,1,0,0,0,0],
    ], dtype=np.uint8)
    passive_solid = np.zeros_like(solid);passive_solid[:,0] = 1
    design = solid-passive_solid;design[0,5] = 1
    arrays = dict(solid=solid,design=design,passive_solid=passive_solid,
                  passive_void=1-design-passive_solid)
    averaging = "normalized_reference_arclength_trapezoid"
    background = dict(kind="complement_on_line",interval="open_closed",
        line=dict(axis="y",value_mm=1.),start_exclusive_mm=14.,end_inclusive_mm=22.)
    metadata = dict(schema_version="hf-geometry-1.0",case_family="gripper",length_unit="mm",
        grid=dict(shape_yx=[6,6],origin_mm=[10.,-2.],cell_size_mm=[2.,.5],extent_mm=[12.,3.],
            axes=[[1.,0.],[0.,1.]],array_order="C_yx_bottom_up",value_location="cell"),
        thickness_mm=3.,model_extent=dict(kind="lower_half",symmetry_axis=dict(normal=[0.,1.],offset_mm=1.)),
        region_tags=dict(support=dict(points_mm=[[10.,-2.],[10.,-1.]],components=[0,1]),
            symmetry=dict(points_mm=[[10.,1.],[14.,1.]],components=[1]),
            input=dict(points_mm=[[12.,-1.5],[12.,-.5]],direction=[1.,0.],averaging=averaging),
            output=dict(points_mm=[[18.,-1.5],[18.,-.5]],direction=[0.,1.],averaging=averaging)),
        processing=dict(source_kind="synthetic_LF_native_history",density_threshold=.5,cleanup_applied=False),
        provenance=dict(lf_v2=dict(schema="dmftd.hf_export.v2",source_note="synthetic history, never an active new LF solve",
            descriptor=dict(native_grid=dict(nx=6,ny=6,extent_mm=[12.,3.]),regions_mm=dict(symmetry_background=background))),
            user_note="Retain original physical segments and source history."))
    descriptor = write_geometry(tmp_path/"parent",metadata,arrays)
    return descriptor,load_geometry(descriptor)


def raw_package(geometry):
    return {name:geometry.path.with_name(name).read_bytes() for name in ("geometry.json","geometry.npz")}


def physical_nodes(project,nodes):
    return {tuple(xy) for xy in project.model.coordinates[np.asarray(nodes,dtype=int)]}


def physical_dofs(project,dofs):
    return {(float(project.model.coordinates[d//2,0]),float(project.model.coordinates[d//2,1]),int(d%2)) for d in dofs}


def task_for(geometry,right_x):
    return dict(schema_version="hf-native-project-task-1.1",task_id="padding_construction_TEST",case_family="gripper",
        purpose="construction_test_only",units=dict(length="mm",force="N",stress="MPa",energy="N mm"),
        geometry=dict(geometry_id=geometry.geometry_id,descriptor_sha256=geometry.metadata["descriptor_sha256"]),
        analysis_grid=dict(policy="native"),material=dict(E_MPa=2.,nu=.25,formulation="plane_strain"),
        third_medium=dict(gamma=1e-3),regularization=dict(alpha=2e-6,length_mm=80.),
        input=dict(tag="input",control="average_displacement",target_mm=.25),
        output=dict(tag="output",spring_N_per_mm=0.),input_auxiliary_spring_N_per_mm=0.,
        constraints=[dict(tag="support",components=[0,1]),dict(tag="symmetry",components=[1])],
        support_selection="solid_incident_nodes_only",background_symmetry=dict(points_mm=[[10.,1.],[right_x,1.]],components=[1]),
        workpiece=dict(kind="fixed_rigid",shape="square",center_mm=[21.,1.],side_mm=2.,fixed_components=[0,1]),
        reference_state="undeformed",qualification_criteria=dict(max_design_volume_fraction=None,min_feature_mm=None),
        path=dict(kind="ordered_cycle",targets_mm=[0.,.25,0.]))


def test_old_mask_bytes_and_hand_tabulated_physical_native_mesh_survive_padding(tmp_path):
    path,parent = parent_package(tmp_path);before = raw_package(parent)
    output = write_right_medium_geometry(path,tmp_path/"padded",2)
    assert output.is_absolute() and output.name == "geometry.json"
    padded = load_geometry(output)
    assert raw_package(parent) == before
    assert padded.grid["shape_yx"] == [6,8] and padded.grid["extent_mm"] == [16.,3.]
    assert padded.grid["origin_mm"] == [10.,-2.] and padded.grid["cell_size_mm"] == [2.,.5]
    for name in ARRAY_NAMES:
        assert padded.arrays[name][:,:6].tobytes(order="C") == parent.arrays[name].tobytes(order="C")
        assert np.all(padded.arrays[name][:,6:] == (1 if name == "passive_void" else 0))
    assert padded.geometry_id != parent.geometry_id and padded.metadata["descriptor_sha256"] != parent.metadata["descriptor_sha256"]
    assert padded.metadata["region_tags"] == parent.metadata["region_tags"]
    # A literal physical-node table is independent of the implementation's row stride.
    xs = [10.,12.,14.,16.,18.,20.,22.,24.,26.]
    ys = [-2.,-1.5,-1.,-.5,0.,.5,1.]
    mapping = prepare_native_geometry(output)
    np.testing.assert_array_equal(mapping.arrays["coordinates_mm"],[(x,y) for y in ys for x in xs])
    expected_quads = [[(xl,yb),(xr,yb),(xr,yt),(xl,yt)]
        for yb,yt in zip(ys,ys[1:]) for xl,xr in zip(xs,xs[1:])]
    np.testing.assert_array_equal(mapping.arrays["coordinates_mm"][mapping.arrays["connectivity"]],expected_quads)
    assert mapping.metadata["counts"]["elements"] == 48 and mapping.metadata["counts"]["dofs"] == 126
    # This open/closed LF line remains the historical segment, not the new HF task boundary.
    np.testing.assert_array_equal(mapping.arrays["coordinates_mm"][mapping.arrays["background_source_nodes"]],
        [(16.,1.),(18.,1.),(20.,1.),(22.,1.)])
    assert mapping.metadata["constraints_applied"] is mapping.metadata["material_assigned"] is False


def test_new_identity_records_hf_derivation_without_relabeling_lf_history(tmp_path):
    path,parent = parent_package(tmp_path);before = raw_package(parent)
    padded = load_geometry(write_right_medium_geometry(path.parent,tmp_path/"padded",np.int64(2)))
    assert raw_package(parent) == before
    assert padded.metadata["provenance"]["lf_v2"] == parent.metadata["provenance"]["lf_v2"]
    assert padded.metadata["provenance"]["user_note"] == parent.metadata["provenance"]["user_note"]
    chain = padded.metadata["provenance"]["hf_analysis_domain_derivations"]
    assert len(chain) == 1
    record = chain[0];origin = record["parent_hf_geometry"]
    assert record["operation"] == "right_passive_void_padding" and record["right_columns"] == 2 and record["margin_mm"] == 4.
    assert record["old_grid"] == parent.grid and record["new_grid"] == padded.grid
    assert record["parent_cell_slice_yx"] == [[0,6],[0,6]]
    assert origin["geometry_id"] == parent.geometry_id and origin["descriptor_sha256"] == parent.metadata["descriptor_sha256"]
    assert origin["geometry_json_sha256"] == sha256(before["geometry.json"]).hexdigest()
    assert origin["geometry_npz_sha256"] == sha256(before["geometry.npz"]).hexdigest()
    assert origin["array_fields"] == parent.metadata["arrays"]["fields"] and origin["processing"] == parent.metadata["processing"]
    policy = padded.metadata["processing"]
    assert policy["source_kind"] == "HF_derived_analysis_domain" and policy["parent_native_subdomain_preserved"] is True
    assert policy["whole_grid_is_LF_native"] is policy["resampling_applied"] is policy["lf_optimization_applied"] is False
    assert policy["new_threshold_or_cleanup_applied"] is policy["background_boundary_applied"] is False
    assert padded.metadata["model_extent"] == parent.metadata["model_extent"] and padded.metadata["thickness_mm"] == 3.


def test_small_project_preserves_physical_groups_material_ports_and_rebuilds_direction(tmp_path):
    path,parent = parent_package(tmp_path)
    padded = load_geometry(write_right_medium_geometry(path,tmp_path/"padded",2))
    old_task,new_task = task_for(parent,22.),task_for(padded,26.)
    old_task_raw,new_task_raw = deepcopy(old_task),deepcopy(new_task)
    old,new = build_native_project(path,old_task),build_native_project(padded.path,new_task)
    assert old_task == old_task_raw and new_task == new_task_raw
    assert (old.model.ne,new.model.ne,old.model.ndof,new.model.ndof) == (36,48,98,126)
    assert old.material == new.material and old.material["regularization_length_mm"] == 80.
    assert old.model.kr == new.model.kr == pytest.approx(.03072,rel=2e-15)
    assert old.model.hx == new.model.hx == 2. and old.model.hy == new.model.hy == .5
    assert old.model.thickness == new.model.thickness == 3.
    for key in ("points","grad","hessian","weights"):
        assert old.model.ops[key].tobytes() == new.model.ops[key].tobytes()
    expected_solid = {(x,y) for y in [-1.75,-1.25,-.75,-.25,.25,.75] for x in [11.,13.]}
    expected_solid |= {(x,y) for y in [-1.75,-1.25,-.75] for x in [15.,17.]}
    old_centres = old.model.coordinates[old.model.connectivity].mean(axis=1)
    new_centres = new.model.coordinates[new.model.connectivity].mean(axis=1)
    assert {tuple(xy) for xy in old_centres[old.model.solid]} == {tuple(xy) for xy in new_centres[new.model.solid]} == expected_solid
    new_cells = {tuple(xy):i for i,xy in enumerate(new_centres)}
    for i,centre in enumerate(old_centres):
        j = new_cells[tuple(centre)]
        assert (new.model.solid[j],new.gamma[j],new.model.lam[j],new.model.mu[j]) == (old.model.solid[i],old.gamma[i],old.model.lam[i],old.model.mu[i])
        np.testing.assert_array_equal(new.model.coordinates[new.model.connectivity[j]],old.model.coordinates[old.model.connectivity[i]])
    added = np.flatnonzero(new_centres[:,0]>22.)
    assert len(added) == 12 and not new.model.solid[added].any()
    np.testing.assert_array_equal(new.gamma[added],np.full(12,1e-3))
    np.testing.assert_array_equal(new.model.lam[added],np.full(12,.8e-3))
    np.testing.assert_array_equal(new.model.mu[added],np.full(12,.8e-3))
    expected_support = {(10.,y,c) for y in [-2.,-1.5,-1.] for c in [0,1]}
    expected_entity = {(x,1.,1) for x in [10.,12.,14.]}
    expected_body = {(x,y,c) for x in [20.,22.] for y in [0.,.5,1.] for c in [0,1]}
    for project in (old,new):
        regions = project.region_metadata
        assert physical_dofs(project,regions["support"]["dofs"]) == expected_support
        assert physical_dofs(project,regions["entity_symmetry"]["dofs"]) == expected_entity
        assert physical_dofs(project,regions["workpiece"]["dofs"]) == expected_body
        assert regions["workpiece"]["definition"] == old_task["workpiece"]
        assert (regions["workpiece"]["selected_cells"],regions["workpiece"]["incident_nodes"],regions["workpiece"]["fixed_dofs"]) == (2,6,12)
        for name,x,component in (("input",12.,0),("output",18.,1)):
            port = regions["ports"][name]
            assert physical_nodes(project,port["nodes"]) == {(x,y) for y in [-1.5,-1.,-.5]}
            assert physical_dofs(project,port["nonzero_dofs"]) == {(x,y,component) for y in [-1.5,-1.,-.5]}
            assert port["weights"] == [.25,.5,.25]
        x,y = project.model.coordinates.T
        manufactured = np.column_stack((3.+.25*x-.5*y,-2.+.125*x+.75*y)).ravel()
        assert project.bin@manufactured == 6.5 and project.bout@manufactured == -.5
        assert (-7.25*project.bin)@manufactured == -7.25*6.5
        assert not project.bin[project.model.fixed_dofs].any() and not project.bout[project.model.fixed_dofs].any()
    old_fixed,new_fixed = physical_dofs(old,old.model.fixed_dofs),physical_dofs(new,new.model.fixed_dofs)
    assert new_fixed == old_fixed|{(24.,1.,1),(26.,1.,1)}
    assert (len(old.model.fixed_dofs),len(new.model.fixed_dofs)) == (23,25)
    assert physical_nodes(old,old.region_metadata["background_symmetry"]["selected_nodes"]) == {(x,1.) for x in [10.,12.,14.,16.,18.,20.,22.]}
    assert physical_nodes(new,new.region_metadata["background_symmetry"]["selected_nodes"]) == {(x,1.) for x in [10.,12.,14.,16.,18.,20.,22.,24.,26.]}
    assert old.region_metadata["source_background"] == new.region_metadata["source_background"]
    old_direction = old.bin/abs(old.bin).max();new_direction = new.bin/abs(new.bin).max()
    assert physical_dofs(old,np.flatnonzero(old_direction)) == physical_dofs(new,np.flatnonzero(new_direction))
    assert not np.array_equal(np.pad(old_direction,(0,new.model.ndof-old.model.ndof)),new_direction)
    assert old.task["workpiece"] == new.task["workpiece"] and old.task["material"] == new.task["material"]


def test_parent_and_existing_output_are_never_overwritten(tmp_path):
    path,parent = parent_package(tmp_path);before = raw_package(parent)
    with pytest.raises(FileExistsError):write_right_medium_geometry(path,path.parent,2)
    assert raw_package(parent) == before
    existing = tmp_path/"existing";existing.mkdir();sentinel = existing/"keep.txt";sentinel.write_text("keep",encoding="utf-8")
    with pytest.raises(FileExistsError):write_right_medium_geometry(path,existing,2)
    assert sentinel.read_text(encoding="utf-8") == "keep" and sorted(p.name for p in existing.iterdir()) == ["keep.txt"]


def test_only_positive_integer_column_counts_are_accepted(tmp_path):
    path,parent = parent_package(tmp_path);before = raw_package(parent)
    for bad in (True,1.5,0):
        output = tmp_path/("rejected_"+str(bad))
        with pytest.raises(GeometryError,match="positive integer"):write_right_medium_geometry(path,output,bad)
        assert not output.exists()
    assert raw_package(parent) == before
