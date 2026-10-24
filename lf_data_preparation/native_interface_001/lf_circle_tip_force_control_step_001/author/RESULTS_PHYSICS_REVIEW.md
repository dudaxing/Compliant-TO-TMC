# L-CTIPFSTEP1 实际结果／物理功能独立复核

**12项PASS；正式非零q保存态续载已完成，科学窗口关闭。** 本审仅读新普通JSON和58份生产.py原字节，无HF导入、科学NPZ/ZIP/媒体读取、F/T/HP/平衡、测试、绘图或再次像素检查。

- **R01 One closed successful continuation — PASS**：Actualsuccess/targetP2,scientificwindowclosed,1API/solver,2original accepts/global1,2;oldP0 only ancestry,not replay.
- **R02 Nonzero fresh identity — PASS**：Freshcheck1 withq/P/R binary64,statehash andtwo declaredfieldSHA identical tosourceHIGH1;no rebase/anchor correction. This audit compares ordinarypins,not split bytes.
- **R03 Root scale and inherited settings — PASS**：OriginalrootP0,segmentP1,full3/segment2/globaloffset1 andnonclocksettings/Nmin preserved. PositivepathSP=P;not independent numerical proof ofroot-vs-segment implementation.
- **R04 Original accepted-state gates — PASS**：Both accepted states pass separatefree/body/mean/J/global/rigid gates;no newHu/Jthreshold. AcceptedminJ4.061818153e-4 isdistinct fromslightlysmaller recordedtrialminJ4.061817586e-4;intermediatetrialmerit acceptance isnot a productionaccepted state.
- **R05 Actual physical response — PASS**：NewP2 independently givesq=.03123384806234602mm/R=.1954005432102683N;deltaq=.0062338479356144755mm/deltaR3.512278757e-5N. No q answer prescribed or newreference error invented.
- **R06 Force/ledger semantics — PASS**：ON-body Fx=-Q,storedg=Q-P exactly;material+Hu components sum tosavedtotal;explicitPonce/bodyxdriveabsent/bodyyoverlaponce. Rseparate. Tinygroupregroupingdifferencesdescriptive,not newclosuregate.
- **R07 J/Hu/tip and right medium — PASS**：AcceptedminJ falls2.50276%,maxHu rises.570303%,axialHu fraction72.58059%→72.71390%;unsignedrasterdistance .00866824→.00877730mm,not a contactgap/pressure test;right480 originalmediumphase retained.
- **R08 True mechanics and internal-attempt counts — PASS**：6F/6complete,4T/4complete,4basechecks,2fullfactor acceptedmerittrials,no newfailure/bisection. HP/saveF/T0;oldprobeinvalidJ/internal.0125/historycounts separate.
- **R09 Scientific-read accounting — PASS**：Workeractual5oldreadcapableopens/3uniquepaths,4newwriteevents/no newreadcapableevent;sourceflow2decodedarchives6fields,not dynamicfieldhook. Ordinarycheck2JSON/viewer4JSON,0fielddecode.
- **R10 Five image receipts and true animation — PASS**：ExistingrootQA5singlePNGchecks/rerender0,renderer2actualframes andrecordedvisibilitylimits retained;pendingrendererlabel ishistorical. Audit doesnot open/rehash media.
- **R11 Original windows, cleanup and seal — PASS**：Science362.422s,outer430.849s;sharedQA66.2818<585/600. Fourrealnormal0completeinstancecleanups/Active0/handlesclosed;sealonce55members14380965B fromordinaryreceipt/manifest only,archive neveropened.
- **R12 Production and qualification scope — PASS**：58productionpy rawidentities stillfrozen,HP/tests/productionchanges/retry0;independentHP/effectivegrasp/release/HF flagsfalse. Numericalcontinuation PASSnot capacity/stability/pressure/purecontactqualification.

## 实际效果与边界

P1→P2从0.0002561572865437846增至0.000260201584412907半模型N；实际q从0.025000000126731543增至0.03123384806234602mm，R从0.19536542042269825增至0.1954005432102683N。新增量是给P、独立求q/R，原mean1.06mm及绝对split继承；fresh检查1、q/P/R bits和state/field pins保持。新段2接受态，4base/2全步trial、6F/4T均完成、0失败/二分；旧q探针invalid_J和.0125内部态保历史，不改写。

两接受态最差ρF=1.2233918339341764e-12、ρP=5.656400795828763e-13、mean/rigid误差0、global=1.7018691195477797e-14，原门保持。新g=1.4718044491490723e-16N、原界2.60201584412907e-13N。SP实际等于P，rootP0仍保，但这条正增路径不能独证根尺度重置。

末态ON-body total=[-0.0002602015844130542,0.012537665631271991]N；material=[-7.099887164487156e-5,0.00950888135479409]N；Hu=[-0.00018920271276818263,0.003028784276477901]N。轴向Hu比例由72.58059%升至72.71390%；这不是压力比例或误差分配。显式P/guide/输入R/其余zero账本结构和原global门保持；普通分组再求和与原节点汇总有约1e-17N舍入差，机器记录仅描述，不新增重组门或改保存值。

accepted minJ从0.00041660852936145333降至0.000406181815315325（约-2.50276%），max|Hu|从.3181733832407684升至.31998793705692913/mm（约+.570303%）；trial记录的更小J=.0004061817585887269单列，不能混为新接受态。tip11260到原物理raster边的无符号距离从.00866824342929462到.008777299023513763mm，未代表解析圆接触判定；右480格原介质身份保持。

实际科学worker362.421993秒，监督362.818736秒；outer含封存430.848600秒、helper封存430.587526秒，均在原窗。root五图各一次检查于shared+66.281796秒完成，helper shared总66.395879秒；四层normal0/完整同实例清理/Active0/句柄释放通过。top采样峰873754624B约833.28MiB，只是采样值。一次seal55成员/14380965B/SHA2a3b8cbac13d578a1dd526c680a4db788cd1200a1ebfbdc7f6467d8a6d120881来自原普通回执/manifest，本审没有再次开归档。

旧NPZ5个read-capable事件/3路径，新输出4个write事件且本worker无新NPZ read-capable事件；2解码档/6字段是完成准入源码控制流口径，不是动态字段hook。checker两JSON、viewer四JSON；既有五图QA/两帧writer记录及可见性限制原样保留，本审未开图像/GIF。

## 建议下一步

先准备并核定新P2 accepted1/global2的独立保存态参考，而非立即再加P。理由是续载功能已有正式证据，但此新态尚无给q/HP参考，J已很小且继续降低，轴向Hu贡献约72.71%；良好收敛不能替代独立数值核对。可以考虑HP80/120各一次、仅核该态，不重复平衡；先确认force1.1、绝对q/P/R、导向和KKT/原严格参考门的接口对应，再单独核资源及授权，不能照搬fixed-q0脚本或预授新资格。参考若通过，仍不证明纯接触/压力/容量/稳定性，之后再据实际J/Hu/距离/收敛决定下一个小P增量。
