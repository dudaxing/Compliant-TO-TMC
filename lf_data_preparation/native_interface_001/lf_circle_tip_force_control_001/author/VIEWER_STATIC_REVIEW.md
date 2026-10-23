# L-CTIPFLOAD1 独立显示源码静审

2026-10-23。审阅者 `/root/fload_tests`，非renderer作者。结论：**16/16静态通过，无剩余静态阻断**。本次仅只读源码、普通字节身份和AST解析；没有import renderer／HF，没有dry render、NPZ解码、F/T或新科学路径，也未打开任何图像。实际可读性仍待唯一授权绘图后的root一次像素检查。

绑定renderer：`D:/hfl1_001/render_fload1.py`，7580字节，SHA256 `a817d4addb7a94c8d8a930593b9b10bb7d11ef407491514810693b5052aa11c4`。对应冻结protocol SHA `1e760e6854cc447f0354d34d95be0f8ed51d43054f938b6f4740d0606869e9f0`。输入字段交叉静核：测试候选 `23b9b1a84edbf48beb9c2641957a094b977cb6901058d9336e89c675c62191f5`、新native force API及原probe的实际输出。

|项|静态结论与依据|
|---|---|
|1 AST及调用边界|AST成功；只import标准库、Matplotlib和NumPy，不import HF／kernel／求解器，未执行renderer。|
|2 summary字段匹配|最终测试写顶层 `force_result_file`、`probe_result_file`、`cross_checks`、`all_eight_new_methods_passed`，renderer读取键一致。|
|3 唯一本次目录|summary固定于run_001/artifacts；另外两个输入resolve后必须在本次run内，禁止历史科学结果。|
|4 输入集合|仅三份不同的新普通JSON：summary、force result、displacement probe result；receipt只对同三文件再读字节核SHA。无NPZ／旧媒体读取。|
|5 缓存几何|force model坐标25×2、connectivity16×4、solid为ne长度一维；positions来自接受态普通记录；body单元按原body节点识别，不新构模或remask。|
|6 真实比例|多边形使用缓存实际positions，参考轮廓使用原坐标，equal aspect；标题明确actual geometry ×1。|
|7 箭头比例|只有位移箭头乘200，scale_units=xy、scale=1且标题明确；微小真实变形本来接近参考轮廓，不误称结构放大200倍。|
|8 控制对照|probe绘给定q下实测Q；force绘给定P下独立求出的q；参考只事后展示，未知q不会变为输入。|
|9 单位与交叉界|mm→μm乘1e3，mm→nm乘1e6，N→μN乘1e6；1e−8 mm界绘为0.01 nm，数值正确。|
|10 预载与分量|使用绝对P，未减掉非零P0；内部材料／Hu分量取负ON-body x，符号与Q相同。标题说明半模型、厚度2mm已包含，不再乘厚度或2。|
|11 机构R|R_input_N在独立右轴，轴名N明确，与P／Q的μN轴区分，不冒称工件驱动力。|
|12 残差与历史|自由残差和工件合力残差分别读取、各与1e−9比较；实际newton_history全部绘出，未筛去内部失败／二分base checks；标题已改actual force-path。|
|13 零值展示|仅非正展示值映至1e−18，严格正值保原；输入的实际残差按定义非负，故实际只有零值使用floor；不修改输入JSON及保存数值，标题明确zero显示规则。|
|14 J／Hu与其他门|绘保存的minimum_J和max_abs_Hu；注释显示实际接受态数、最大rigid/zero误差与global balance，未重算材料／曲率或新增科学门。|
|15 绘图库静核|PolyCollection的ne颜色、二维单元顶点、quiver shape、axes.set的ticks/labels、twinx、constrained layout、单次savefig API未见明显静态错误；图例和单位有明确文字。|
|16 输出／资格|新view目录必须不存在；只生成一张force_control.png及普通receipt，记录三输入／新图字节身份、比例与耗时；无旧媒体打开、重绘、动画或资格升级。|

首次启动前的两项显示修订均已落实：历史标题改为“All actual force-path base checks”；floor由max(value,floor)改为仅零值展示，以免悄悄抬高严格正的小残差。这是未运行前的文案／显示映射修订，不改变科学数据或增加绘图次数。

本结论不等于图像已生成或通过像素检查，不等于17项数值验证通过；完整17项与预算／清理门由独立top wrapper按卡先核，viewer的八新方法门不能替代原九项JUnit门。全清单通过后原窗口内才可调用此renderer一次。

## final_protocol_ack：最终包装绑定补充

本节保留原审阅protocol `1e760e...e9f0` 为历史，不改写原审阅事实。随后仅读取最终protocol及launch／outer／run包装源码，确认最终protocol为31415字节、SHA `3476f6d6136181c498ca80bfa422c7c334a160f5cda2ee530b2c714c5a37ece0`。renderer仍是上述 `a817d4...11c4` 7580字节，测试仍是 `23b9b1...91f5` 34807字节，均已重新核字节身份。

最终包装把两文件安装移到top launcher：tests／viewer清理、helper清理、root一次QA、outer本实例清理四层证明通过后，top才在原窗口内安装。run helper仍只有唯一17项测试通过后一次调用原renderer；renderer本身、三份普通JSON输入、schema字段、唯一PNG、×1／箭头×200、显示floor与原预算未改变。该安装时序调整不影响前述16项显示静审结论；本确认没有重新解释为完整进程包装审计通过，完整包装另有其独立记录。

本补充未导入或执行包装／renderer，没有绘图、数值、NPZ或像素检查。
