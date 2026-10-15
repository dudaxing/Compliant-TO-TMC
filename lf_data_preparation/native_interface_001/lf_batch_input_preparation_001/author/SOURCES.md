# L-BPREP1：两个仓库内普通 LF 包及准备成本依据

2026-10-16（Asia/Seoul）。本记录只核普通 JSON／原回执和文件 stat，没有新输入准备、HF 导入、科学／ZIP／媒体读取或仓库修改。后续应完全用仓库相对路径，不依赖 Downloads ZIP。

## 可直接使用的两个普通 LF 包

### fine：gripper__refine__kin_1e+00__kout_1e+00__random

LF geometry_id：`ed54b3c0507fd4e87ac327040c7b5eb313d872c7fa99b3418243947b424f8756`；schema `dmftd.hf_export.v2`。descriptor 的 arrays.file 为同目录 `design.npz`。

| 文件 | 原 SHA256 | 原大小 B |
| --- | --- | ---: |
| `lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.json` | `05aa71c6d3a77d4a221fe16453f06e7e19b45325a4aff824a951c95d4fd1a443` | 10471 |
| `lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.npz` | `8ce4f2114f96b2ffd596f889ccdfa9e7eb2a8a2c87ce6000ac4a35f9c9f6fbf6` | 1507 |

同字节、直接受原 producer seal 覆盖的备选副本：

- `lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine/native_geometry/sources/design.json`
- `lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine/native_geometry/sources/design.npz`

JSON 原字节 SHA 已核；NPZ 仅继承原封存 SHA／大小并核当前 stat，未读取 payload、header 或重新 hash。完整证据链、准备产物身份见 [SOURCES.json](SOURCES.json)。

### wave：gripper__refine__kin_1e+00__kout_1e+00__wave

LF geometry_id：`a8d12d0fbe070ac74e52193311f1acb6738367c5d7fb9af726bdc99b380667b9`；schema `dmftd.hf_export.v2`。descriptor 的 arrays.file 为同目录 `design.npz`。

| 文件 | 原 SHA256 | 原大小 B |
| --- | --- | ---: |
| `lf_data_preparation/native_interface_001/lf_third_input_001/run_001/sources/design.json` | `8d6629a966dab7411709c53c8c798cf6ee77c1a07446174aac9bca52162864f8` | 10458 |
| `lf_data_preparation/native_interface_001/lf_third_input_001/run_001/sources/design.npz` | `972339221c71f30b37c9847277d484f5655217a0968a64bdb2a691de7301c736` | 1483 |

同字节、直接受原 producer seal 覆盖的备选副本：

- `lf_data_preparation/native_interface_001/lf_third_input_001/run_001/case/native_geometry/sources/design.json`
- `lf_data_preparation/native_interface_001/lf_third_input_001/run_001/case/native_geometry/sources/design.npz`

JSON 原字节 SHA 已核；NPZ 仅继承原封存 SHA／大小并核当前 stat，未读取 payload、header 或重新 hash。完整证据链、准备产物身份见 [SOURCES.json](SOURCES.json)。

## 共同任务与既有准备身份

共同模板：`lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine/task.json`，2355 B，raw SHA `49f04cc5184cefc9a33fc92faeb529e9d53bf7da7f7c3e57f5872cd27f0eb8b1`，semantic task SHA `95ab4d283991a13315caeedab12afb3a84f052cd53d995cab7185433a3fc20d4`。wave 原准备协议确实绑定了这个模板，两个既有绑定 task 除 geometry 身份外完全相同。fine 原L-PREP1使用saved_extension_004/proposed_task.json，后来生成的fine task可作为两例共同模板；不能把这两份原文件raw SHA混用。

原生 h0.5 mm／80×40 mm，shape_yx=[80,160]；明确右补4 mm／8列，分析域84×40 mm，shape_yx=[80,168]。LF design.npz、转换后的native geometry.npz及右补后的derived geometry.npz是三个不同文件，见下面身份表及JSON。

| 例 | 转换 native HF geometry_id | 右补 HF geometry_id | bound task semantic SHA |
| --- | --- | --- | --- |
| fine | `62dd40a9ed8a41a6a2deb55927982c7f409d63bfedbf96079b2ee032e816da8d` | `ddc7a66a3ef45689e9b9a881155d5e5b4f71475615dcb33b5717a4353c60f91a` | `95ab4d283991a13315caeedab12afb3a84f052cd53d995cab7185433a3fc20d4` |
| wave | `42b201157a5d7a42ef153e026b91a43ce6fe2eb6460128ffce3bb9ac3204c10f` | `5e99dfa60343c1c2da0a921b8ddb7402319e2ad5157aa0135c89a83f1a2c3b4f` | `5c9941a569b69e9b4265eb3da73e7ba60deb991970033650ef56cb67a5b3749e` |

所有geometry JSON／NPZ、task、input_manifest的确切路径、原seal SHA/大小、原LF来源与准备模块epoch已逐项列入JSON；本轮只重核JSON字节和stat，不解码旧数组。L-PREP1是data-only，未构模；L-THIRD1另有未变形兼容性检查，制造资格pending及机械资格未通过仍保持。

## 原准备实测资源

| 阶段 | helper s | outer s | tree peak RSS B | 原采样额度 |
| --- | ---: | ---: | ---: | --- |
| L-PREP1 | 7.938718400022481 | 21.479693799978122 | 166240256 | 8589934592 B |
| L-THIRD1 | 17.13060710002901 | 18.71912630001316 | 198811648 | 1073741824 B |

L-PREP1涵盖3个真实准备、9个有限反例和1张未变形声明图；L-THIRD1还涵盖原ZIP抽取、一次未变形构模与保存、掩码核对及四面板图，后者已在1 GiB采样额度下PASS。下一小规模两包顺序准备建议helper180 s／outer240 s、采样1 GiB；现有证据没有必须采用8 GiB的理由。实测成本不保证下次成本，采样边界也不是OS硬限制；具体新增范围须由新卡明确。

## 可恢复性与限制

fine与wave各两份普通LF文件和共同task模板都已在仓库内。原ZIP路径只保留为来源历史，下一helper不应再读取它。原回执中的旧绝对路径也只作历史上下文；新入口从显式repo根解析本记录相对路径。新输出按自己的新manifest／seal记录，不能预先承诺换目录后的普通descriptor字节SHA与旧输出相等。不得覆盖旧包、移植旧机械资格，或将本次只读准备写成新batch执行。
