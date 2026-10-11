"""Record ordinary-source findings only; never call the documentation tool."""
import ast
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
name = "close_resume_docs.py"
raw = (HERE/name).read_bytes()
ast.parse(raw,filename=name)
report = dict(status="findings_recorded_static_documentation_tool_review_final_review_deferred",
    reviewed_external_SHA256={name:sha256(raw).hexdigest()},tool_executed=False,
    numerical_terminal_inspected=False,final_static_pass_claimed=False,
    findings=[
        dict(id="D1",issue="NOT_PASS still unconditionally parses any existing helper/tests/result/response/view JSON.",
             effect="A malformed partial artifact may prevent recording the real failure instead of preserving the raw evidence.",
             recommendation="Use the actual completed terminal classification to adapt missing/invalid reads minimally after terminal; do not introduce a generalized defensive parser framework."),
        dict(id="D2",issue="The visualization branch is selected by if view truthiness, then states 3PNG/GIF and embeds all fixed filenames.",
             effect="A running/not_pass or partial view manifest can produce false completeness claims and nonexistent links; no pixel review is required in that branch for NOT_PASS.",
             recommendation="Report the actual view status and existing artifacts only; distinguish missing display or unavailable pixel inspection. Never fabricate a completed decrease state or a finished image set."),
        dict(id="D3",issue="Test/helper/progress links are unconditional and missing production counts default to0.",
             effect="Early failures may produce broken links and convert unknown/missing calls into apparently observed zero calls.",
             recommendation="Only link existing files; show missing/not_available for absent counters. Preserve started/completed values where actually recorded."),
        dict(id="D4",issue="The unfinished-feature paragraph says general input is unfinished without distinguishing implementation from validation.",
             effect="This can imply that existing Mean/API/batch or native input functionality is missing.",
             recommendation="Say qualification of arbitrary new LF geometries/tasks remains incomplete; existing interfaces and the tested physical task are implemented.")
    ],
    supported_source_contracts=[
        "Completed outer drives PASS/NOT_PASS; documentation closure PASS is separately labelled.",
        "Default hf_repo candidate remains uninstalled, while force/tangent and prepared-card history remain unchanged.",
        "Only two oldfronts are written; full BASE raw bytes are embedded once with SHA and exact history offsets.",
        "Typed trial/accepted states and original/child target identities are distinguished; original parent failure remains historical.",
        "Postterminal metadata actions0 are separated from actual test/production/view actions and no new physical qualification is granted."
    ],
    decision="Root accepted findings and will adapt to actual terminal records. No final peer PASS until revised actual bytes are supplied.",
    actual_actions=dict(document_tool_run=0,formal_repository_write=0,HF_import=0,NPZ_decode=0,
                        tests=0,force=0,tangent=0,solver=0,observer=0,HP=0,render=0))
(HERE/"DOC_TOOL_STATIC_REVIEW.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
md = """# M-RESUME1 封账工具普通源码静审（问题记录，尚未最终通过）

仅阅读 close_resume_docs.py 及 AST；未读取动态生产记录、执行封账、导入 HF、解码 NPZ 或运行科学／绘图。当前不声称最终静审通过，等待真实终态及最小适配后再审。

发现4点：NOT_PASS仍直接解析所有既存部分JSON，可能不能记录malformed失败产物；if view仅按字典存在便声明3PNG/GIF并插固定链接，可能把部分显示说为完整显示；测试／helper／进度链接无条件生成且未知计数默认0；“一般输入未完成”没有区分已有接口与任意新LF几何／任务的验证资格。

建议只根据实际终态做最小调整：真实存在的文件才链接，图件及pixel检查状态分别记录，未知计数保留missing/not_available，不造图／数值／下降态。不为这些准备问题新建通用防御框架。

其余源合同符合目标：已完成outer决定数值PASS/NOT_PASS；默认候选未安装；旧准备文件只读；两个front嵌入BASE完整原字节一次并记录精确区间；父失败／子段／accepted与trial区分，封账metadata actions0与实际机械调用分开；不升级HP、压力、有效夹持、稳定性或HF5。

Root已接受上述findings，待实际终态适配，不作当前final静审。精确源SHA与详细问题见 DOC_TOOL_STATIC_REVIEW.json。
"""
(HERE/"DOC_TOOL_STATIC_REVIEW.md").write_text(md,encoding="utf-8")
print(json.dumps(dict(status=report["status"],source_sha256=sha256(raw).hexdigest(),
    JSON_sha256=sha256((HERE/"DOC_TOOL_STATIC_REVIEW.json").read_bytes()).hexdigest(),
    MD_sha256=sha256((HERE/"DOC_TOOL_STATIC_REVIEW.md").read_bytes()).hexdigest()),indent=2))
