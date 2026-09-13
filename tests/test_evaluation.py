"""Public result validity and failure persistence, independent of any LF data."""
from copy import deepcopy
import json
import numpy as np
import pytest

from hf_eval.data import write_geometry
from hf_eval.evaluation import evaluate, inspect_geometry


def sample(tmp_path):
    metadata={"schema_version":"hf-geometry-1.0","case_family":"synthetic_validation",
        "grid":{"shape_yx":[2,3],"origin_mm":[0,0],"cell_size_mm":[1,1],"axes":[[1,0],[0,1]],
                "extent_mm":[3,2],"array_order":"C_yx_bottom_up","value_location":"cell"},
        "thickness_mm":2,"model_extent":{"kind":"full"},
        "region_tags":{
            "support":{"points_mm":[[0,0],[0,2]],"components":[0,1]},
            "symmetry":{"points_mm":[[0,2],[3,2]],"components":[1]},
            "input":{"points_mm":[[3,0],[3,2]],"direction":[1,0],"averaging":"normalized_reference_arclength_trapezoid"},
            "output":{"points_mm":[[3,0],[3,2]],"direction":[0,1],"averaging":"normalized_reference_arclength_trapezoid"}},
        "source_record_ids":["synthetic_test_only"],"processing":{"kind":"synthetic"}}
    arrays={"solid":np.ones((2,3),dtype=np.uint8),"design":np.ones((2,3),dtype=np.uint8),
            "passive_solid":np.zeros((2,3),dtype=np.uint8),"passive_void":np.zeros((2,3),dtype=np.uint8)}
    task={"schema_version":"hf-task-1.0","task_id":"synthetic_validation_v1","case_family":"synthetic_validation",
          "purpose":"linear_interface_smoke_only","parameter_origin":"authorized_pilot_not_research_task",
          "material":{"E_MPa":1.0,"nu":.3,"formulation":"plane_strain"},
          "input":{"tag":"input","displacement_mm":1e-6},"output":{"tag":"output","spring_N_per_mm":0.0},
          "constraints":[{"tag":"support","components":[0,1]},{"tag":"symmetry","components":[1]}],
          "support_selection":"solid_incident_nodes_only","input_auxiliary_spring_N_per_mm":0,
          "workpiece":None,"third_medium":None,"qualification_criteria":{"max_design_volume_fraction":None,"min_feature_mm":None},
          "reference_state":"undeformed"}
    solver={"schema_version":"hf-solver-1.0","solver_id":"hf1_q1_solid_linear_v1","analysis":"solid_linear_q1",
            "quadrature":"gauss_2x2","dtype":"float64","linear_solver":"scipy_superlu",
            "relative_force_tolerance":1e-9,"constraint_relative_tolerance":1e-10,
            "constraint_scale_floor_mm":1e-6,"time_limit_seconds":300}
    return write_geometry(tmp_path/'geometry',metadata,arrays),task,solver


def test_success_does_not_promote_research_qualification(tmp_path):
    geometry,task,solver=sample(tmp_path)
    original=geometry.read_bytes()
    result=evaluate(geometry,task,solver)
    assert result['readability']['status']=='pass'
    assert result['numerics']['status']=='success'
    assert result['qualification']['status']=='pending'
    assert result['functionality']['status']=='not_assessed'
    assert result['metrics_at_target']['q_in_mm']==pytest.approx(1e-6,rel=1e-10)
    assert geometry.read_bytes()==original


def test_configuration_failure_persisted_with_null_target(tmp_path):
    geometry,task,solver=sample(tmp_path)
    task['material']['formulation']='plane_stress'
    result=evaluate(geometry,task,solver,tmp_path/'failure')
    saved=json.loads((tmp_path/'failure/result.json').read_text(encoding='utf-8'))
    assert saved==result
    assert result['readability']['status']=='pass'
    assert result['numerics']['status']=='failed'
    assert result['numerics']['reason']
    assert result['metrics_at_target'] is None
    assert not (tmp_path/'failure/fields.npz').exists()


def test_bad_geometry_separate_from_numerical_failure(tmp_path):
    geometry,task,solver=sample(tmp_path)
    with geometry.open('a',encoding='utf-8') as stream:
        stream.write('invalid trailing text')
    result=evaluate(geometry,task,solver,tmp_path/'bad_geometry')
    assert result['readability']['status']=='fail'
    assert result['qualification']['status']=='not_evaluated'
    assert result['numerics']['failure_stage']=='geometry_read'
    assert result['metrics_at_target'] is None


def test_output_directory_not_overwritten(tmp_path):
    geometry,task,solver=sample(tmp_path)
    destination=tmp_path/'previous'
    destination.mkdir(); (destination/'result.json').write_text('existing record')
    with pytest.raises(FileExistsError):
        evaluate(geometry,task,solver,destination)
    assert (destination/'result.json').read_text()=='existing record'


def test_explicit_volume_failure_blocks_analysis_without_changing_geometry(tmp_path):
    geometry,task,solver=sample(tmp_path)
    task['qualification_criteria']['max_design_volume_fraction']=.5
    result=evaluate(geometry,task,solver)
    assert result['qualification']['status']=='fail'
    assert result['numerics']['failure_stage']=='geometry_qualification'
    assert result['metrics_at_target'] is None
    assert inspect_geometry(geometry)['qualification']['measurements']['solid_cells']==6
