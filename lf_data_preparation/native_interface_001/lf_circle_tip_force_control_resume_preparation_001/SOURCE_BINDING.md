# 来源与本轮实际读取

2026-10-23；基线`7ebcbf747a85e9c8bbe547bcd6e4fe600f76c12c`。本页是准备记录，不是续载结果或科学缓存准入回执。完整原值见[SOURCE_BINDING.json](SOURCE_BINDING.json)。

|普通来源|原字节SHA256|
|---|---|
|当前force/result.json（5140126B）|`8caad93b7f765af9b70597b4c3992b8425af2a77c74b7e7eb68fafee8fda3355`|
|原fixed父result|`9e083bb057de9ea9b2b52694b3cc474a877ecbfcc3785d26fa50f55566e320ec`|
|原model描述|`7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b`|
|原geometry描述|`9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a`|

候选父为当前force的accepted1/original1成功末态：P1=0.0002561572865437846 N，绝对q=0.025000000126731543 mm，signed R=0.19536542042269825 N；state声明`352103915d1f03e02da4b49de5426ddb3daf9438f0e7d25ed37c9876aaa0984c`。state.npz声明SHA=`7e4c6d137e651801b5f8bbcb574f08fb633ff56d320611c69da6fcb136b88eb3`，lift/fluctuation均float64[29970]。本轮只stat，不读其内容、散列或解码，也不从positions反推split。

原预载P0=0.0002399800950672949 N；原Nmin=1.0110744672806061e-06 N、max_bisections4、minimum_increment=.00625 mm分别保留，N/mm不互换。原minJ=0.00041660852936145333、maxHu=0.31817338324076838仅来自已有普通标量，未新定位场极值。

本轮读取4份普通描述，绑定57份当前生产源码；对未来3个科学依赖只stat：原model.npz、geometry.npz和force accepted001/state.npz。已存在不代表payload已核。未来真实续载的最小科学读取预计仍为3路径：model整档身份、geometry四mask、force split两字段；不应为复用旧_admit而再解原fixed q0态。小模型未来自行生成的缓存另计，不借正式旧缓存。

完整物理：α2.5e−7、γ1e−6、r9/(80,40) mm、right92/Lr80 mm、E1 MPa/ν.3/plane strain/t20/h.5；14720单元/29970DOF、原510工件单元/565节点、端口/支撑/导向不变。父force producer的六源SHA全部原样保留；未来受授权改动的controller/API可不同，原力核与切线两源SHA必须继续匹配。不能为了新controller静默重写旧producer身份。

正式旧force完整结果与state位于[HIGH1原包](../lf_circle_tip_force_control_high_001/execution/execution_evidence.zip)，原fixed模型依赖见[HIGH1恢复说明](../lf_circle_tip_force_control_high_001/RECOVERY.md)。本轮未解包或复制科学档。D路径只是本机历史来源，换机恢复需新路径绑定与明确读取范围。
