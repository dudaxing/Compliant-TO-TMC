"""HR1 bounded local contract; invoked once by the frozen probe, not pytest.

Module import is standard-library-only. Scientific objects arrive from the
declared probe runtime. This is not the full kernel/AD/69+63 qualification.
"""
from __future__ import annotations

import ast
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


PROTOCOL = "F-REUSE1"
RUN_ID = "force_reuse_001"
C1_KERNEL_SHA = "88d57ed77565963d8cc367c18398b11b30f8f1e0e335c7dcdbc3d68702ecb6bf"
ARITHMETIC_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
HP_SHA = "af5fedf386fea8e77474363abd5798932250830f8c6d6b09b319c8d7c4f72869"
RESULT_SHA = "f05123413d64a93a1535d6e6c30a67dfa799de6e0e5565d8903211c9bf14028e"
FIELDS = ("F", "G", "Hu", "J", "B", "delta")
OUTPUT_FIELDS = frozenset(("residual", "material_residual", "regularization_residual",
    "material_energy", "stress_first_piola", "stress_second_piola", "small_branch",
    "arithmetic_supported", *FIELDS, *(f+s for f in FIELDS for s in ("_hi", "_lo"))))
FORCE_KEYS = {"total_force": "internal_decimal", "material_force": "material_internal_decimal",
              "regularization_force": "regularization_internal_decimal"}
FORCE_LIMITS = {"total_force": "1e-11", "material_force": "1e-9", "regularization_force": "1e-9"}
GROUPS = ("valid_first_three", "valid_last_three", "original_mixed", "mixed_negative_J",
          "mixed_large_input", "mixed_nan_input", "mixed_large_coefficient", "mixed_nan_coefficient")


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value, *, replace=False):
    path = Path(path)
    target = path.with_name(path.name+".pending") if replace else path
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    if replace:
        os.replace(target, path)


def record_file(path, directory, status="pass"):
    return dict(path=Path(path).relative_to(directory).as_posix(), bytes=Path(path).stat().st_size,
                sha256=sha(path), status=status)


def dump_ast(node):
    return ast.dump(node, include_attributes=False)


def static_contract(root):
    """Read only: attest the already derived tree; never apply its patch."""
    oldpath = root/"C1/source/hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
    newpath = root/"R1/source/hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
    require(sha(oldpath) == C1_KERNEL_SHA, "C1 baseline kernel identity")
    for source in ("C1", "R1"):
        require(sha(root/source/"source/hf_repo/src/hf_eval/compensated_invariants.py") == ARITHMETIC_SHA,
                "arithmetic byte identity")
    a, b = (ast.parse(p.read_text(encoding="utf-8")) for p in (oldpath, newpath))
    af = {n.name:n for n in a.body if isinstance(n, ast.FunctionDef)}
    bf = {n.name:n for n in b.body if isinstance(n, ast.FunctionDef)}
    require(set(bf)-set(af) == {"_kinematics_vmap_axes", "_without_tangent_reusing"}, "new function scope")
    require(set(af) <= set(bf), "removed original function")
    for name in set(af)-{"_response", "_guarded_batch"}:
        require(dump_ast(af[name]) == dump_ast(bf[name]), "changed frozen function: "+name)
    old, new = af["_response"], bf["_response"]
    require([x.arg for x in new.args.kwonlyargs] == ["_kinematics_values"]
            and len(new.args.kw_defaults) == 1 and isinstance(new.args.kw_defaults[0], ast.Constant)
            and new.args.kw_defaults[0].value is None, "private cache keyword contract")
    oldargs = dump_ast(old.args)
    # A fresh AST object is used; no compiled/imported source is mutated.
    args = ast.parse(ast.unparse(new)).body[0].args
    args.kwonlyargs = []; args.kw_defaults = []
    require(oldargs == dump_ast(args), "original positional arguments changed")
    require([dump_ast(n) for n in old.body[2:]] == [dump_ast(n) for n in new.body[2:]],
            "response remainder AST changed")
    expected = ast.parse("values = (_kinematics(lift, fluctuation, grad, hessian, xp) "
                         "if _kinematics_values is None else _kinematics_values)").body[0]
    require(dump_ast(new.body[1]) == dump_ast(expected), "cache selection changed")
    require(dump_ast(new.body[0]) == dump_ast(old.body[0]), "response declaration changed")
    wrapper = ast.parse("def _without_tangent_reusing(values,lift,fluctuation,grad,hessian,weights,lam,mu,kr):\n"
        "    return _response(lift,fluctuation,grad,hessian,weights,lam,mu,kr,jnp,_kinematics_values=values)[1]\n").body[0]
    require(dump_ast(bf["_without_tangent_reusing"]) == dump_ast(wrapper), "cache wrapper changed")
    oa, ob = af["_guarded_batch"], bf["_guarded_batch"]
    copied = ast.parse(ast.unparse(ob)).body[0]
    evaluate = next(n for n in copied.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
    added = evaluate.body.pop(0)
    expected_added = ast.parse("if not tangent:\n"
        "    return jax.vmap(_without_tangent_reusing,\n"
        "        in_axes=(_kinematics_vmap_axes(),0,0,None,None,None,0,0,None))(\n"
        "            kinematics,lift,fluctuation,grad,hessian,weights,lam,mu,kr)\n").body[0]
    require(dump_ast(added) == dump_ast(expected_added), "accepted force branch is not prescribed reuse")
    require(dump_ast(copied) == dump_ast(oa), "guard/valid/reject/tangent branch changed")
    # All nonfunction statements, including jacfwd and strict jit wrappers,
    # are identical except the one explicitly named version value.
    def statements(tree):
        out = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                continue
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "KERNEL_VERSION" for t in node.targets):
                continue
            out.append(dump_ast(node))
        return out
    require(statements(a) == statements(b), "nonfunction/AD/compiler statement changed")
    version = next(n.value.value for n in b.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "KERNEL_VERSION" for t in n.targets))
    require(version == "p26_q1_split_invariants_hu_force_reuse_r1", "R1 version")
    return dict(status="pass", C1_kernel_sha256=sha(oldpath), R1_kernel_sha256=sha(newpath),
                arithmetic_sha256=ARITHMETIC_SHA, response_remainder_ast_unchanged=True,
                guard_reject_ad_unchanged=True, compiled_guard_executed=False)


def load_baseline(root, candidate):
    path = root/"C1/source/hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
    name = "hf_eval._force_reuse_c1_baseline"
    require(name not in sys.modules, "baseline already loaded")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "baseline loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == path.resolve() and sha(path) == C1_KERNEL_SHA,
            "actual baseline source differs")
    require(module.ci is candidate.ci and sha(module.ci.__file__) == ARITHMETIC_SHA,
            "baseline and candidate must share the bound identical arithmetic module")
    return module


def read_fixture(root, np):
    path = root/"data/inputs.npz"
    require(sha(path) == INPUT_SHA, "original numeric input identity")
    with np.load(path, allow_pickle=False) as archive:
        return {name:archive[name].copy() for name in archive.files}


def gather(fixture, np):
    cells = fixture["connectivity"]
    require(cells.shape == (1,4) and np.issubdtype(cells.dtype, np.integer), "one original cell required")
    edofs = (2*cells[...,None]+np.arange(2)).reshape(1,8)
    require(edofs.tolist() == [[0,1,2,3,6,7,4,5]], "original edofs changed")
    return edofs


def slice_tree(value, axes, index):
    if axes is None:
        return value
    if isinstance(axes, dict):
        require(set(value) == set(axes), "cache axes keys")
        return {key:slice_tree(value[key], axes[key], index) for key in axes}
    if isinstance(axes, tuple):
        require(len(value) == len(axes), "pair axes length")
        return tuple(slice_tree(v,a,index) for v,a in zip(value,axes))
    require(axes == 0, "only field axis zero may be mapped")
    return value[index]


def compare_array(np, actual, expected, label, *, finite_required=False):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape and a.dtype == b.dtype, label+": shape/dtype mismatch")
    if a.dtype == np.bool_:
        require(np.array_equal(a,b), label+": boolean mismatch")
    else:
        require(a.dtype == np.float64, label+": non-binary64 observation")
        require(np.array_equal(np.isnan(a),np.isnan(b)) and np.array_equal(np.isinf(a),np.isinf(b)),
                label+": nonfinite mask mismatch")
        if finite_required:
            require(np.isfinite(a).all() and np.isfinite(b).all(), label+": unexpected rejection")
        keep = ~np.isnan(a)
        require(np.array_equal(a.view(np.uint64)[keep],b.view(np.uint64)[keep]),
                label+": binary64 bit mismatch (including signed zero)")
    return dict(shape=list(a.shape),dtype=str(a.dtype),status="pass",signed_zero_checked=True)


def flatten_arrays(value, prefix=""):
    if isinstance(value, dict):
        return {key:array for name,child in value.items()
                for key,array in flatten_arrays(child,prefix+name+"__").items()}
    if isinstance(value, (tuple,list)):
        return {key:array for index,child in enumerate(value)
                for key,array in flatten_arrays(child,prefix+str(index)+"__").items()}
    return {prefix.rstrip("_"):value}


def save_arrays(probe, np, name, arrays):
    path = probe.output/name
    with path.open("xb") as stream:
        np.savez(stream, **arrays); stream.flush(); os.fsync(stream.fileno())
    record=record_file(path, probe.output)
    probe.summary.setdefault("local_artifacts",[]).append(record)
    probe.checkpoint()
    return record


def cases(np, candidate, fixture):
    from hf_eval.tmc_kernel import operators
    ops = operators(1.,1.)
    for key in ("grad","hessian","weights"):
        require(np.array_equal(ops[key],fixture[key]), "unit saved/common operator mismatch: "+key)
    xy = np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]],dtype=np.float64)
    x,y = xy.T
    zeros = np.zeros(8,dtype=np.float64)
    shear = lambda a:np.column_stack((a*y,np.zeros(4))).ravel()
    entries = [dict(name="identity",L=zeros.copy(),w=zeros.copy(),lam=2.,mu=3.,kr=0.),
        dict(name="shear_1_32",L=zeros.copy(),w=shear(1./32),lam=2.,mu=3.,kr=0.),
        dict(name="shear_1_8",L=zeros.copy(),w=shear(1./8),lam=2.,mu=3.,kr=0.),
        dict(name="extension_1_32",L=zeros.copy(),w=np.column_stack((x/32,np.zeros(4))).ravel(),lam=2.,mu=3.,kr=0.),
        dict(name="bilinear",L=zeros.copy(),w=np.column_stack((x*y/8,-x*y/16)).ravel(),lam=0.,mu=0.,kr=1./4)]
    edofs = gather(fixture,np)[0]
    entries.append(dict(name="unit__near_rotation",L=fixture["u_lift"][edofs],
        w=fixture["u_fluctuation"][edofs],lam=float(fixture["lam"][0]),mu=float(fixture["mu"][0]),
        kr=float(fixture["kr"])))
    return entries,ops,xy


def numpy_responses(probe,np,c1,r1,fixture):
    entries,ops,xy = cases(np,r1,fixture)
    expected_axes = {**{name:0 for name in FIELDS},"near":0,"supported":None,
        "pairs":{**{name:(0,0) for name in FIELDS},"near":0,"supported":None}}
    require(r1._kinematics_vmap_axes() == expected_axes,"actual production cache axes")
    rows=[]; artifacts=[]
    for names in [[index] for index in range(6)]+[[1,2,3]]:
        selected=[entries[i] for i in names]
        L=np.stack([x["L"] for x in selected]); w=np.stack([x["w"] for x in selected])
        cached=r1._kinematics(L,w,ops["grad"],ops["hessian"],np)
        label="_".join(entry["name"] for entry in selected)
        if not bool(cached["supported"]) or not np.all(cached["J"]>0):
            save_arrays(probe,np,"numpy_"+label+"_rejected_kinematics.npz",flatten_arrays(cached))
        require(bool(cached["supported"]) and np.all(cached["J"]>0),"valid NumPy case rejected")
        old_rows=[];new_rows=[]
        for index,entry in enumerate(selected):
            args=(L[index],w[index],ops["grad"],ops["hessian"],ops["weights"],
                  entry["lam"],entry["mu"],entry["kr"],np)
            old=c1._response(*args)[1]
            new=r1._response(*args,_kinematics_values=slice_tree(cached,expected_axes,index))[1]
            old_rows.append(old);new_rows.append(new)
        artifacts.append(save_arrays(probe,np,"numpy_"+label+".npz",
            flatten_arrays(dict(C1=old_rows,R1=new_rows))))
        require(all(set(row)==OUTPUT_FIELDS for row in old_rows+new_rows),"26-field contract")
        old={key:np.stack([row[key] for row in old_rows]) for key in OUTPUT_FIELDS}
        new={key:np.stack([row[key] for row in new_rows]) for key in OUTPUT_FIELDS}
        checks={key:compare_array(np,new[key],old[key],key,finite_required=True) for key in sorted(OUTPUT_FIELDS)}
        require(new["arithmetic_supported"].shape==(len(selected),)
                and np.all(new["arithmetic_supported"]==1),"element support contract")
        rows.append(dict(cases=[entry["name"] for entry in selected],status="pass",fields=checks))
    # A valid geometric guard does not license out-of-range material exp(-5J).
    w=np.column_stack((99*xy[:,0],np.zeros(4))).ravel(); L=np.zeros(8)
    cached=r1._kinematics(L[None],w[None],ops["grad"],ops["hessian"],np)
    if not bool(cached["supported"]) or not np.all(cached["J"]==100):
        save_arrays(probe,np,"numpy_J100_bad_kinematics.npz",flatten_arrays(cached))
    require(bool(cached["supported"]) and np.all(cached["J"]==100),"J=100 geometric domain")
    with np.errstate(all="ignore"):
        args=(L,w,ops["grad"],ops["hessian"],ops["weights"],2.,3.,0.,np)
        old=c1._response(*args)[1]
        new=r1._response(*args,_kinematics_values=slice_tree(cached,expected_axes,0))[1]
    artifacts.append(save_arrays(probe,np,"numpy_J100_rejection.npz",flatten_arrays(dict(C1=old,R1=new))))
    require(old["arithmetic_supported"]==new["arithmetic_supported"]==0,
            "cached kinematics widened material support")
    rejected={k:compare_array(np,new[k],old[k],"J100/"+k) for k in sorted(OUTPUT_FIELDS)}
    return dict(status="pass",rows=rows,material_rejection=dict(status="pass",fields=rejected),artifacts=artifacts)


def selector_boundaries(np,c1,r1):
    rows=[]
    for field,bound in (("B",1./16),("delta",1./64)):
        for sign in (-1.,1.):
            B=np.zeros((3,2,2));delta=np.zeros(3)
            values=sign*np.array([np.nextafter(bound,0.),bound,np.nextafter(bound,np.inf)])
            if field=="B":B[:,0,1]=values
            else:delta[:]=values
            for kernel in (c1,r1):
                actual=kernel._small_invariant_branch(kernel.ci.dd_from(B,np),kernel.ci.dd_from(delta,np),np)
                require(np.array_equal(actual,[True,True,False]),"selector inner/equal/outer")
                if field=="B":
                    high=np.zeros((2,2));low=np.zeros_like(high)
                    high[0,1]=sign*bound;low[0,1]=sign*2.**-60
                    actual=kernel._small_invariant_branch((high,low),kernel.ci.dd_const(0.,np),np)
                else:
                    actual=kernel._small_invariant_branch(kernel.ci.dd_from(np.zeros((2,2)),np),
                        (np.asarray(sign*bound),np.asarray(sign*2.**-60)),np)
                require(not bool(actual),"selector lost boundary low part")
            rows.append(dict(field=field,sign=sign,status="pass",expected=[True,True,False],low_outside=False))
    return dict(status="pass",backend="NumPy only",extra_jit_count=0,rows=rows)


def micro_inputs(np,r1,fixture):
    entries,ops,xy=cases(np,r1,fixture)
    output=[]
    for ids in ([0,1,2],[3,4,5],[1,2,3],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]):
        selected=[entries[i] for i in ids]
        output.append([np.stack([e["L"] for e in selected]),np.stack([e["w"] for e in selected]),
            ops["grad"].copy(),ops["hessian"].copy(),ops["weights"].copy(),
            np.asarray([e["lam"] for e in selected]),np.asarray([e["mu"] for e in selected]),np.asarray(0.)])
    output[3][1][1]=np.column_stack((-2*xy[:,0],np.zeros(4))).ravel()
    output[4][1][1,:]=2.**401
    output[5][1][1,:]=np.nan
    output[6][5][1]=2.**401
    output[7][5][1]=np.nan
    for values in output:
        require([a.shape for a in values]==[(3,8),(3,8),(9,4,2),(4,2,2),(9,),(3,),(3,),()],"fixed micro signature")
        require(all(a.dtype==np.float64 for a in values),"fixed micro dtype")
    return output


def run_micro(probe,np,jax,jnp,c1,r1,fixture):
    def original(L,w,g,h,weights,lam,mu,kr):
        fields=jax.vmap(lambda a,b:c1._kinematics(a,b,g,h,jnp))(L,w)
        support=jnp.all(fields["supported"])
        valid=support & jnp.all(fields["J"]>0) & c1._coefficient_support(weights,lam,mu,kr,jnp)
        return dict(fields=fields,global_supported=support,valid=valid)
    def reused(L,w,g,h,weights,lam,mu,kr):
        batch=r1._kinematics(L,w,g,h,jnp)
        fields=jax.vmap(lambda values:values,in_axes=(r1._kinematics_vmap_axes(),))(batch)
        valid=batch["supported"] & jnp.all(batch["J"]>0) & r1._coefficient_support(weights,lam,mu,kr,jnp)
        return dict(fields=fields,global_supported=batch["supported"],valid=valid)
    inputs=micro_inputs(np,r1,fixture)
    device=[tuple(jnp.asarray(value) for value in row) for row in inputs]
    jax.block_until_ready(device)
    compiled={}
    for name,function in (("C1",original),("R1",reused)):
        fn=jax.jit(function,compiler_options=c1.COMPILER_OPTIONS)
        traced=probe.step("local."+name+".trace",lambda fn=fn:fn.trace(*device[0]))
        lowered=probe.step("local."+name+".lower",lambda traced=traced:traced.lower())
        compiled[name]=probe.step("local."+name+".compile",
            lambda lowered=lowered:lowered.compile(compiler_options=c1.COMPILER_OPTIONS))
    rows=[]
    for index,name in enumerate(GROUPS):
        observed={}
        for version in ("C1","R1"):
            value=probe.step("local."+name+"."+version+".call",
                lambda version=version,index=index:compiled[version](*device[index]))
            probe.step("local."+name+"."+version+".synchronize",lambda value=value:jax.block_until_ready(value))
            observed[version]=jax.tree.map(np.asarray,value)
        a,b=observed["C1"],observed["R1"]
        artifact=save_arrays(probe,np,"micro_"+name+".npz",flatten_arrays(observed))
        require(a["global_supported"].shape==b["global_supported"].shape==(),"global support must be scalar")
        require(bool(np.all(a["fields"]["supported"]))==bool(b["global_supported"]),"all(K_e) != K")
        require(bool(a["global_supported"])==bool(b["global_supported"]),"global kinematic support mismatch")
        require(bool(a["valid"])==bool(b["valid"])==(index<3),"original valid expression mismatch")
        require(np.all(b["fields"]["supported"]==b["global_supported"]),"cached scalar not broadcast consistently")
        require(np.array_equal(b["fields"]["pairs"]["supported"],b["fields"]["supported"]),"nested cache scalar mismatch")
        if bool(b["valid"]):require(np.all(a["fields"]["supported"]),"legal branch local support")
        checks={}
        for field in FIELDS:
            checks[field]=compare_array(np,b["fields"][field],a["fields"][field],name+"/"+field)
            for part,label in enumerate(("hi","lo")):
                key=field+"_"+label
                checks[key]=compare_array(np,b["fields"]["pairs"][field][part],a["fields"]["pairs"][field][part],name+"/"+key)
        checks["near"]=compare_array(np,b["fields"]["near"],a["fields"]["near"],name+"/near")
        checks["pairs_near"]=compare_array(np,b["fields"]["pairs"]["near"],a["fields"]["pairs"]["near"],name+"/pairs.near")
        rows.append(dict(name=name,status="pass",valid=bool(b["valid"]),global_supported=bool(b["global_supported"]),
            C1_element_supported=a["fields"]["supported"].tolist(),R1_cached_supported=b["fields"]["supported"].tolist(),
            fields=checks,artifact=artifact))
        probe.summary["micro_progress"]=dict(completed_groups=index+1,completed_calls=2*(index+1),rows=rows)
        probe.checkpoint()
    return dict(status="pass",micro_graph_count=2,micro_call_count=16,group_count=8,groups=rows,
                compiled_full_guard_executed=False,constitutive_response_executed=False,
                kr="fixed legal scalar 0.0: kinematics/guard only; real NumPy case kr values retained")


def d(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values),Decimal(0)).sqrt()


def reference_data(root,fixture):
    directory=root/"provenance/force_reference/unit__near_rotation"
    hp_path,result_path=directory/"hp_0.json",directory/"result.json"
    require(sha(hp_path)==HP_SHA and sha(result_path)==RESULT_SHA,"saved force-reference identities")
    hp=json.loads(hp_path.read_text(encoding="utf-8"))
    result=json.loads(result_path.read_text(encoding="utf-8"))
    freeze=json.loads((root/"data/input_freeze.json").read_text(encoding="utf-8"))
    require(freeze["input_sha256"]==INPUT_SHA and freeze["case"]=="unit__near_rotation"
            and freeze["level"]==.125 and freeze["force_scale_per_length"]==100.,"SF input authority")
    vectors={p:{name:[Decimal(value) for value in hp[p][key]] for name,key in FORCE_KEYS.items()} for p in ("80","120")}
    require(all(len(v)==8 and all(x.is_finite() for x in v) for row in vectors.values() for v in row.values()),"reference vector domain")
    fixed=set(map(int,fixture["fixed_dofs"]))
    require(all(0<=index<8 for index in fixed),"fixed DOF range")
    with localcontext() as context:
        context.prec=120
        total=vectors["80"]["total_force"]
        sf=max(norm([v for i,v in enumerate(total) if i in fixed]),norm([v for i,v in enumerate(total) if i not in fixed]),
            Decimal("1e-8")*d(freeze["force_scale_per_length"])*max(abs(d(freeze["level"])),Decimal("1e-6")))
        original=next(row for row in result["directions"] if row["direction"]==0)
        require(sf==Decimal(original["force_scale"])==Decimal("1.2500E-7"),"original force scale changed")
        denominators={name:sf if name=="total_force" else max(norm(vectors["80"][name]),Decimal("1e-12")*sf) for name in FORCE_KEYS}
        checks=[]
        for name in FORCE_KEYS:
            value=norm([a-b for a,b in zip(vectors["80"][name],vectors["120"][name])])/denominators[name]
            passed=value<=Decimal("1e-40")
            checks.append(dict(name=name,value_decimal=str(value),denominator_decimal=str(denominators[name]),
                limit_decimal=str(Decimal("1e-40")),status="pass" if passed else "not_pass",**{"pass":passed}))
    return vectors,sf,denominators,dict(status="pass" if all(row["pass"] for row in checks) else "not_pass",
        reference_checks=checks,force_scale_decimal=str(sf),precision=120,
        hp_sha256=HP_SHA,result_sha256=RESULT_SHA,input_sha256=INPUT_SHA,new_hp_evaluations=0)


def force_reference_gates(root,np,outputs):
    fixture=read_fixture(root,np)
    edofs=gather(fixture,np)[0]
    hp,sf,denominators,reference=reference_data(root,fixture)
    require(reference["status"]=="pass","saved HP80/120 reference disagreement")
    checks=[];vectors={}
    with localcontext() as context:
        context.prec=120
        for name,field in (("total_force","residual"),("material_force","material_residual"),
                           ("regularization_force","regularization_residual")):
            value=np.asarray(outputs[field])
            require(value.shape==(1,8) and value.dtype==np.float64 and np.isfinite(value).all(),"force output shape/domain")
            # One element with a bijective edofs map: exact permutation, no
            # floating summation and no deletion of constrained reactions.
            assembled=[Decimal(0)]*8
            for local,global_dof in enumerate(edofs):assembled[int(global_dof)]+=d(value[0,local])
            vectors[name]=[str(v) for v in assembled]
            error=norm([a-b for a,b in zip(assembled,hp["80"][name])])/denominators[name]
            limit=Decimal(FORCE_LIMITS[name]);passed=error<=limit
            checks.append(dict(name=name,value_decimal=str(error),denominator_decimal=str(denominators[name]),
                limit_decimal=str(limit),status="pass" if passed else "not_pass",**{"pass":passed}))
    return dict(schema="hf-force-reuse-reference-gates-1",protocol=PROTOCOL,run_id=RUN_ID,
        status="fixed_force_three_reference_gates_pass" if all(row["pass"] for row in checks) else "not_pass",
        count=3,checks=checks,reference_checks=reference["reference_checks"],force_scale_decimal=str(sf),
        hp_sha256=HP_SHA,result_sha256=RESULT_SHA,input_sha256=INPUT_SHA,edofs=edofs.tolist(),
        global_internal_decimal=vectors,includes_fixed_dofs=True,new_hp_evaluations=0,
        precision=120,scientific_admission=False)


def run_local_contract(probe,np,jax,jnp,c1,r1,fixture,static_result):
    path=probe.output/"contract.json"
    contract=dict(schema="hf-force-reuse-contract-1",protocol=PROTOCOL,run_id=RUN_ID,status="running",
        source=str(probe.source),source_manifest_sha256=probe.summary["source_manifest_sha256"],
        harness=probe.summary["harness"],arithmetic_harness=probe.summary["arithmetic_harness"],
        runtime_identity=probe.summary["runtime_identity"],static=static_result,
        micro_graph_count=0,micro_call_count=0,group_count=8,groups=[],scientific_admission=False,
        local_structure_equivalence_pass=False,full_kernel_ad_qualification=False)
    write_json(path,contract,replace=True)
    try:
        contract["numpy"]=probe.step("local.numpy26",lambda:numpy_responses(probe,np,c1,r1,fixture),describe=lambda v:v)
        write_json(path,contract,replace=True)
        contract["selector"]=probe.step("local.selector_numpy",lambda:selector_boundaries(np,c1,r1),describe=lambda v:v)
        reference=probe.step("local.reference_agreement",lambda:reference_data(probe.root,fixture)[3],describe=lambda v:v)
        contract["reference"]=reference
        require(reference["status"]=="pass","saved reference agreement failed")
        write_json(path,contract,replace=True)
        micro=run_micro(probe,np,jax,jnp,c1,r1,fixture)
        contract.update(micro_graph_count=micro["micro_graph_count"],micro_call_count=micro["micro_call_count"],
            groups=micro["groups"],micro=micro,status="local_structure_equivalence_pass",local_structure_equivalence_pass=True)
        write_json(path,contract,replace=True)
    except Exception as error:
        contract.update(status="failed",error=dict(type=type(error).__name__,message=str(error)))
        write_json(path,contract,replace=True)
        raise
    return record_file(path,probe.output,status=contract["status"])
