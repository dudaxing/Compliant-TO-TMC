"""Source/math/interface contract only; no imports of mechanics or arrays."""
from pathlib import Path
from hashlib import sha256
import json

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT=Path(__file__).resolve().parent
BASE='01b5078acaf76fdaabfbdf214da9db16056467bc'
evidence={
    'hf_repo/src/hf_eval/split_displacement.py':dict(sha256='6738ace4b617b0103b6d266d9b62b68343cc6d053c52246b6ca0344f72e9dc6e',lines={'measurement':'25-52','interface_and_warm_validation':'55-109','initial_durable_and_timer':'113-128','lift_constraint_force':'154-189','predictor':'228-246','fresh_base_acceptance':'247-262','bounded_trials':'265-296','advance_rollback_commit':'299-333','path_order_and_result':'335-364'}),
    'hf_repo/src/hf_eval/native_mean.py':dict(sha256='379856e9b3fc226928361a09d4028c60af7aeabf74b19024d227f806cf351998',lines={'public_zero_start_and_full_task_match':'113-146','fresh_assembly_temporary_cache':'155-175','accepted_snapshot_capture':'177-207','controller_call':'209-212','metadata_parent_completion':'215-253','accepted_only_writer':'256-293'}),
    'hf_repo/src/hf_eval/displacement.py':dict(sha256='fbae379e37f0816edcdebd765bcae73a525c8709c2cb8f798146e497c9a4a386',lines={'settings':'23-56','ports_not_renormalized':'79-91','augmented_matrix':'105-114','general_LU_and_signs':'117-144'}),
    'hf_repo/src/hf_eval/split_state.py':dict(sha256='457e78f7f9dfa55566800915637af3b2e5ea38db969d7da98c8294efad69538e',lines={'two_owned_readonly_arrays':'26-45','lossy_display_not_mechanics':'51-62'}),
    'hf_repo/src/hf_eval/split_affine.py':dict(sha256='cefbf2679143d9f76eabe910f0602d075757b4c22e4d82cf419b417ca71336ba',lines={'bitwise_comparison':'25-28'}),
    'hf_repo/src/hf_eval/native_project.py':dict(sha256='4f1b4f772938bb870e8784fac881bad9a16f004fabf3b6e91ea9d2701c7601bc',lines={'parent_full_ordered_path':'71-84','reference_geometry_and_fixed_body':'90-107'}),
    'functional_views/native_alpha_partial_20261011/complete_001/author/UNLOAD_COST_AUDIT.md':dict(sha256='6729e3fd28882fdcdfec04e5ac34f3ff17522a73db95dd87a7ef398fe39f72dd',lines={'saved_failure_and_source_semantics':'whole ordinary audit; no array values re-read'}),
    'functional_views/native_alpha_partial_20261011/complete_001/author/unload_cost_audit.json':dict(sha256='aeaeaef7d8909e210f61e6d5a561c6c77d8dcfb2fb21164271c4c841d0bf7a78',lines={'saved_failure_identity':'ordinary inventory only'})}
for name,item in evidence.items():
    assert sha256((ROOT/name).read_bytes()).hexdigest()==item['sha256'],name

report=dict(
    status='completed_source_math_interface_audit_not_implemented_or_numerically_validated',
    source_snapshot_commit=BASE,formal_repository=ROOT.as_posix(),proposed_stage='M-RESUME1',
    source_evidence=evidence,
    scope='Source/plain-audit reading and symbolic algebra only. No NPZ decode, HF/candidate import, scientific calls, tests, force/tangent/HP/observer/solver, new scientific arithmetic or plots. No formal repository mutation.',
    proposed_minimal_transport=dict(
        initial_parameter_keyword_default=0,
        nonzero_option_only='ordered_cycle with explicitly supplied saved ORIGINAL accepted state, originalR, first absolute target equal to initial_parameter and at least one remaining original target',
        current_case=dict(parent_original_index=13,initial_parameter_mm=1.20,next_original_index=14,next_absolute_target_mm=1.15,target_origin=0,source_parent_status='failed/time_limit,14accepted,noacceptedunload'),
        lift='Use existing binary64 impose rule L(p)=L0 if p==0 else L0+p*H; expected initial lift at p0 must match saved lift bitwise. Initial fluctuation copied unchanged; both fixed split arrays remainzero. Never u_display/rebase/recombine.',
        durable_start='state_u=saved.copy(), state_R=originalR, state_s=p0, state_K=None',
        initial_anchor_policy='First nonzero anchor is validate-only: freshF/T and original force-relative/mean gates. If gates fail, initial_state_not_equilibrated before any corrector/trial/commit. If pass, unchanged imported state/R accepted and fresh matchingK captured. Defaultp0=0 behavior unchanged.',
        caches='No saved total_matrix/tangent/temp last_tangent import. First anchor derives fresh matched arrays/tensors/matrix through existing assemble/capture. Accepted caches copy/readonly asbefore.',
        settings='Restore exact savedparent settings, response_mode,tangent_mode,initial_guess; only time_limit may differ under a separate future approved card. No resource amount proposed here.',
        parent_task='Validate exact requestedsuffix of original fulltask path; retain same physical/task/geometry/model identity. Do not rewrite parentpath into [1.20,1.15] because native task schema requires undeformedfullpath starting0.',
        indices='Child local0/1 mapped to original13/14; anchor leg resume_origin with parent_leg loading, endpointleg unloading with parent_leg unloading. Anchor isnot undeformedorigin or freshloading.',
        completion='Keep originalfailed result immutable. Newsegment_completed/requested_endpoint may be actual; full_original_path_completed/task_target_executed remainfalse until separate explicitassociation evidence, never automatic child-success upgrade. NoHP/pressure/grip/HF5 transfer.'),
    symbolic_residuals={
        'physical_displacement':'u_exact=D(L)+D(w), fixedDOFs0; each storedcomponent binary64',
        'mean_constraint':'c=CompensatedDot(b_in,L,w,-target_origin,-p); current continuation target_origin=0 gives original exact D(p)',
        'free_force':'r_f=[f_int(L,w)+k_out*b_out*q_out-b_in*R]_free',
        'q_out':'CompensatedDot(b_out,L,w)',
        'J_augmented':'[[K_ff+k_out*b_out_f*b_out_f^T, -b_in_f],[b_in_f^T,0]]',
        'corrector':'J_augmented*(delta_w_f,delta_R)=(-r_f,-c)',
        'predictor_force_rhs':'-[K*DeltaL+k_out*b_out*Deltaq_out]_free',
        'predictor_mean_rhs':'-CompensatedDot(b_in,L_new,w_old,-target_origin,-p_new)',
        'predictor_current_zero_shape':'DeltaL=0 so forceRHS0, meanRHS=originalabsoluteD(p_new)-measuredoldmean; no manual -.05 literal',
        'port_projection':'w_free += meanRHS*b_free/(b_free^T*b_free), apply KKT deltaR but deliberatelynot tangentdelta_w; existing exactmean pivot feasibility follows',
        'R_sign':'Actuator onmodel is +b_in*R; augmented lastcolumn -b_in. Descending target doesnotflip R sign or takeabs; deltaR followsunsymmetric system.',
        'units':'K N/mm, w/L/p mm, R N; mixedunit LU backwarderror remainsdiagnostic, notenergy or newacceptancegate'},
    precision_findings=[
        'Using originalbinary64absolute p values withtarget_origin0 preserves old `_dot` subtractionterms andphysicaltargetidentity. Nominaldecimal -.05 or rounded displayR isnot interchangeable with originalstoredtargets/R.',
        'Even when signedoffset subtraction can be exact bySterbenz for thisboundedclosepair, an offset API needs its own representationalcontract. It isunnecessary here; absolute initial_parameter retainsoriginalpath interpretation and avoids new targetorigin rebasing.',
        'Generic savedlift is L(p0), not necessarily lift_origin. Reuse identical impose operationincludingp0==0 branch. Origin/shape validation, fixedDOFs andsavedfluctuation checks remainexistingconstraints.',
        'Initial validate-only uses exactly existing scientifictolerances, notnewthresholds. Transport/source/shape/stateindex andbitwiseidentity areinterfaceadmissibility, notnewsciencequalification.',
        'Fresh tangent remainsfullDOF/unsym andparameterinitializationsame asparent. No conservativeenergy/Hessian/SPD assumption or allcolumnreference qualification ismade.'
    ],
    rollback_contract=[
        'Before each unacceptedNewtonattempt snapshot bothsplitarrays,R,p andKobject. Commit onlyafter newtonreturns qualifiedbase; trials mutate onlylocalcandidate/R. Failedattempt preserves durablebeforeacceptedstate andKobjectidentity, notnewKnumericalhash proof.',
        'First anchorinvalidbase stopsbefore corrector/commit, leaving importedstate/R/p andKNone. InvalidJ/time_limit duringfresh evaluate likewise cannot manufacture acceptedanchor or endpoint.',
        'Existing signedmidpoint bisection alreadyworks fordescendingabsolute parameters via (p-before_p)/2 and absincrement; keep settings/stoprules unchanged. Internaltrials/bisection are distinctfromexternalreruns.',
        'Acceptance/capture occurs before postaccept clock; callback/postaccept timefailure may leave an alreadyqualified acceptedstate. Do notclaim everyfailure returns allthewayto importedanchor, or temporarylast_tangent isrolledback. Saveonlyactualaccepted snapshots.',
        'Parent acceptedstate/resultfiles are immutable; any child failure isnew partialsegment evidence, notrewrite ofparentNOTPASS oroldwindow extension.'
    ],
    proposed_change_extent=['Small opt-in controller initialization/validation/first-anchor validation-only branch; defaultinitial_parameter0 andoldNewton/Armijo/LU/bisection math unchanged.',
                           'Public savedaccepted-state reader/continuation entry, exactparentpathsuffix andsettings restoration, minimal continuation metadata/index mapping; reuseexistingproject/assemble/capture/writer ratherthannewforce/tangentkernel.',
                           'No savedmatrix import, no fullparent loading replay, no alpha/mesh change, no newpressure/Hu formula or generalarbitrarywarmstart qualification.'],
    deferred=['Actualnewsource staticreview','Exactfutureinputdecode/resource contract','Directhumanapprovedboundednumericalcard','Actualinitialsame-state validation andunload result','Optionalparent-child association/independentreference/pressure/meshstability qualification'],
    authorization='This audit/contract grants no numerical execution, resource window, new decoding or scientific gate. No numerical budget is selected.',
    reviewer_actions=dict(NPZ_decode=0,HF_or_candidate_imports=0,scientific_calls=0,tests=0,plots=0,new_scientific_values=0,formal_repository_mutations=0))
out=EXT/'physical_basis.json'
with out.open('x',encoding='utf-8',newline='\n') as stream: stream.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

md='''# M-RESUME1：保存峰值下降续算的源码／数学合同

状态：`completed_source_math_interface_audit_not_implemented_or_numerically_validated`。正式源为 main `01b5078acaf76fdaabfbdf214da9db16056467bc`。这是源码、接口和符号推导，不是实现或数值验证；未读NPZ、导入HF、调用科学入口、运行测试/求解或绘图，未改正式仓库。全部source SHA/行号在同目录 physical_basis.json。

## 最近功能与选择

原 alpha5e−7 路径有14个接受原点/加载态，original index13为physical mean1.20 mm。原original index14卸载至1.15 mm因controller预算停止，没有卸载接受态。M-AVIEW1已显示这些缓存；不必重复长加载。最近功能是从原已接受峰值接续原第一下降目标，父结果NOT_PASS保持。

推荐新增 `initial_parameter=0` 这一小型显式选项，当前续算采用**原绝对参数** `[1.20,1.15]`，`target_origin=0`、`initial_parameter=1.20`。非零选项只用于ordered_cycle、有明确保存ORIGINAL接受态和R、首目标等于p0且至少还有一个原目标。原默认0分支和原路径合同保持。

控制器耐久初态应为 `(saved_split.copy(), original_R, p0, K=None)`，而非 `(saved_split, R, 0, None)`。首anchor目标等于当前参数，不做predictor；在原状态fresh F/T并只用原force-relative/mean容差核验，合格才接受原同字节anchor并capture匹配新K。不合格在任何corrector/trial/commit之前以initial_state_not_equilibrated关闭；不能默默修成另一初态。default p0=0 warm分支保持原行为。

## 精度和lift不变量

位移是两个存储binary64数组的精确和 `D(L)+D(w)`。不要将u_display、重新相加后的一个数组或显示舍入值作续算初态。初始R读取原JSON完整精度，不用报表显示舍入值。

generic lift满足既有impose：p=0时L0.copy，否则binary64 `L0+p*H`。warm保存lift须逐bit等于**L(p0)**，不一定等于截距L0；固定DOF的origin/shape与fluctuation仍为零。当前native mean的shape为零，但应沿同规则检查，不由图件反推数组。采用同一impose规则可保持firstanchor字节。

原 `_dot` 将lift/fluctuation乘积和target负项一起FMA补偿/fsum，最后才舍入。`target_origin=0`、原absolute p保留旧 `−0−p` 目标项与exact D(p)，不把目标改成`D(1.20)+D(硬编码−.05)`。接近binary64两数的减法可能符合Sterbenz，但无需引入新的signed-offset表示或rebase合同。

源码：split_displacement.py:25–52、55–109、154–189；split_state.py:26–62。

## 控制器数学及符号

令b为输入权重、o为输出权重，R是actuator-on-model multiplier，q=o·(L+w)。自由行残差和平均约束为

```
r_f = [f_int(L,w) + k_out o q - b R]_free
c   = CompensatedDot(b,L,w,-target_origin,-p)
A   = [[K_ff + k_out o_f o_f^T, -b_f], [b_f^T, 0]]
A [δw_f, δR]^T = [-r_f, -c]^T
```

K单位N/mm、w/L/p单位mm、R单位N。原general sparse LU和非对称K保持；不能改成对称Hessian或依据总能量二阶导。mixed-unit backward error只是已有诊断，不是新验收门。

跨目标predictor沿原代码：force RHS为 `−[K ΔL+k_out o Δq]_free`，mean RHS为 `−CompensatedDot(b,L_new,w_old,-d0,-p_new)`。当前shape0使ΔL=0；下降由原absolute p_new与旧mean的有符号差进入mean RHS，不手写−.05。R符号不因卸载翻转或取绝对值，δR由系统解决定，不预判其符号。

原port_projection仍只把mean RHS分配到b_f方向，不施加tangent δw，但施加同KKT δR；随后原pivot补偿feasible。Newton基点判定、J>0、固定scale Armijo与bounded backtracking不变。predictor/trial合格不等于接受平衡态。

源码：displacement.py:105–144；split_displacement.py:214–296。

## 公共接口、状态索引和缓存

native task完整path仍从0起并含原加载/回撤，native_mean目前要求targets匹配全部path。续算必须验证请求是该原路径suffix，保留原物理/task/geometry/model身份，不把父task改写为只有 `[1.20,1.15]`。新入口只传子路径与显式transport metadata；默认Mean/API/CLI行为不变。

child local original index0/1关联parent original13/14；首anchor leg为resume_origin并记录parent_leg loading，端点为unloading。首anchor不是undeformed origin或新加载，重测也不是原父路径重跑。

采用KNone与fresh首anchor，**不读取/复用保存total_matrix、tangent或失败过程的临时last_tangent**。原assemble/capture匹配stateSHA、复制并只读数组/tensor/matrix，writer只保存实际accepted，避免另造核。parent全部settings、response/tangent模式及initial_guess原样恢复；只有未来另行明确授权的time_limit可改变，本报告不选任何额度或新容差。

原父result与14态保持不变。child可以记录实际segment_completed/requested_endpoint；task_target_executed/full_original_path_completed不能由child success自动置true。父子完整路径关联及独立资格须另据实际证据，原24态/48HP不转移。

源码：native_project.py:71–84；native_mean.py:113–146、155–253、256–293。

## 回滚边界

未接受Newton尝试前保存split两数组、R、p及K对象；只在合格基点返回后提交。试探只改局部candidate/R，失败保持之前耐久accepted状态。首anchor不合格在修正/提交之前停止，仍是导入state/R/p与KNone。既有下降midpoint与abs increment规则已支持负增量，不必换二分算法或放门。

回滚证据是两数组/R bitwise、p相同、K对象身份，不是重做K数值证明。native_mean临时last_tangent不承诺随失败回滚。callback/postaccept clock发生在commit/capture之后，可能已有合格accepted；不能笼统宣称所有failure均回到最初seed。保存真实partial新段，不能把未接受trial补入文件或把旧窗口延长。

源码：split_displacement.py:299–364；native_mean.py:173–207、256–293；已有UNLOAD_COST_AUDIT同义证据保留。

## 最小范围及下一依赖

只准备opt-in初始参数/anchor验证、公共保存态读取与suffix/settings/metadata关联，复用原控制器和缓存writer。暂不做矩阵复用、重复加载、alpha/mesh改变、Hu公式修复、任意warmstart或压力资格。首anchor运输身份条件是接口合同；使用原生产容差，不增加新科学阈值。

随后必须审实际候选源码和精确读取范围，再准备有界局部执行卡。此审计没有实际实现、数组核验、初态F/T或卸载值，没有资源预算、测试通过、continuation成功或新solve授权。
'''
md_path=EXT/'CONTINUATION_CONTRACT.md'
with md_path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(md)
print(json.dumps(dict(status=report['status'],JSON=out.as_posix(),JSON_SHA256=sha256(out.read_bytes()).hexdigest(),MD=md_path.as_posix(),MD_SHA256=sha256(md_path.read_bytes()).hexdigest()),ensure_ascii=False))
