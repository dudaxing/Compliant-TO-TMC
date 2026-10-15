"""Prepare the directly approved L-USE1 ordinary source packet, without running it."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import ast
import json

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_saved_consumer_001'
STAGE=ROOT/REL
BASE='c9ca9a23464bed01aff3ee7a6a0410a09c933d9e'
author=STAGE/'author'
author.mkdir(exist_ok=False)

def new(path,value):
    raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as f: f.write(raw)

manifest=json.loads((ROOT/'handoff/repository_manifest.json').read_bytes())
old={row['path']:row for row in manifest['files']}
inputs=[
 'lf_data_preparation/native_interface_001/lf_link_001/run_001/light_index.json',
 'lf_data_preparation/native_interface_001/lf_link_001/run_001/linked_response.json',
 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/result.json']
media=[
 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/comparison.png',
 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/distances_forces.png',
 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/peak_fields.png',
 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/actual_states.gif',
 'lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference/reference_observations.png']
sources=[REL+'/example/consume_saved_lf.py',REL+'/execute_consumption.py',REL+'/launch_consumer.py']
pins={}
for name in sources:
    raw=(ROOT/name).read_bytes(); ast.parse(raw,filename=name); pins[name]=sha256(raw).hexdigest()
cwd=Path('D:/hf-native-workpiece-api-author-20261015/LF_USE_execution_cwd_001')
cwd.mkdir(exist_ok=False)
protocol=dict(schema_version='L-USE1-saved-consumption-card-1.0',card='L-USE1',
 source_baseline_commit=BASE,source_commit_scope='Inherited baseline only; new approved example/helper/launcher bytes are bound individually, not claimed to be present in the baseline commit',
 helper_seconds=120,outer_seconds=180,sampled_RSS_bytes=1024**3,
 index_file=inputs[0],example_source=sources[0],output_directory=REL+'/run_001',working_directory=cwd.as_posix(),
 expected_rows=25,selected_indices=[13,16],source_bindings=pins,
 json_input_bindings={name:old[name]['sha256'] for name in inputs},
 inherited_media_bindings={name:{key:old[name][key] for key in ('sha256','bytes')} for name in media},
 bindings={**{name:old[name]['sha256'] for name in inputs+media},**pins},
 expected_calls=dict(consumptions_started=1,consumptions_completed=1,json_reads_started=3,json_reads_completed=3,table_writes=1,review_writes=1),
 new_HF_API_tests_F_T_HP_solver_plots_media_reads_pixels=0,full_path_reference_pass=False,formal_labels=False,ranking=False,
 stop_policy='One invocation, first terminal error stops, no retry/repair rerun/extension/force/rollback; preserve actual partial outputs')
new(STAGE/'protocol.json',protocol)
human=dict(card='L-USE1',authorization_from_direct_human_reply=True,direct_human_answer='批准按 L-USE1 执行',
 reply_context=dict(source='actual_user_message',scope='Direct approval of the pending L-USE1 authoring and once-only consumption stage',
  approved_inputs='Existing light index, linked response and ordinary result JSON; 25 rows and original five media links',
  helper_seconds=120,outer_seconds=180,sampled_RSS_bytes=1024**3,
  boundaries='No new HF summary/API, tests, solver/F/T/HP, plots, science/media bytes or pixels; original source/physics/gates/results remain unchanged'),
 observed_authorized_baseline=BASE,source_commit_association='Root verified current inherited baseline; human did not literally name a commit hash')
new(author/'direct_human_reply.json',human)
auth=dict(human,authorized=True,one_invocation=True,authorized_execution_source_commit=BASE,
 source_commit_scope=protocol['source_commit_scope'],protocol_sha256=sha256((STAGE/'protocol.json').read_bytes()).hexdigest(),
 human_evidence_sha256=sha256((author/'direct_human_reply.json').read_bytes()).hexdigest(),source_bindings=pins,
 created_utc=datetime.now(timezone.utc).isoformat())
new(author/'authorization.json',auth)
previous=Path('D:/hf-native-workpiece-api-author-20261015/LF_LINK_execution_closure_001')
for source,target in [('execution_publication_receipt.json','previous_publication_receipt.json'),
 ('root_execution_publication_terminal_confirmation.json','previous_root_publication_confirmation.json')]:
    new(author/target,(previous/source).read_bytes())
card='''# L-USE1：外部研究层消费已有25态保存结果

2026-10-15（Asia/Seoul）。用户已直接批准“批准按 L-USE1 执行”，不是从目标自动续作推断授权。继承main c9ca9a2；新示例及包装在本次批准后编写，以protocol中的逐文件SHA冻结，不声称这些新字节已在c9提交内。

整体目标仍为独立HF读取LF普通几何、在明确任务下给出TMC响应和可观察力学效果，供外部研究层使用。HF不优化、不调用dmftd，MPM未实现。最近L-LINK1已完成公共摘要关联，但只展开峰值和回零，不能直接提供完整25态或卸载1.05 mm的数值快照。

本步编写一个纯标准库示例，通过显式repo/index/output从无关cwd消费已有包。一次运行相同CLI main/参数解析及consume函数，读取light_index、linked_response和原result三个普通JSON各一次；不再次调用HF摘要。以行序enumerate作为接受编号，另保原目标编号；原反力字段为R_input。输出25态states_table.json、Markdown检查页REVIEW.md及已有五媒体链接。JSON保留原浮点、state SHA、加载/卸载、R、q_in/q_out、minJ和工件材料/Hu/总合力向量；Markdown显示舍入并链接原图。

参考覆盖保持matched_partial、indices13/16、2/25、已有4HP；其余行显示未覆盖，不显示为数值失败。全路径参考及原所有资格字段保持。R为半模型反力，工件力为下半固定体弱式合力，不能称压力或已认证有效夹持力；q_out不是表面间隙，minJ沿原全局保存含义。无新正式标签或排名，不新增跨几何可比性。

唯一执行顺序：源静审/身份与实际授权核对→一次外部cwd helper→同原JSON字段投影、25态/两匹配行/五链接核对→两普通输出封存/真实回执→按实际结果记录和交付。示例无hf_eval/NumPy/JAX等依赖；独立包装只管理时间、采样RSS和记录，生产源码不安装或修改。零新科学由固定源码/实际计数支撑，不声称动态机械hook监控。

额度为helper120秒／outer180秒、采样1GiB，时钟从各程序入口开始，含输入读取、CLI main、写入、封存及回执；采用合作检查/采样，非OS硬限额。outer等待同一child真实终止。首个终端错误停止，无重试、修复重跑、延期、force、回滚或删除，保实际部分输出。三原JSON的完整SHA链在唯一消费中核对；旧科学数组/科学gzip/CSV、五媒体字节/像素在准备、执行和收尾均不读取。媒体只保身份/路径，交付可用继承封存＋stat。

验收要求实际一次helper/CLI main/consume；三JSON读取完成各一次、表和检查页各一次，25行对应全部原接受态、每个原浮点和state SHA保持，匹配参考恰为13/16，五链接按显式仓库根解析，输入与原结果保持。source AST不是执行/测试通过；没有新单测或重复L-LINK1的16项测试。独审核实际普通输出/封存、物理语义和范围；推送/恢复以实际回执核定。

下一步仅根据真实消费需求推进：必要时补其余保存态独参；跨几何比较先明确共同任务、分析域/网格及逐例参考范围。当前不安排新的物理路径，也不因本示例升级完整25态参考、全切线列、压力/有效夹持/释放/稳定性或HF5整体。
'''
new(STAGE/'L-USE1_CARD.md',card.encode('utf-8'))
new(author/'prepare_packet.py',Path(__file__).read_bytes())
new(author/'source_preparation_receipt.json',dict(card='L-USE1',status='authorized_source_prepared_not_executed',
 baseline_commit=BASE,protocol_sha256=auth['protocol_sha256'],source_bindings=pins,
 prepared=True,authorized=True,executed=False,installed=False,AST_parsed_only=True,
 previous_publication_receipt_SHA256=sha256((author/'previous_publication_receipt.json').read_bytes()).hexdigest(),
 no_scientific_or_media_byte_reads=True,created_utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(status='authorized_source_packet_prepared_not_executed',protocol_sha256=auth['protocol_sha256'],source_bindings=pins)))
