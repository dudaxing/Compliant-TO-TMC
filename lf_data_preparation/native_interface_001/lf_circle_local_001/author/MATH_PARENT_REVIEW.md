L-CLOCAL1 数学与父态有限静审

结论：pass_parent_math_scope_review，无实质阻断；原授权定位意图应按以下真实布局表述，不是执行资格。

选S4 accepted1/global7/1.35、SHA0c8c5b07…a12455。3NPZ只解码8字段：model coordinates/connectivity/solid/workpiece_cells，state lift/fluctuation，forces J/Hu；原完整archive SHA＋stat已核，未读载荷。

J(ne,9)采用9点Simpson，非Gauss。原tmc_kernel.operators点序xi慢eta快：(-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(0,1),(1,-1),(1,0),(1,1)。节点BL/BR/TR/TL，N=[(1-xi)(1-eta),(1+xi)(1-eta),(1+xi)(1+eta),(1-xi)(1+eta)]/4。reference点=sumNX，actual点=sumN(X+lift+w)，真实mm/scale1；不新算J/Hu/F。

Hu(ne,2,2,2)无qp轴，是每单元常值位移Hessian；maxabs分量需保有符号值和exactties。单元中心marker仅代表位置，不称最大Hu GP；若广播9行须明确重复。free-medium严格同S1：~solid并排除workpiece_cells，不能改成全DOFfree单元。

最近witness在geometry.boundary.groups.all_exposed.closest_pair（原机制点73.0061191935,30.9038621851及工件点73,31）；tip witness在derived.tip_surface_witness。保持原保存点/edgeIDs，不新搜索；最近unsigned.096332和tip3.007572不同，containment仍未测。

仅源码/普通JSON与sealstat；原物理和门不改，不授连续极值、HP、稳定、接触或压力资格。完整字段SHA/范围见JSON；已将精确点序与键直接发作者。
