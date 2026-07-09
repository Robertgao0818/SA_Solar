# Storyline v2 与技术方案(2026-07-06 重梳)

**Status**: draft v3(round-3 评审自洽性修正已落;待 §5 P1-6 可识别性摸底 + P0-1 位移审计完成后转 execution baseline)
**来源**: 7-agent 资产摸底(`/tmp/zasolar_inventory_2026-07-06.json`)+ 用户原草稿 + 两轮批评修订(含另一 Fable 5 的三形态批评)
**关联文档**: 位移审计 handoff `/tmp/handoff_gehi_displacement_audit_2026-07-06.md`;backdating 任务定义 `solar_backdating/docs/install_date_optimization_v2_prd.md`;验证框架 `docs/validation_strategy.md`、`docs/evaluation_protocol.md`

## 0. 本文的证据纪律

每条关键结论标注证据等级(memory `verdict_evidence_grading` 规则):

- **[F]** = 有文件/数字支撑(附路径或出处)
- **[H]** = 假设 / 文献记忆 / 推理,写论文或对外引用前必须核验

一个先行澄清:本次重梳的起点是"backdating 任务目标和技术栈没有明确"。摸底结论是:**任务定义其实已经明确**(v2 PRD + D1–D19 决策链 [F]),真正缺的是"可对外引用的结论"——三个未关闭的 gate(位移审计、scorer fidelity、gold-set 裁决)导致没有独立精度数字可引。storyline 要修的是 claim 的支撑结构,不是任务定义。

---

## 1. Storyline 主干(四幕)

### 1.1 问题与动机

- 南非没有国家级分布式光伏装机注册,SSEG 注册严重不全——电网运营者与研究者对屋顶光伏的空间分布和采纳时间线双盲 [F: memory `sa_admin_data_limits`;SSEG 匹配三重 confounder 见 memory `sseg_structural_mismatches`]。
- **load-shedding 是动机核心,不是背景注脚**:2022–24 load-shedding 危机构成准实验级的采纳冲击;space×time 装机面板使 event-study / 分布效应设计可行;admin 数据不全恰是需要遥感面板的原因 [H: 经济设计层,论文动机段]。
- **全球产品定位段(审稿人必问"为什么不用现成的")**:Kruitwagen 2021、TZ-SAM、Global Renewables Watch 均为 utility-scale + 10m 级卫星影像,屋顶住宅按设计不可见,且无 building-level 安装日期;住宅级普查只存在于有国家航测计划的富数据国家(DeepSolar/US 等)。SA = 住宅屋顶层 + 采纳时间线双重空白,且是该空白价值最高的国家(无注册 + load-shedding 冲击)[H: 文献记忆,各产品最小可检测规模等数字发稿前核对原文]。

### 1.2 贡献一:普查(where + how much)

- 两大都市区装机级 inventory,已交付:**CT 111,801 装机**(2026-06-21)+ **JHB 41,393 行**(含日期的经济表 [F: `~/zasolar_data/geid_temporal/jhb_full382_fpcut_scan_2026-06-02/`])。CT 的 GT 复评:对 99 个 GT 格 agg_area_F1=0.833、bulk=1.083 [F: `results/analysis/ct_census_gt_eval/`]——**bulk 是面积口径、且只在 GT 子集上测得(面积净高估 ~8%)**;headline 必须与 bulk 及其口径并报,111,801 这个裸计数不单独出现,count 口径的校准区间留给 ESSD 打磨(round-3 修正:不能拿面积 bulk 直接平减计数)。
- 技术路线写成"已验证的系统"而非"选型建议":max-recall 实例分割检测器(torchvision Mask R-CNN R50-FPN,`detect_direct.py`→`finalize.py`,v4_canonical + per-detection 锁定口径)→ SAM2.1 mask+box 边界细化(JHB 生产)→ FP 抑制级联 [F: 摸底 detection-engine 区]。
- **SA 特有原创点:太阳能热水器混淆的双轨抑制**(round-3 修正措辞,消除 [F] 自相矛盾):**训练轨已兑现于模型谱系**——V3-C targeted-HN 起点 → V4/V4.1 HN 世代(77% 热水器采样)[F: memory `v4_hn_strategy` + `configs/datasets/training_sets.yaml` 谱系];**推理轨** = DINOv2 二分类抑制器(per-imagery-layer 校准阈值)[F: `cls_v2_protocol`]。文献无先例 [F: memory `pv_thermal_literature`]。**勿与 P2-10 混写**:`data/negative_pool/` 项目级 HN 档案库(711 行)是后建的持久化池,当前 eligibility gate 未翻转、贡献 0 chips——已入训的是旧世代 HN 集,档案库是待启用的新基建,两者是不同资产。
- 两城后处理不对称(CT: CLS-only;JHB: SAM+Gemini FP-cut)在方法段写成 per-imagery-source 校准的 feature(cls v2 protocol 本就是 per-layer 阈值)[F],不回避。

### 1.3 贡献二:方法论(how do we know it's right)

- **aggregate-first 验证**:成功标准定义在经济分析的使用单元(任务格聚合)而非像素;V1.4 四通道 + Tier-1 指标(σ_Bw/RMSE 主裁判,bulk 仅 sanity gate)+ 口径纪律(双 IoU、双 merge-mode、禁跨口径比较)[F: `docs/evaluation_protocol.md`]。
- **GT 噪声天花板分解**:现有 A2 GT 使 polygon F1@0.5 可测上限约 0.85–0.88;表面"与文献 12pp 差距"中 7–9pp 是指标/GT 伪影 [F: `docs/plans/2026-06-10-rcnn-f1-gap-review.result.json`]。这直接反驳与 curated benchmark(如 Dice 0.998 类数字)的表面对比——升格为方法论贡献写进论文。
- **指标口径表**(round-3 新增:口径纪律也要管住自己的 storyline)。§1.2 的 agg_area_F1=0.833 与本节 polygon 天花板 0.85–0.88 相邻出现会诱导读者做跨口径比较——这正是我们自己禁止的动作;且 12pp gap 暗示 polygon 口径真实 F1 约 0.73–0.78,若只 headline 聚合口径、polygon 数字藏在 gap-review 文档里,被挖出来就是 metric-shopping 观感。修法:主表并报两口径 + 天花板分解(这本身就是贡献二的演示):

| 指标 | 分析单元 | IoU/匹配 | merge-mode | GT 层级 | 可比对象 |
|---|---|---|---|---|---|
| agg_area_F1 / bulk / σ_Bw | 任务格聚合**面积** | 无(面积和) | per-detection | A2 SAM GT(CT 99 格 / JHB clean_gt 25 格) | 仅同口径 census run |
| polygon F1@0.5 | 单装机多边形 | 0.5,installation profile | per-detection | clean_gt(可测天花板 0.85–0.88) | 仅同口径,须并报天花板 |
| Ch1 precision 0.749 | 人工复核样本 | 非 IoU(人判) | — | 人工 | 不与任何 F1 互比 |

- 回应"模块拼接"质疑:拼接的不是模块,是一套在使用单元上闭环的验证体系。

### 1.4 贡献三:追踪(when)——锚定身份 + 存在性时序解码

- **任务定义** [F: v2 PRD]:以普查 polygon 锚定身份(免跨期匹配),GEHI 历史序列逐 vintage presence 打分(Gemini scorer + 蒸馏 ViT 候选,content-addressed verdict store 保证可重现),exact 单调 changepoint 后验 + Turnbull NPMLE EB prior,输出**区间删失**安装日期;明确只 claim first-visible-appearance,不 claim 物理安装日期 [F: D11]。
- **为什么不是 MOT/逐年检测**(provider-conditional 表述,非范式判决):
  - GEHI z19 GSD 地板下的*自由*逐期检测不可靠(3.1% 目标 sub-8px;geid_bbox 原型归档 [F: `_archive/geid_bbox_legacy_2026-05-05/` + `DATA-visibility-gsd-area-2026-07-06.md`]);
  - 静止目标 + present-day anchor 使跨期身份 assignment 问题结构性退化为单锚点 changepoint 解码问题 [推理];
  - 逐期比对本身在 0.15m 市政正射上是现役验证方法(CoJ 审计 ground truth 即逐期比对 [F: `scripts/audit/score_coj_chips.py`])。MOT/SORT 进 related work 作被论证排除的备选。
- **验证三通道** [F]:内部重现性(verdict store + 端到端 reps)/ **外部高频参照**(CoJ ArcGIS 2019/2023 市政航测:**真飞行日期的参照影像**,由它得出的仍是 first-visible 语义而非物理安装日期——D11 纪律贯穿内部术语,round-3 修正原"外部真日期"措辞;16,166 户,gate_nc PASS、gate_a 一层失败根因已诊断)/ 人工 gold-set 裁决(tooling 已建;夜1 部分裁决 ~150 anchors 暴露 dating-unit 结构缺陷,将对 Panel v2 重跑,见 §5)。
- **已知失败模式显式化**(把失败写成"已知已处理"):heater_swap 类非单调序列 → `non_monotone_anomaly` 旗标通道(decoder emission 残差/后验熵 + legacy dip 状态机,两个现成信号源,不改模型);2024 右删失伪影警示随每份交付物 [F: D19(vi)]。**econ 注意**(round-3):被旗标剔除的恰是"有 SWH 的住户"——与 load-shedding treatment 相关的子人群(危机期间换装/加装最活跃),简单 exclude 会引入选择偏差;剔除 vs 显式建模列开放问题 6。
- **emission 的影像质量条件化**(round-3 新增):emission 目前**只按 `quality_flag` 分层** [F: `estimators/emissions.py:5-9` 自述]——PRD D2 spec 的 zoom/imagery-era 轴被 banked panel 缺 achieved-zoom provenance 挡住(明示为 D17/ISSUE-18 territory [F])。后果:模糊早期 vintage 上的 "absent" 与清晰近期 vintage 上的 "absent" 被当作等强证据(仅当 scorer 自报低质量时才降权),会系统性把早期安装的 first-visible 后推。修复几乎免费:Panel v2 re-render 自带 provenance sidecar,解锁 zoom/era 轴;人工侧灵敏度标定来自 gold-set 质量分层早期切片(§5 P0-2b),独立于 scorer 自报质量。
- **对齐不确定性显式化**(round-2 新增):GEHI 跨期不保证像素级对齐 [F: 用户 Opus 检测 + 架构文档 L9/L136 设计了 `alignment_score`/`best_offset_m` 但从未实现 + quality_flag 词表已列 georegistration error]。位移+污染审计为 P0(见 §5),审计产出的位移分布/污染率本身写进方法段,是数据质量透明度的加分项。

### 1.5 数据产品与发布

- space×time 装机面板 + cohort 采纳曲线;GeoParquet/GeoJSON + Zenodo DOI,参照 ESSD Data Descriptor 惯例(草稿此段保留)。
- **发布 schema 区间优先**:`install_interval_start/end`、`earliest_present_date`、分年后验质量列(待补)为主;`install_date` 点值降级为后验摘要列并加旗标——行级点日期恰是两次未过 hard gate 的东西 [F: 列头实测 + D19 口径替换记录 `PRD-AMENDMENT-P1-posterior-mass-caliber-2026-07-04.md`]。
- **provider 合法性**(round-2 新增;round-3 修正构型):GEHI 批量抓取属 ToS 灰区,时间维度目前 100% 依赖它。缓解三件套照旧:只发布派生矢量(绝不再分发影像)、论文写 provider 不写抓取细节、license-clean 复现子集。**round-3 修正**:此前"CoJ 栈升格为主验证层、GEHI 降为 scale extension"的提法混用了**数据层**与**验证层**,且藏着循环——CoJ 审计的全部效力来自它独立于生产管线,一旦 CoJ 影像进入主定日期链路,"用 CoJ 审计验证日期"变成自我验证,外部通道归零(剩余独立检验只有未 run 的 gold-set)。改为**双 provider 一致性设计**:JHB 上 CoJ 市政栈(2000–2023 [F: memory `coj_arcgis_imagery_catalog`;实际 cadence/coverage 待核])与 GEHI **各自独立**跑完整定日期管线,报 concordance——一致性本身是比单向审计更硬的验证证据,并产出 GEHI 单独运行时的误差校准模型,供只有 GEHI 的其他城市带误差条外推。license-clean 叙事、验证独立性、多城扩展三者全保。

---

## 2. 对原草稿的处置表

| 草稿段落 | 处置 | 理由(证据) |
|---|---|---|
| U-Net/smp/DeepSolar 选型 | **重写**为已验证系统 | 普查已交付两城;inventory 需要实例 polygon;口径已锁 [F] |
| FP 抑制"多分类" | **替换**为双轨方案 | HN 池 + DINOv2 抑制器已生产;热水器双轨是文献空白 [F] |
| Google Open Buildings 基线 | **降级+改角色** | 项目实际用 Overture(7 城已下载);footprint 的真实用途是新城 onboarding + resi/com 分轨 kW 标定(斜率差 4×,R²=0.196 vs 0.879)[F: `sseg_kw_calibration_2026-05-10/summary.csv`]。收着写:Overture 非洲 footprint 大量吸收 GOB 捐赠数据 [H: 待核],换名不换血统,GOB 区域性偏移 caveat 照样适用——不得写出"不用 GOB 故无此问题"的意味 |
| 配准 Sobel+NCC | **移位保留**(round-2 修正,原判"删除"撤回) | 不属于检测环节,属于时序 chip 完整性;成为 P0 位移审计的方法核心 [F: 见 §1.4 对齐段] |
| SORT/匈牙利/MOT | **移入 related work** | provider-conditional 拒绝,三条理由见 §1.4;"住宅 vs 电站分轨"直觉保留,电站边界扩建追踪列 extension |
| Street View/众包验证 | **替换**为三通道 | 已建的重现性/市政审计/gold-set 更强;Street View 仅热水器核实辅助 [F] |
| 数据发布(Zenodo/ESSD) | **保留** | 与 16 列 schema 对齐即可 |
| GEE/LandTrendr、scipy Hungarian | **移除** | provider 是 GEHI 非 GEE;无 assignment 问题可解 |

---

## 3. 技术栈表(实际版)

| 环节 | 实际栈 | 状态 |
|---|---|---|
| 普查检测 | torchvision Mask R-CNN R50-FPN(detect_direct→finalize,v4_canonical+per-detection) | 生产,两城已交付 |
| 边界细化 | SAM2.1-hiera-large mask+box refine | JHB 生产;CT 未用(§1.2 已 justify) |
| FP 抑制 | HN 池(训练时)+ solar_cls DINOv2-S adaptive-chip(CT)+ Gemini FP-cut(JHB) | 生产 |
| 验证 | V1.4 四通道 + Tier-1 kernel(`core/eval_matching`、`core/area_metrics`) | 生产(Ch1/2/4 待脚本化) |
| 多城基建 | regions.yaml + region_registry;7 城 Vexcel task grid + Overture 密度 prep | CT/JHB 完成;6 城 0 tiles |
| 历史影像 | GEHistoricalImagery(z19/z18 + catalog cache) | 生产,唯一 provider(合法性缓解见 §1.5) |
| 影像完整性 | 位移+污染审计(edge + phase correlation,双容差判据) | **P0 新增,未跑** |
| Presence 打分 | Gemini(生产默认)→ DINOv3-L-SAT / DINOv2-S 蒸馏候选 | ISSUE-06 gate 未跑 |
| 日期估计 | exact monotone changepoint posterior + Turnbull NPMLE EB prior(PAVA 证伪地板) | 生产默认(D19 口径) |
| 异常通道 | non_monotone_anomaly 旗标(emission 残差 + dip 状态机) | P1 待建 |
| 外部精度 | CoJ 市政审计(16,166 户)+ gold-set 人工裁决(n=500) | 审计已跑;裁决未跑 |
| 建筑分层 | Overture footprint → resi/com 分轨 kW 标定 | pilot(n=55, R²=0.64) |
| 发布 | 区间优先 schema → GeoParquet + Zenodo DOI | JHB 表需在新 estimator 下重算 |

---

## 4. Claim-支撑结构:今天能说什么、什么被 gate 挡着

**今天可引用 [F]**:两城 census 数字及其 GT 复评;CoJ 审计通过的 gate(gate_nc);重现性数字(survival 通道 TVD);V1.4 框架与 GT 天花板分解。

**被 gate 挡住(不 run 不能说)**:

| 想要的 claim | 挡着它的 gate | 状态 |
|---|---|---|
| 安装日期独立精度(人工验证) | 顺序链:位移审计 → ISSUE-06 → Panel v2 重建 → ISSUE-11(§5) | 夜1 部分裁决(~150 anchors)已暴露 dating-unit 结构缺陷,旧 run 判不抢救 [F: memory `issue11_prep_collision`];裁决包将对 Panel v2 重建 |
| per-target 唯一评分 panel(修复 96m chip-group 评分不唯一) | 位移审计定几何 + Panel v2 重建 | 未开始;方向已定 = gap audit `ae3b003` 修正案 A(dating unit 改 per-target)[F] |
| 自托管 scorer 替代 Gemini(或"22M 学生打平 LLM"叙事) | ISSUE-06 fidelity gate | blocker 全清,未 run |
| tight12 紧裁几何可用(Phase-3 蒸馏 + Panel v2 前提) | 位移+污染审计 | handoff 已写,未 run |
| CT 时间维度任何数字 | CT backdating 整体未跑(v2 明确 out of scope) | 零数字 |

**风险登记(论文必须主动披露的)**:provider 合法性(§1.5);D19 口径替换的透明表述(headline 从 hard-MAP 点日期换成 fractional posterior-mass 的决策过程);位移未测(审计后转为已测);GT 天花板;2024 右删失伪影;34.8% recovered-ambiguous 层的负载性 [F: ISSUE-03 C2];**右删失 × load-shedding 退场同向叠加**(round-3 新增):2024-03 起 load-shedding 长期暂停、屋顶光伏需求真实回落 [H: 需核 SARS 进口/SAPVIA 口径] 与右删失伪影**同号、同期**——采纳曲线下行段里真实效应与测量伪影不可分;且 2022Q4–2023 安装峰值恰落在 first-visible 滞后最长的窗口。econ paper 的 event-study 承诺("采纳响应 load-shedding 强度")在 P1-6 可识别性摸底完成前不得写出;缓解 = 可靠地平线截断列(Panel v2 schema)+ 外部总量序列尾部校准。

---

## 5. 执行优先级(2026-07-06 修订:ISSUE-11 重排到管线改进之后,owner 决策)

- **P0(DAG:1 与 2 并行,汇合于 3)**
  1. GEHI 位移+污染审计(为 Panel v2 定 per-target 几何;handoff: `/tmp/handoff_gehi_displacement_audit_2026-07-06.md`)。CPU-only。
  2. ISSUE-06 fidelity gate(scorer/backbone 选型)——**与 1 并行**:两者正交(几何选型 vs backbone 选型),资源不冲突(gate 主要是对已有 verdict store 的分析,held-out 打分已存在)。放在重建之前的成本协同:若蒸馏学生过 gate,Panel v2 全量重扫从 Gemini quota 变成本地推理。**附带条件(预注册进 gate 文档)**:结论以 banked96 几何为条件;Panel v2 换几何后,赢家须在重渲染样本上做廉价 fidelity 复检——两 head 现打平在噪声内(0.797 vs 0.7968),排名翻转风险真实;若仍打平,默认选便宜的 DINOv2-S(falsification floor 的设计意图)。若两线派并行 agent 同动 solar_backdating,分 worktree 或文件白名单不相交(07-05 双 session 相撞前科,memory `multi_session_same_repo`)。
  2b. **gold-set 质量分层早期切片**(round-3 新增;位移审计之后即可跑,与 ISSUE-06 并行):n≈100–150,按 z-level × 年份 × quality_flag 分层的**帧级可见性**人工标注——与 FPD 裁决不同,它不依赖管线 claimed 窗口,标注跨 panel 版本永久有效,故不违反"人工资本只花一次"原则。产出 = scorer 分质量层灵敏度(独立于 scorer 自报 quality),喂 Panel v2 的 emission 校准(§1.4)。前置 [F]:裁决 UI 已有 modal-FPD marker + `off_roof_marker` 几何旗标(`build_goldset_strip_html.py:303,318`;夜1 notes 已见 `marker_off_target:` ——污染已实际到达人工裁决层),重建包时保留并强化 anchor 叠加;位移审计若显示污染严重,先修叠加/re-center 再标注,否则人工裁的是邻居屋顶。
  3. **Panel v2 重建**(新增):per-target 唯一评分几何(首选 tight12;若审计显示位移不可 re-center,退回 adaptive clamp——公式已存在于孤儿脚本 `build_gt_anchor_manifest.py`,勿硬耦合 tight12)+ 选型后 scorer + decoder+EB(D19 口径)+ `non_monotone_anomaly` 旗标 + **质量条件化 emission**(re-render 自带 achieved-zoom provenance,解锁 PRD D2 的 zoom/era 分层轴;人工灵敏度输入来自 2b)+ 区间优先 schema(分年后验质量列、`install_date` 降级为后验摘要、**可靠地平线截断列**——P(visible|installed) 低于阈值的近期时段明示不可用)。吸收原 P1-4/P1-5。动机 [F]:当前生产 panel 的 96m chip-group 跨 target 共享 chip,PV presence 评分不唯一(`build_inventory_chip_groups.py` chip-group 结构;`SPEC-GAP-AUDIT-goldset-night1-2026-07-05` 标记 per-chip vs per-target 单位对齐;gap audit `ae3b003` 修正案 A 已定 per-target 方向)。
  4. ISSUE-11 gold-set 人工裁决——**对 Panel v2 做,不对现 panel 做**。依据:夜1 部分裁决(~150 anchors)已暴露结构缺陷,旧 run 判不抢救 [F: memory `issue11_prep_collision`];人工裁决资本只花一次,花在拟发布的 panel 上;goldset 窗口围绕管线 claimed FPD 采样,panel 换版本本来就需重渲染 strips(tooling 全部可复用,4.2G 包重建)。**显式接受的代价**:独立精度数字后移——Panel v2 + 裁决完成前,论文不得引用任何独立精度 claim(§4 表第一行)。
- **P1**
  5. provider 缓解写入发布方案;**双 provider 一致性设计评估**(round-3 替代原"CoJ 升格主验证层"——该提法会拆掉审计通道的独立性,见 §1.5)+ CoJ catalog cadence/coverage 核验;探测 CT 市政 WMS 历史 vintage [H: 是否存在未知]
  6. **删失×需求退场可识别性摸底**(round-3 新增,gates econ paper / 开放问题 3):拉 JHB(+候选城)2021–2025 逐年 vintage 密度,用现有 Turnbull 框架在真实删失结构下模拟采纳曲线可识别性;外部总量序列(SARS 组件进口、Eskom BTM 估计 [H: 序列可得性待核])做尾部校准 = validation_strategy bonus Channel 5 的具体化。半天–一天,CPU-only。
  7. CT 时间维度表述决策(建议:第一版 = JHB 深验证 + 方法可迁移性,CT 列 next,不为叙事对称开新战线)
  8. SAM area bug 修复 commit(未 commit 前 JHB 面积聚合数字不可全信 [F: 工作树未提交改动])
- **P2(扩展,不阻塞 storyline)**
  9. Vexcel downloader 泛化 + 6 城影像;10. HN 池 eligibility gate 翻转(注意 §1.2:档案库 ≠ 已入训的旧 HN 集);11. zerov2 按诊断阶梯 kill-or-revive(不进主线叙事)

---

## 6. 开放问题(下轮优化的切入点)

1. **双 provider 一致性设计的落地评估**(round-3 已裁定方向,替代原"升格主验证层"提法):CoJ catalog 2000–2023 的实际 cadence/coverage/获取成本;JHB 双链路 concordance 的口径设计(两条链全程独立,只在比较层汇合,否则又造出自我验证)。
2. **CT 时间维度**:第一版论文是否只 claim JHB?(本文建议是,见 P1-7,但这决定摘要怎么写。)
3. ~~目标体裁与拆分~~ **已裁定 [F: owner 确认 2026-07-06]:ESSD Data Descriptor 先行**——理由:今天 [F] 级资产(census、验证框架、GT 天花板分解、CoJ 审计)恰好构成 Data Descriptor 全部主角;econ paper 被 P1-6 可识别性摸底 gate 住;先拿 DOI,econ 文引用数据集,贡献切分与求职叙事分工最干净。"aggregate-first 验证"在 ESSD 语境是加分项——venue 定了贡献二的位置。**遗留联动(并入 Q2)**:ESSD 的收录范围——census-only(两城,今天即 [F]-ready)还是 census + JHB 时间面板(带删失/验证 caveat)——取决于 P0 链(Panel v2 + ISSUE-11)相对投稿时点的进度,与 Q2 一起定。
4. **D19 口径替换的披露方式**:方法段直述"点日期未过 hard gate、headline 落在 cohort 层的 fractional posterior"是最稳的写法,但措辞需要打磨。
5. **全球产品定位段的文献核验**(§1.1 [H] 项):Kruitwagen/TZ-SAM/GRW 的最小可检测规模、日期粒度,建议交给一次 deep-research 跑核验;顺带核 §4 的 load-shedding 暂停时点/SARS 进口序列与 §2 的 Overture-GOB 血统 [H] 项。
6. **heater_swap 旗标户的处置**(round-3 新增):被旗标剔除的是"有 SWH 的住户"——与 load-shedding treatment 相关的子人群(危机期间换装/加装最活跃),简单 exclude 引入选择偏差;剔除、加权(IPW)还是显式建模(two-state 扩展),需 econ 设计侧定夺。
