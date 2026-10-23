"""Write the finite plan and a conceptual figure, without HF/scientific input."""
import json
from pathlib import Path

A = Path(__file__).resolve().parent

def write(name, content):
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False)
    (A/name).write_bytes((content.strip()+'\n').encode('utf-8'))

methods = [
    ('V01', '独立非对称dense oracle；绝对q、非零段起点、求和广义力及多段状态。', 4),
    ('V02', '非零fresh正确/坏R/mean/P、非有限q/q-lift失配；不得修复。', 6),
    ('V03', '非零锚点后预定invalid_J且maxdepth0；两split/q/P/R原位回滚。', 1),
    ('V04', '真实direct四P与prefix→child→grandchild及给q参考按原目标交叉。', 0),
    ('V05', '两次新API fresh位身份/check1；完整前缀/索引、nonclock、谱系及显式固定树路径迁移。', 0),
    ('V06', '负P递增时每态SP/g界仍用rootP0；段/根增量分别记录。', 0),
    ('V07', '旧fixed父力控前缀兼容，旧默认位移controller仍拒非opt-in body lift。', 1),
    ('V08', 'fresh后预定第二次T constraint_failure；真实非零锚点partial与父树保持。', 1),
    ('V09', 'geometry/model/kernel pin/lift/w/state身份六项拒绝，F/T前invalid_saved_state。', 6),
    ('V10', 'schema/probe/partial/非末原目标/缺原目标覆盖五项源语义拒绝。', 5),
    ('V11', '无append/改P0/改旧中间P/缺前缀/重复/下降/NaN/Inf八项扩展拒绝。', 8),
    ('V12', 'clock=0/NaN、旧output/force父内output/root固定父内output五项拒绝；签名不暴露q/非clock覆盖。', 5),
]
table = '\n'.join('|'+a+'|'+b+'|'+str(c)+'|' for a,b,c in methods)
write('VALIDATION_PLAN.md', f'''
# 有限小模型验证方案（未实现/未执行）

12个新非参数化方法，最多7条真实16单元/25节点/50场DOF路径；reduced含q/R为37×37。所有方法共享一次夹具，不重跑旧17项全套。依据与源码行号见[独立验证备忘](author/VALIDATION_AUDIT.md)、[数学备忘](author/MATH_AUDIT.md)；两份备忘是设计输入，最终字段/路径/错误约定以[接口合同](INTERFACE_SPEC.md)及本页为准。

## 一次夹具和7条路径

沿用已验证4×4 Q1夹具：域2×2 mm、h.5、t2、E1/ν.3、plane strain、α1e−4/γ1e−6/Lr2、mean峰.0005 mm；原工件cell14/nodes17,18,22,23、原端口/支撑/重叠去重。小夹具不是正式r9的替代物理，正式条件保持原样。本准备没有生成夹具。

1. 固定父mean从0→.0005，原mm最小步长.0005/16。
2. 同父给q参考[0,.000125,.00025,.0005]，新计算出P0/P1/P2/P3；有限、非零P0、strict increase且均负是预设夹具检查，不满足即停，不调整目标。历史三点数值只作可行性依据，不作为新四点载荷。
3. 原fixed父力控direct完整4P；共同Nmin=min(三个正ΔP)/16。
4. 同旧入口prefix两P，force_settings与direct相同。
5. 新API从prefix追加P2；完整列表[P0,P1,P2]，非零q来自力控源。显式fixed_parent_result指向新复制的同字节最小固定树，原pin须匹配。
6. 新API从child追加P3；完整列表[P0,P1,P2,P3]，验证新1.1源的二次准入，按child记录解析固定来源。
7. 从prefix单独受控partial：fresh接受后预定第二次T报constraint_failure，保存真实原锚点/失败，非物理失稳搜索。

七条每条controller最多60秒，共享tests480秒；不因错误新增或重试路径。只给力控P，不传参考q，不从参考终态热启动。新fixture源/父/result及split缓存的读取、复制和F/T尝试/完成数在未来唯一窗口逐项记录；本轮全为0。

## 12方法及调用上限

|ID|目的|有限代数/注入/拒绝调用上限|
|---|---|---:|
{table}

合计最多37次上述有限调用；V08是同一条真实partial，在真实路径轴与注入轴各记一次，不重复启动。V04–06只查共享实际输出，不另跑科学。正向new API的实际调用另如7路径清楚计数；方法数不等于求解数。V02低层非有限q用invalid_input、q-lift冲突用constraint_conflict；公共坏source用invalid_saved_state。V11新入口统一invalid_task_extension，不改变旧入口错误码。

## 预先门与成功条件

fresh保两split/state hash及q/P/R binary64字节，check1、无predictor/投影/修正；源树保持。每一真实接受态保原freeρF≤1e−9、bodyρP≤1e−9、SP=max(abs(P),abs(rootP0),Ffloor)、mean≤5e−14 mm、J>0/有限、global≤1e−6、rigid/zero≤8e−11 mm；root SP不能改为segment P。

direct与分段共同原目标：q差及全50DOF四split项fsum物理位移max差各≤1e−8 mm；R差≤max(1e−12 N,1e−7 abs(R_direct))。给q参考以同样位移界、按该参考R的同公式作另一次事后交叉。它们是预先功能比较界，不是严格误差上界、稳定性或新HP。fresh硬身份与端点工程界分开，不按结果收紧/放宽。

全部12方法/所有实际原门通过、1PNG一次检查/清理通过，才安装三份已测字节；任何非预期失败即停、不安装。预定typed拒绝和partial符合其断言才算验证成功，不能被当作外部重跑的理由。HP=0、save-time F/T=0，原material/Hu/total与R定义、false资格不升级。

新图只用这7路径产生的新缓存/普通结果：实际×1变形和明确倍数箭头、P–绝对q（标出非零锚点/段界）、R、三项同P差、全部base/trial残差及J/Hu/rootSP。一次六面板PNG与人工页，无正式r9新图或新HP。[候选资源/停止卡](L-CTIPFRESUME1_CARD.md)。
''')
write('CONTRACT.json', dict(stage='L-CTIPFRESUME1_candidate', status='not_approved_not_implemented_not_executed',
    production_modified=['hf_repo/src/hf_eval/split_guided_force.py','hf_repo/src/hf_eval/native_guided_force.py'],
    production_new=['hf_repo/src/hf_eval/native_guided_force_resume.py'], production_installs=3,
    other_existing_production_files_unchanged=55, new_test_files=1,
    public_entry='hf_eval.native_guided_force_resume.extend_native_guided_force',
    positional_arguments=['saved_force_result','full_extended_body_load_targets_half_N','output_directory'],
    keyword_arguments={'fixed_parent_result':None,'time_limit_seconds':60.,'on_accept':None},
    source_schemas=['hf-native-guided-force-1.0','hf-native-guided-force-1.1'], result_schema='hf-native-guided-force-1.1',
    root_scale='max(abs(P),abs(root_P0),Ffloor)',
    segment_anchor='Immediate successful force-parent last original P; exact fresh state/q/P/R',
    state_rule='lift[body_x] already equals absolute q; overwrite for candidates, never add twice',
    source_path_rule='Optional current fixed-parent path must match original raw/canonical pin; derive relative model/geometry; selected force split relative to immediate force result',
    scientific_closure_future_per_API={'opaque_model_hash_paths':1,'geometry_NPZ_decoded_masks':4,'force_state_NPZ_decoded_fields':2,'NPZ_paths':3,'ancestor_split_force_tangent_matrix_reads':0},
    small_model={'elements':16,'nodes':25,'field_DOF':50,'free_DOF':35,'mixed_shape':[37,37],
        'mean_peak_mm':.0005,'reference_q_mm':[0.,.000125,.00025,.0005],
        'force_targets':'New probe-derived finite negative strictly-increasing P0,P1,P2,P3; never supplied q answers',
        'minimum_force_increment_half_N':'min(diff(new four P))/16, inherited unchanged by every force segment'},
    tests={'methods':12,'real_paths_max':7,'finite_algebra_injection_rejection_calls_max':37,
        'method_ids':[a for a,_,_ in methods],'per_real_controller_seconds':60},
    comparison_gates={'q_abs_mm':1e-8,'all_DOF_four_split_fsum_abs_mm':1e-8,
        'R_abs_N':'max(1e-12,1e-7*abs(reference_R))','fresh':'binary identity and checks1'},
    resources={'tests_total_seconds':480,'tests_process_seconds':465,'tests_cleanup_seconds':15,
        'display_and_QA_seconds':60,'display_process_seconds':35,'display_cleanup_seconds':10,'QA_deadline_from_display_start_seconds':55,
        'other_shared_seconds':120,'helper_seconds':660,'outer_seconds':720,'sampled_RSS_GiB':8,'four_library_thread_cap':16},
    outputs={'PNG':1,'PNG_inspections_max':1,'GIF':0,'new_HP':0,'real_r9_paths':0},
    stop='First unexpected terminal error; no external retry, repair rerun, extension, force, deletion or automatic rollback',
    original_physics_and_gates_preserved=True, qualification_upgrade=False))

# This figure uses only ordinary, already-published scalar labels. No HF import.
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig = plt.figure(figsize=(14,8), facecolor='#f7f9fb')
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
navy, teal, orange = '#17324d','#006b71','#bc5c16'
ax.text(.045,.95,'Force-state continuation',fontsize=23,weight='bold',color=navy,va='top')
ax.text(.045,.895,'SPECIFICATION ONLY  |  No new finite-element result or load step',fontsize=12,color='#52677c')
ax.text(.045,.85,'Held input mean d = 1.06 mm  |  Same geometry, body membership, physics and original gates',color=navy)
ax.add_patch(FancyBboxPatch((.04,.755),.92,.058,boxstyle='round,pad=.006',facecolor='#e0f0f0',edgecolor='none'))
ax.text(.055,.785,'ROOT SCALE ANCHOR:  P0 = 2.3998009507e-4 N   (retained across every segment)',color=teal,va='center',weight='bold')

def box(x,title,lines,color):
    ax.add_patch(FancyBboxPatch((x,.425),.275,.275,boxstyle='round,pad=.01',facecolor='white',edgecolor=color,linewidth=1.5))
    ax.text(x+.014,.675,title,fontsize=14,weight='bold',color=color,va='top')
    for i,line in enumerate(lines):
        ax.text(x+.014,.625-i*.041,line,fontsize=11,color=navy,va='top')

box(.05,'Saved force parent',[
    'P1 = 2.5615728654e-4 N',
    'q1 = 0.025000000127 mm',
    'R1 = 0.195365420423 N',
    'Original lift1 and w1',
    'lift1[body-x] already = q1'],teal)
box(.365,'Fresh anchor at P1',[
    'Same split, absolute q1, P1, R1',
    'One new F/T base check',
    'Bitwise state identity',
    'No projection or repair',
    'No q-origin reset'],teal)
box(.68,'Append absolute P2 > P1',[
    'Solve unknown q2 and R2',
    'u2 = lift(q2) + w2',
    'Overwrite body-x lift with q2',
    'Keep original root P0 scale',
    'q2 is not a supplied target'],orange)
for start,end in ((.33,.355),(.645,.67)):
    ax.annotate('',xy=(end,.56),xytext=(start,.56),arrowprops={'arrowstyle':'->','color':navy,'lw':1.7})

ax.text(.05,.345,'ABSOLUTE DISPLACEMENT',color=teal,fontsize=12,weight='bold')
ax.text(.05,.30,'x_body = X_body + q_absolute',fontsize=13,color=navy)
ax.text(.05,.255,'Keep q1 in the saved lift; do not add q1 twice.',color=navy)
ax.text(.05,.215,'No reconstruction from rounded display coordinates.',color='#52677c')
ax.text(.53,.345,'UNCHANGED FORCE GATE',color=orange,fontsize=12,weight='bold')
ax.text(.53,.30,'SP = max(|P|, |root P0|, Ffloor)',fontsize=13,color=navy)
ax.text(.53,.255,'Segment start P1 is not the scale anchor P0.',color=navy)
ax.text(.53,.215,'Signed increasing P can remain negative.',color='#52677c')
ax.plot([.045,.955],[.16,.16],color='#c4d2dd',lw=1)
ax.text(.045,.12,'NEXT: finite 16-cell direct / saved-child / saved-grandchild validation, then installation if all PASS.',color=navy,fontsize=11)
ax.text(.045,.077,'Half-model P already includes thickness.  Full symmetric axial load = 2P; q is unchanged.',color='#52677c',fontsize=10)
fig.savefig(A/'continuation_schematic.png',dpi=160,facecolor=fig.get_facecolor())
fig.savefig(A/'continuation_schematic.svg',facecolor=fig.get_facecolor())
plt.close(fig)
svg = (A/'continuation_schematic.svg').read_text(encoding='utf-8')
(A/'continuation_schematic.svg').write_text('\n'.join(line.rstrip() for line in svg.splitlines())+'\n',encoding='utf-8')
print(json.dumps(dict(status='prepared', methods=12, real_paths_planned=7, real_paths_executed=0, conceptual_figures=1)))
