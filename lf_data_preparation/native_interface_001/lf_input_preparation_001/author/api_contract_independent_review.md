# L-PREP1 API／任务绑定独立源码审

状态：PASS_STATIC；尚未授权、执行或安装。审阅者未编写 API、CLI、root prepare／卡／说明／front；审阅者编写的 launcher／publisher 不在这份独立结论内，另由交叉审查者检查。

新 API 复用原转换器、右被动空域派生器与严格 task1.0／1.1 校验。原 `_validate_task` 深复制完整模板，geometry 严格恰有 geometry_id／descriptor_sha256 两键；新代码仅替换这两键，并逐项比较其余顶层字段。材料、工件、端口、背景、路径、task_id 与历史说明保持。返回三个绝对入口路径，manifest 的产物和 LF 快照是 case 相对路径；几何 canonical descriptor SHA 与原文件 raw SHA 分别记录，未混用。 异机需迁移整个 case；LF 快照在 native_geometry/sources。原扩域器深复制的旧 lf_v2 provenance 相对位置属于原来源上下文，没有重写到 derived_geometry；本输入 manifest 指向真实 native 快照。geometry 自身 descriptor／array 可读与完整 LF 追溯是不同的恢复范围。

坏 descriptor pin、family、不合法任务、数值宽度和已有输出在 converter 前拒绝；列对齐使用原转换器已经验证的 dx，再以 Fraction 十进制比例拒绝非整数列，保留真实转换 partial。业务失败不删除或重试；failed manifest 的 OSError 不掩盖原异常。公开宽度原接受非 JSON Real 的问题已在源准备期最小修正为 None／有限 int／float、bool 独拒绝（新 API SHA d37ab7ea…），未执行任何测试；不新增 serializer 或测试实例。

普通读取证实三来源／模板 family 相符：两份 native1.0 模板不含工件；fine 来源网格160×80、h0.5，原 native1.1 模板声明方形固定工件、alpha5e-7和原二十五目标。以上仅是输入语法与接线，不做构模、网格／工件兼容性或机械资格核验。原 converter 的边界、网格与四掩码规则未改；显式 padding 保存原子域，整个派生域不冒称 LF 原域。

卡的未来范围是3真实准备＋9预期拒绝、两新文件安装、1未变形图、helper180／outer240秒／采样8GiB。读取合同为8种参与解码的 NPZ 路径、11次 loader／44静态字段出现；另3份 LF 快照仅原字节复制，不能和 decoder 数混为同量。字段不是动态逐字段监控。CLI 验证是已安装 __main__／argv／stdout／退出行为的 runpy 同解释器调用，不声称新解释器启动。图只显示几何与声明，箭头不是力、位移或压力，工件未应用。

新增模块本身不破坏旧参考匹配：native_response 仅遍历已声明 source_bindings。新准备 manifest 没有继承 HP、完整路径、压力、夹持或 HF5 资格；原历史真实变更来源保持其原证据。PREP 的 evaluate_native 示例明确属于后续另定物理任务／资源，不在本卡运行。

root prepare 源只将 ordinary 文件和三份既有 LF NPZ manifest／stat 身份绑定，默认新目标当前须不存在，授权与运行对象不会预先创建；两个 front 旧 raw 连续保留一次。该 writer 在本审阅时尚未运行，正式协议、归档链接及发布恢复将在写入后另核。本报告无候选／HF imports、测试、数组／媒体读取、绘图或正式写入。

阻断：无。效果证据目前为源与 AST，未声称三例或十二实例已经通过。
