"""Analytic mechanics checks with dimensional reference scales frozen in HF-1."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from hf_eval.data import Geometry
from hf_eval.linear import AnalysisError, analyze, element_stiffness, solve_average_system


def _rectangle(hx, hy):
    return np.array([[0, 0], [hx, 0], [hx, hy], [0, hy]], dtype=float)


@pytest.mark.parametrize("hx,hy,thickness", [(2.3, 1.4, 0.7), (0.6, 3.1, 2.0)])
def test_rectangular_element_affine_stress_forces_and_energy(hx, hy, thickness):
    E, nu = 210.0, 0.27
    eps = np.array([0.012, -0.007, 0.02])
    xy = _rectangle(hx, hy)
    u = np.column_stack((eps[0]*xy[:, 0]+eps[2]*xy[:, 1]/2,
                         eps[2]*xy[:, 0]/2+eps[1]*xy[:, 1])).ravel()
    # Independent tensor formula for 3D isotropic elasticity with epsilon_zz=0.
    lam = E*nu/((1+nu)*(1-2*nu))
    mu = E/(2*(1+nu))
    stress = np.array([2*mu*eps[0]+lam*(eps[0]+eps[1]),
                       2*mu*eps[1]+lam*(eps[0]+eps[1]), mu*eps[2]])
    expected_energy = 0.5*hx*hy*thickness*(eps @ stress)
    # Uniform stress integrated along the two incident edges at each corner.
    gx_integral = np.array([-hy, hy, hy, -hy])/2
    gy_integral = np.array([-hx, -hx, hx, hx])/2
    expected_force = thickness*np.column_stack((stress[0]*gx_integral+stress[2]*gy_integral,
                                                stress[2]*gx_integral+stress[1]*gy_integral)).ravel()
    K = element_stiffness(E, nu, hx, hy, thickness)
    energy_scale = E*thickness*hx*hy*np.linalg.norm(eps)**2
    force_scale = E*thickness*max(hx,hy)*np.linalg.norm(eps)
    assert abs(0.5*u@K@u-expected_energy) <= 1e-10*energy_scale
    assert np.linalg.norm(K@u-expected_force) <= 1e-10*force_scale
    assert np.linalg.norm(K-K.T) <= 1e-10*E*thickness


def test_rectangular_element_linear_rigid_modes():
    E, nu, hx, hy, thickness = 17.0, 0.31, 2.7, 1.3, 0.9
    K = element_stiffness(E, nu, hx, hy, thickness)
    xy = _rectangle(hx, hy)
    modes = [np.tile([0.2,0],4), np.tile([0,-0.3],4),
             np.column_stack((-0.04*xy[:,1],0.04*xy[:,0])).ravel()]
    for u in modes:
        force_scale = np.linalg.norm(K,2)*np.linalg.norm(u)
        assert np.linalg.norm(K@u) <= 1e-10*force_scale
        assert abs(u@K@u) <= 1e-10*force_scale*np.linalg.norm(u)


def test_average_constraint_is_not_a_rigid_port_binding():
    solved = solve_average_system(np.diag([1.,3.]), np.array([.5,.5]), 2., [])
    np.testing.assert_allclose(solved["u"], [3,1], rtol=0, atol=1e-10)
    assert abs(solved["R_in_N"]-6) <= 1e-10
    assert abs(solved["q_in_mm"]-2) <= 1e-10*2
    assert abs(solved["input_work_N_mm"]-6) <= 1e-10*6
    assert solved["relative_force_residual"] <= 1e-9
    assert solved["u"][0] != solved["u"][1]


def test_generalized_output_spring_and_force_sign_have_analytic_solution():
    solved = solve_average_system(
        sparse.diags([1.,3.]), np.array([.5,.5]), 2., [],
        k_out=5., b_out=np.array([1/3,2/3]),
    )
    # K + 5*b_out*b_out.T = [[14,10],[10,47]]/9.
    np.testing.assert_allclose(solved["u"], [148/41,16/41], rtol=1e-10, atol=0)
    assert abs(solved["R_in_N"]-496/41) <= 1e-10*(496/41)
    assert abs(solved["q_out_mm"]-60/41) <= 1e-10*(60/41)
    assert abs(solved["output_load_N"]+300/41) <= 1e-10*(300/41)
    assert abs(solved["energy_balance_error_N_mm"]) <= 1e-10*solved["input_work_N_mm"]
    # A common incorrect diagonal k*b_i^2 would instead give [188/61,56/61].
    assert np.linalg.norm(solved["u"]-np.array([188/61,56/61])) > 0.1


def test_fixed_dof_reaction_sign_and_average_constraint():
    K = np.array([[2.,-1.,0.],[-1.,4.,-1.],[0.,-1.,3.]])
    b = np.array([0.,.5,.5])
    solved = solve_average_system(K,b,1.,[0])
    np.testing.assert_allclose(solved["u"],[0,8/9,10/9],rtol=1e-10,atol=0)
    assert abs(solved["R_in_N"]-44/9) <= 1e-10*(44/9)
    assert abs(solved["support_reaction_N"][0]+8/9) <= 1e-10
    np.testing.assert_allclose(K@solved["u"],b*solved["R_in_N"]+solved["support_reaction_N"],rtol=0,atol=1e-10)


def test_zero_input_has_finite_zero_response_and_nonzero_normalizer():
    solved=solve_average_system(np.diag([1.,3.]),np.array([.5,.5]),0.,[])
    assert solved["relative_force_residual"] == 0
    assert solved["force_scale_N"] > 0
    np.testing.assert_array_equal(solved["u"],np.zeros(2))


@pytest.mark.parametrize("K,b,d,fixed,kwargs", [
    (np.zeros((2,2)),np.array([1.,0.]),1.,[],{}),
    (np.eye(2),np.array([1.,0.]),1.,[0],{}),
    (np.eye(2),np.array([1.,0.]),float("nan"),[],{}),
    (np.eye(2),np.array([1.,0.]),1.,[],{"k_out":1.}),
    (np.eye(2),np.array([1.,0.]),1.,[],{"k_out":-1.}),
    (np.eye(2),np.array([1.,0.]),1.,[0.5],{}),
])
def test_invalid_or_singular_system_is_not_returned_as_success(K,b,d,fixed,kwargs):
    with pytest.raises(AnalysisError):
        solve_average_system(K,b,d,fixed,**kwargs)


def _geometry():
    # Upper-right void makes active-node filtering and full-grid padding visible.
    solid=np.array([[1,1],[1,0]],dtype=np.uint8)
    tags={
        "support":{"points_mm":[[0,0],[0,2]],"components":[0,1]},
        "symmetry":{"points_mm":[[0,2],[2,2]],"components":[1]},
        "input":{"points_mm":[[2,0],[2,1]],"direction":[1,0],"averaging":"normalized_reference_arclength_trapezoid"},
        "output":{"points_mm":[[2,0],[2,1]],"direction":[-1,0],"averaging":"normalized_reference_arclength_trapezoid"},
    }
    metadata={"schema_version":"hf-geometry-1.0","case_family":"inverter",
              "geometry_id":"test-only-not-written","thickness_mm":0.7,
              "grid":{"shape_yx":[2,2],"origin_mm":[0.,0.],"cell_size_mm":[1.,1.],
                      "axes":[[1,0],[0,1]],"extent_mm":[2.,2.],"array_order":"C_yx_bottom_up","value_location":"cell"},
              "model_extent":{"kind":"full"},"region_tags":tags}
    arrays={"solid":solid,"design":np.ones_like(solid),"passive_solid":np.zeros_like(solid),"passive_void":np.zeros_like(solid)}
    return Geometry(metadata,arrays,Path("unused-test-geometry.json"))


def _task_solver():
    task={"schema_version":"hf-task-1.0","task_id":"test_linear_interface","case_family":"inverter",
          "purpose":"linear_interface_smoke_only","parameter_origin":"authorized_pilot_not_research_task",
          "material":{"E_MPa":1.,"nu":.3,"formulation":"plane_strain"},
          "input":{"tag":"input","displacement_mm":1e-6},"output":{"tag":"output","spring_N_per_mm":.2},
          "constraints":[{"tag":"support","components":[0,1]},{"tag":"symmetry","components":[1]}],
          "support_selection":"solid_incident_nodes_only","input_auxiliary_spring_N_per_mm":0,
          "workpiece":None,"third_medium":None,"qualification_criteria":{},"reference_state":"undeformed"}
    solver={"schema_version":"hf-solver-1.0","solver_id":"hf1_q1_solid_linear_v1","analysis":"solid_linear_q1",
            "quadrature":"gauss_2x2","dtype":"float64","linear_solver":"scipy_superlu",
            "relative_force_tolerance":1e-9,"constraint_relative_tolerance":1e-10,
            "constraint_scale_floor_mm":1e-6,"time_limit_seconds":300}
    return task,solver


def test_small_mesh_assembly_recovery_inactive_nodes_and_support_filtering():
    geometry=_geometry(); task,solver=_task_solver()
    solid_before=geometry.solid.copy(); metadata_before=deepcopy(geometry.metadata)
    result,arrays=analyze(geometry,task,solver)
    assert result["status"] == "success"
    assert result["element_count"] == 3
    assert result["relative_force_residual"] <= 1e-9
    assert result["constraint_error_mm"] <= 1e-10*1e-6
    assert abs(result["q_out_mm"]+1e-6) <= 1e-10*1e-6
    assert result["output_load_N"] > 0 # q_out is negative along the -x output direction.
    inactive_dofs=np.flatnonzero(~np.repeat(arrays["active_nodes"],2))
    np.testing.assert_array_equal(inactive_dofs,[16,17])
    np.testing.assert_array_equal(arrays["u"][inactive_dofs],[0,0])
    assert not np.intersect1d(inactive_dofs,arrays["fixed_dofs"]).size
    np.testing.assert_array_equal(arrays["u"][arrays["fixed_dofs"]],0)
    assert abs(result["strain_energy_N_mm"]-result["integrated_strain_energy_N_mm"]) <= 1e-10*result["strain_energy_N_mm"]
    assert abs(result["energy_balance_error_N_mm"]) <= 1e-10*result["input_work_N_mm"]
    stress=arrays["stress_gauss_MPa"]; strain=arrays["strain_gauss"]
    # Check recovery in physical tensor form independently of the stiffness B.
    lam=1*.3/(1.3*.4); mu=1/(2*1.3)
    expected=np.stack((2*mu*strain[:,:,0]+lam*(strain[:,:,0]+strain[:,:,1]),
                       2*mu*strain[:,:,1]+lam*(strain[:,:,0]+strain[:,:,1]),mu*strain[:,:,2]),axis=-1)
    np.testing.assert_allclose(stress,expected,rtol=1e-10,atol=1e-16)
    np.testing.assert_array_equal(geometry.solid,solid_before)
    assert geometry.metadata == metadata_before
    again,second=analyze(geometry,task,solver)
    for key in arrays:
        np.testing.assert_array_equal(arrays[key],second[key])
    for key in ("R_in_N","q_out_mm","strain_energy_N_mm"):
        assert again[key] == result[key]


def test_unattached_port_is_rejected_without_reweighting():
    geometry=_geometry(); task,solver=_task_solver()
    geometry.metadata["region_tags"]["output"]["points_mm"]=[[2,0],[2,2]]
    with pytest.raises(AnalysisError,match="Every output port node"):
        analyze(geometry,task,solver)


@pytest.mark.parametrize("change", ["quadrature","plane_stress","auxiliary_spring","workpiece","unknown_field",
                                    "wrong_port_tag","empty_constraints","unknown_qualification"])
def test_unsupported_semantics_are_rejected(change):
    geometry=_geometry(); task,solver=_task_solver()
    if change == "quadrature": solver["quadrature"]="lobatto_3x3"
    elif change == "plane_stress": task["material"]["formulation"]="plane_stress"
    elif change == "auxiliary_spring": task["input_auxiliary_spring_N_per_mm"]=1.
    elif change == "workpiece": task["workpiece"]={"radius_mm":1.}
    elif change == "wrong_port_tag": task["input"]["tag"]="output"
    elif change == "empty_constraints": task["constraints"]=[]
    elif change == "unknown_qualification": task["qualification_criteria"]={"unknown":1.}
    else: task["lf_stiffness_path"]="unsupported"
    with pytest.raises(AnalysisError):
        analyze(geometry,task,solver)


@pytest.mark.parametrize("E,nu,hx,hy,t",[(0,.3,1,1,1),(1,.5,1,1,1),(1,.3,-1,1,1),(1,.3,1,1,float("nan"))])
def test_invalid_material_or_element_dimensions(E,nu,hx,hy,t):
    with pytest.raises(AnalysisError):
        element_stiffness(E,nu,hx,hy,t)
