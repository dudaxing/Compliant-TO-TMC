# M-EXTEND2：短运行目录下的显式末态延伸

状态：仅准备，未授权、运行或安装。源基线main d7078c2，M-EXTEND1实际NOT_PASS已经闭卡并发布/恢复。新卡不重启旧launcher，也不使用旧余时。

## 目标与保留合同

修正Windows深层测试胶囊路径的包装遗漏。失败目标262字符、parent存在、LongPathsEnabled=0，证据强支持普通MAX_PATH限制；没有新的IO重现。[原实际记录](../saved_extension_001/RESULTS.md)及[微软说明](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)供核对。

七份功能候选和36个精确测试选择复用原字节，不复制或修改核心源。默认严格同任务续算保持；显式extend_path=True/--extend-path要求独立新task，只在旧15完整前缀后追加1.10 mm，其余所有字段（含task_id/description）保持。新task canonical94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6，旧a343fbb…，原float.hex规则保持。复用原task文件，不改旧结果/response/reference/view或M-EXTEND1。

选择成功child local1/global14/1.15 mm（state999b581e…），原lift/fluctuation/signed R运输原样；absolute initial_parameter1.15、K=None，fresh F/T复核。请求[1.15,1.10]，global14/15和child0/1；实际N>=2含原二分，无N≤9限制。立即parent success、failed/time_limit祖先分别保留；完整旧/新路径、压力、有效夹持/稳定性/全部切线列/HF5资格不升级。

原模型13440单元/27378DOF，h=.5mm、固定方形中心(71,40)mm/边18mm、E1MPa/nu.3、plane strain/厚20mm、gamma1e−6/alpha5e−7/Lr80mm、端口/边界保持。mechanical/chunk256/port_projection、原settings（新clock除外）保持。原生产residual≤1e−9、均值约束原bound规则（参数1e−10）、global balance≤1e−6、fixed split sum≤8e−11mm、接受态J>0，原分母/floor/回溯/二分及force/tangent/controller算术保持。

## 一次顺序及唯一包装差异

1. 核新直接批准/发布恢复proof/133原卡所需来源的本卡冻结闭包和六old SHA。创建短、独占runtime **D:/hf-extend2-runtime-20261012**（已存在即拒绝，本轮未创建），capsule=runtime/repo，pytest临时目录/cache也在runtime。90原字节复制布局保留：52HF模块、2CLI、13测试源、pyproject、16普通JSON、5既存媒体及旧plugin。实际来源清单用capsule相对身份＋明确机器绝对origin，不能fallback默认HF。
2. 一次36精确测试（原25+新11），真实tiny上界16单元/50DOF；实际collection/108三阶段报告/JUnit/stdout留存。五份旧媒体仅原字节复制和hash，不解码像素/绘图；不复制旧NPZ/HP科学gzip，tiny用例可生成并读取自己的微型数组。当前没有预collect或测试。
3. 一次公开API从原接受末态延伸1.15→1.10，model/reader/solve/save/summary/API各一次、两defaults aliases各一次；F/T开始/完成与原实际result对账，可恢复invalid-J trial不强迫两者相等。真实repo_root、原输入与新cache仍正式仓库。源NPZ仅2份/6字段：geometry四authority masks、选中state lift/fluctuation；不解码旧forces/tangents/matrix或HPgzip。计数是冻结loader闭包，非动态全hook监测。
4. 真实success及原门/身份/保存均PASS后，原pureviewer一次读取本次新cache，formal hf_repo四纯模块与胶囊同字节且不交六安装源；生成3PNG/N帧实际GIF及原派生表/摘要。只读1+2N新NPZ/27+18N字段，无新F/T/HP/model/solve。segment PEAK1.15并非原峰1.20，1.10不是释放完成；mechanical_hooks_monitored=false，新reference not_provided。
5. 同一窗口内一次ZIP_STORED原字节封存短runtime源码/fixture/tiny临时产物/cache到本run/runtime_capsule.zip；不np.load、不解码像素/科学，也不再运行测试。核成员集合、size/SHA、capsule90源及实际origin，写runtime_archive_manifest；归档在安装前PASS。zip内部成员为runtime相对路径，异地解包须选择短新目录，原绝对路径仅历史位置。
6. 以上全部PASS且资源/stop/pins有效才安装同六生产文件：native_resume/native_mean/native_evaluate/native_response及两个CLI，old→已测试new→实际installed SHA逐项核。新test只在原candidate/胶囊。安装后不重做科学/pytest，无自动回滚；partial安装如实NOT_PASS。默认当前未安装。

## 资源与首错清理

| 范围 | 一次cap |
| --- | ---: |
| 精确测试child | 180秒 |
| controller | 1800秒 |
| pureviewer child | 600秒 |
| whole helper/实际child wall | 3000秒 |
| whole outer | 3060秒（51分钟） |
| sampled tree RSS | 8GiB |

最早clock包括import/批准检查/复制/科学/显示/ZIP成员复核/安装/最终hash及回执；子test/view min(cap,whole剩余)，不叠加、退款或续期。RSS采样/协作停止，非OS实时硬限。原实际child退出等待、terminal stop及迟到PASS拒绝保持。

一次启动，首错停止后续测试/科学/view/install。typed solver失败由唯一API保存实际partial后停；unexpected异常只保真实已有progress/cache。只在原whole/RSS/stop仍开放时，允许一次既存runtime的partial原字节证据封存作为清理；窗口已闭则跳过，保外部partial。归档失败保partialZIP/原error，不重试、不删除runtime；成功归档后若安装失败不归档第二次。所有失败仍NOT_PASS，无修复重跑/延期/force/环境更换/自动回滚/新HP。

新布局已做静态字符串/AST路径审阅：90复制目标已知最长136，tiny tmp已知例118，正式输出已知206；不是实际IO/pytest通过证明，也不加科学门。系统注册表、整个正式ROOT和原partial均保持。

## 功能与后续

原最后有效进度仍为1.20→1.15两态、4HP与M-ALINK1关联；M-EXTEND1测试/力学/图/安装0，新显式入口未验证。本卡成功才取得有限兼容与新段功能/实际图/六源安装；full_original/full_extended仍false，原M-ALPHA1 NOT_PASS保留，不将段顶点当原目标峰值。完整卸载、连续压力/有效夹持、移动摩擦/多形状、一般LF/稳定性及HF5仍未完成。下一步按实际新响应滚动安排，不授权继续新目标。
