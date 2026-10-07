# V1 加载失败诊断与 V2 源建议

新增 wrapper 读取 `model["coords"]`，真实 coarse/fine 的 23 数组字段均使用 `coordinates`；当前 `native_project.write_native_project` 也是此名字。原 Audit 数学不读取 coords，错误发生在新增节点数检查，尚未进入 HP。旧 reference 已关闭 NOT_PASS：checks11、接受态0、HP0。此前静审未把新增数组下标逐项对照实际模型声明，是作者覆盖遗漏。

已仅用两份实际 model/result JSON 与全部8态 descriptor JSON，核对模型字段、原 run_state 的两 state /17 force /3 tangent /CSC 字段名称和维度声明、标量下标与每个继承属性来源；除 coords 外未发现第二个缺失字段。该结论是保存声明与源接口兼容性，不替代未来原数值与 HP 门。

V2 只修正 `coordinates`，另设 `batch_reference_v2_001`、独立 author/output/contract/protocol/phase/schema2.0；`PRODUCTION_STAGE` 保持旧完整生产来源，新卡根目录使用同 raw F3 的 ROOT 深度与独立 stop。绑定旧失败卡仅作关闭上下文，不承接资格、补算或修改旧输出。数学和门直接继承原 Audit；各实际 N4 仍需全新8HP。先源审，再由 root 决定新卡，当前没有执行授权，未制卡、导入或运行。
