# L-CTIPLOCAL2：补齐介质定位图排版

用户已明确批准本卡实施及执行。整体目标是独立可恢复的TMC大变形分析；LOCAL1已完成1.03/1.04 mm两态的数值定位与尖端近景，但介质图顶部标题重叠。本卡仅修复该显示缺口，保留原LOCAL1执行PASS/视觉NOT_PASS历史。

保持r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm和其它物理、设置及原门。复用同两态，原J/Hu、Q1坐标、全部9861非工件介质、见证并列语义、地图范围与色标不变。新候选仅修medium图rect高度为.85（bottom .075，top .925）和suptitle y=.985；新图实际效果仍需一次像素检查。

唯一启动，helper180秒/outer240秒，采样8GiB、四库线程上限16。5NPZ/12字段限于model coordinates/connectivity/solid/workpiece_cells；两态各lift/fluctuation/J/Hu，各原NPZ在窗口内一次hash与选定字段解码。读取原LOCAL1普通定位/producer回执，精确核对位置、值、共同视野与色标；差异保留并停止，不改门或裁剪数据。

只生成1张新medium_locations.png、render.json与manual.html。已通过tip图仅链接，不重开或重绘旧媒体，不生成第二张PNG或GIF。首个终端错误停止，无重试、修复重跑、延期、force、回滚或删除；无新测试、构模、F/T/HP/Newton/平衡求解、默认HF改动或安装。含记录、main普通推送和同机异目录local Git恢复核对。

通过新图才补足视觉缺口，不改写旧失败。根据真实结果另行决定是否准备1.04→1.05 mm；不自动加载，不升级压力、有效夹持、完整路径、释放、稳定性、网格/域宽或HF5资格。
