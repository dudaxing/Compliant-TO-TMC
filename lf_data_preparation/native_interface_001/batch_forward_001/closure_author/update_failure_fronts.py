"""Publish-readable fronts from the closed production/reference records."""
from pathlib import Path
import json
from hashlib import sha256
from datetime import datetime, timezone

root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
stage=root/'lf_data_preparation/native_interface_001/batch_forward_001'
diagnosis=json.loads((stage/'reference_failure_diagnosis.json').read_bytes())
assert diagnosis['status']=='closed_not_pass' and diagnosis['production_unchanged'] and diagnosis['actual_new_HP_calls']==0
readme='''## 当前：两例真实批量生产通过，独立参考包装已停止

两例无工件任务均完成 0→0.025 mm 的四个原目标态；输入反力分别为 0.00521459203 N 和 0.00375627879 N，生产残差、约束、固定边界及力平衡检查通过。新独立参考因包装误用 `coords` 而在读取模型时停止，实际模型字段为 `coordinates`；新 HP=0，细例参考及新批量图未执行。失败卡保留且不重试。当前正在准备最小 V2 包装和单独新卡，原力学源与生产证据不变。

整体目标仍是复用 LF/N4 几何与研究层，完成独立非线性 TMC 正向评价；HF 不包含优化器。固定工件加载/卸载已有真实结果与图，通用接触/连续压力、匹配网格及 HF5 整体仍未完成。两例为不同设计，不能由此作网格收敛或排名。[当前状态](docs/CURRENT_STATUS.md)；[新生产及失败记录](lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md)；[物理功能矩阵](docs/PHYSICAL_FUNCTION_PROGRESS.md)。main 开发，origin 保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

以下保留历史记录；“真实两例尚未执行”等旧文字仅描述当时状态。

---

'''
resume='''## 当前恢复入口：生产通过，参考读取失败卡已关闭

先读 [CURRENT_STATUS](CURRENT_STATUS.md)、[当前结果](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md) 与该目录 `current_progress_002.json`、`reference_failure_diagnosis.json`。原两例生产卡 PASS，各四态/14F/9T，54份保存输出和28核心源字节保持。canonical 新参考一次 NOT_PASS：`coords` 字段不存在，HP=0；细例参考/图未执行。不得复跑原生产卡、失败参考卡或修改冻结 source/protocol/output。

下一步是最小 V2 参考包装的全部字段、状态和属性审阅，随后单独新卡；原参考数学、门和资源预算保持。V2 数值执行尚未授权或启动。新参考两例均通过后才能生成自有批量图与 qualified_response；旧单例图/HP不能替代新结果资格。开发只用 main，origin=https://github.com/dudaxing/Compliant-TO-TMC.git；任意克隆目录以实际 Git 根为准，不依赖这台机器的绝对工作路径。

以下为历史记录，当前以上方及真实终态记录为准。

---

'''
changes={}
for path,prefix in [(root/'README.md',readme),(root/'docs/RESUME_DEVELOPMENT.md',resume)]:
    old=path.read_bytes();before=sha256(old).hexdigest()
    path.write_bytes(prefix.encode('utf-8')+old)
    changes[path.relative_to(root).as_posix()]=dict(before=before,after=sha256(path.read_bytes()).hexdigest())
(stage/'failure_front_documentation_install.json').write_text(json.dumps(dict(status='recorded',files=changes,
    created_utc=datetime.now(timezone.utc).isoformat(),science_calls=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(stage/'closure_author/update_failure_fronts.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':'fronts_updated','science_calls':0}))
