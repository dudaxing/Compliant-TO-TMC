# 新工件的局部保存结果观察

复用原纯缓存工具，未执行渲染，未调用观察API或力学入口。`saved_fit_comparison.py`保持SHA256 `a95be2a7953a3a52cf15d76dd319f995b262f22007df3c394f0a59a0f96592bf`；`build_saved_fit_card.py`保持SHA256 `57c49638854bd6d46122c2b6772f8f47ccfa69069fd200e0a944b707877b6974`。一次120秒、外层150秒、8 GiB，未来只有完整生产和新鲜同路径参考通过、主保存查看器实际通过后才能冻结。

它读取已通过主查看器的实际边、节点弱形式力与保存F缓存。原始结构观察窗口为 `y=30, x∈[63,80] mm`；本次边长18工件底边为 `[62,80] mm`，因此画面是局部尖端片段，不是全底边。局部Green应变不能混作全结构最大应变。工件总/材料/Hu弱形式节点力用于说明力学作用，不作为点接触压力。

拟阶段为 `functional_views/workpiece_enlarge_20261007/fit_001`，未来具体case/view都须指向主查看器实际输出，例如：

```powershell
python <external_author>/saved_view_candidate/cached_fit_candidate/build_saved_fit_card.py --repo hf_repo --stage functional_views/workpiece_enlarge_20261007/fit_001 --case pose002=lf_data_preparation/native_workpiece_001/shift_square_pose_002/run_001/result --view pose002=functional_views/workpiece_enlarge_20261007/complete_001/view/pose002 --case enlarged001=lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result --view enlarged001=functional_views/workpiece_enlarge_20261007/complete_001/view/enlarged001
python functional_views/workpiece_enlarge_20261007/fit_001/launch_view.py view
```

以上为未来模板，未执行；没有推测的新N或新状态字段。完整生产失败时应保留真实失败结果，不能交给该完整比较入口宣称夹持成功。
