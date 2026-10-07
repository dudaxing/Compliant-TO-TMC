# 右侧介质余量2mm完整路径生产候选

此目录尚未导入或执行制卡／数值入口。`build_right_margin_production.py` 仅冻结 `lf_data_preparation/native_workpiece_001/right_margin_cycle_001`；先要求实际 `right_margin_preparation_001` PASS、120/150/8GiB终态与所有源输入／输出SHA仍匹配，再由root审阅制卡和执行范围。

新生产task、geometry snapshot、model fixture与direction全用实际prep输出原字节。原 `execute_shift_pose.py` 57d18b…、13行 `prepare_shift_pose.py` fbb3e1… 与64行launcher f3a966… raw复用；源码25个hf_eval模块（原24＋analysis_domain）和worker／shim合计27份小caps，重新冻结、独立basename。CLI不被误列为机械runtime，仍通过准备proof绑定。

实际模型旧／新raw delta须从已通过prepared `model_comparison.fields` 中 raw_equal=False生成，不借gamma-only的3field预期。共27字段，10scalar/operatorsraw相同、17raw变化；原物理子域相等来自准备的cell/node/DOF mapping proof，不是raw delta或旧机械资格。生产构造与prepared新fixture27fields必须raw相同。

物理任务仍固定side18中心(71,40)，rightface80；分析域右端82、右介质余量2mm，h1/E1/gamma1e-6/alpha1e-6/Lr80、原端口坐标和权重、全部其它物理值及24原targets保持。实际新counts8key取自prep，并核3280cells/3403nodes/6806DOFs/450fixed/6356free，不复制历史4-keycounts。重新生成的PORTdirection6806DOFs原字节复制至新run；任何旧lift/fluctuation/accepted states均不复制。

一次fresh-zero `0→1.2→0 mm`，显式port_projection、mechanical/chunk256，原Newton/Armijo/J/残差和二分门不变；只把原time_limit改4500秒，helper4500／outer4560秒、8GiB。额外accepted二分态由实际结果决定，参考将需全部实际N的全新2N次HP，不能预设N=24或借用任一旧HP。图／reference尚未执行，压力与接触判据也无新资格。

制卡前需独立静审文件；命令 `python <外部目录>/build_right_margin_production.py --repo <Git仓库根>`。制卡不调用HF或solver；本作者仅AST/compile及文件rawSHA读取／复制，没有运行制卡、准备、F/T/solver/HP、观察或绘图。
