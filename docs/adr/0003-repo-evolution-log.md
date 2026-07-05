# ADR-0003: 仓库演化决策日志（dated pivots / migrations / splits）

- **Status**: Accepted — append-only 历史记录（新条目只追加，不改写旧条目）
- **Created**: 2026-07-03
- **Driver**: CLAUDE.md 重构 — 入口文档只保留现状陈述，全部带日期的演变叙事迁入本文档，恢复入口文档的规则密度

## Context

CLAUDE.md / AGENTS.md 曾同时承担"操作手册"与"变更史"两个角色：V1.4 pivot、
子仓拆分、数据迁移、provider 切换等叙事各带日期散布在入口文档里，稀释了
真正需要每次会话遵守的规则。本文档接管变更史：每条记录 = 日期 + 决策 +
现状后果 + 证据指针；入口文档只写现状（如"本仓库无 `scripts/temporal/`"）。

## Decision log

| 日期 | 决策 | 现状后果 | 记录 |
|---|---|---|---|
| 2026-04-03 | **V1.3 任务定义**：reviewed prediction footprint segmentation | GT 遵循 installation-level 规则；`installation` profile 为默认评估口径 | `data/annotations/ANNOTATION_SPEC.md`, `.claude/rules/07-annotation-semantics.md` |
| 2026-04-19 | tiles/results 重构为 region × imagery_layer / region × model_run 布局 | 路径一律经 `core.grid_utils` / `core.region_registry` 解析，禁止 hardcode | `docs/plans/2026-04-19-tiles-results-restructure.md`, `.claude/rules/06-multi-city.md` |
| 2026-04-22 | **V1.4 pivot**：成功指标从 per-polygon F1 改为 grid 级聚合 inventory；四通道 validation（stratified P / exhaustive R / plausibility / external） | per-polygon F1 降为诊断；task grid 为主聚合单元 | `docs/validation_strategy.md` |
| 2026-04-26 | 大数据迁移 `/mnt/d/ZAsolar/` → `~/zasolar_data/`（WSL ext4） | 项目内 `tiles/` `results/` 只是占位/symlink；`SOLAR_TILES_ROOT` env；过渡 symlink（`tiles_joburg` / `results_joburg` / `tiles/joburg_geid`）已删且不得重建 | `.claude/rules/06-multi-city.md`, `docs/governance/repo-rules.md` |
| 2026-05-05 | **solar_backdating 子仓拆分**（install-date 主线）；`geid_bbox` GEID free-detection 原型归档 | temporal / install-date 工作只进子仓；原型冷存于 `/home/gaosh/projects/_archive/geid_bbox_legacy_2026-05-05/` | `solar_backdating/SHARED_FROM_ZASOLAR.md` |
| 2026-05-13 | 主仓 temporal 脚手架删除；**GEHistoricalImagery（Mbucari CLI）定为唯一历史影像 download provider** | 本仓库无 `scripts/temporal/` `tests/temporal/` `configs/temporal/`；旧 GEID 协议栈（Indy/ssleay32/SendMessage/cipher_key）不再是项目依赖 | `solar_backdating/docs/gehi_temporal_replacement_plan.md` |
| 2026-05-29 | **solar_cls 子仓拆分**（PV/non-PV FP suppressor，镜像 backdating plugin 模式） | 本仓库无 `scripts/classifier/` `tests/classifier/` `configs/classifier/` `data/cls_*` 实体；seam = `data/cls_pv_thermal_v2` gitignored symlink → `~/zasolar_data/cls/data/cls_pv_thermal_v2/`（供 `scripts/training/negative_pool/bootstrap_from_cls_v2.py` 只读） | `solar_cls/SHARED_FROM_ZASOLAR.md`, `docs/handoffs/2026-05-29-cls-extract-and-trainpool-handoff.md` |
| 2026-06-03 | JHB canonical grid 方案 = JNB Vexcel-382；老 Gxxxx/JHBnn namespace 退役 | 老 ID 经 retired-namespace 两级解析永久可查（eval GT / provenance 不可遗忘） | ADR-0002 |
| 2026-06-12 | CT CPT regrid（G→CPT digit-preserving，1103 cells）+ retired namespace 政策落地；架构优化主线 6 步落地 | 无 active 区域拥有裸 `G\d{4}`；crosswalk `data/ct_grid_crosswalk_g_to_cpt.csv` | ADR-0002, ADR-0001 |
| 2026-06-16 | CT census 全量完成（2083 grid，detect_direct→finalize per-det + CLS-only） | 全局 union-merge@IoU0.1 → 111,801 装机 / 5.0 km²；报告与 GT eval 见 validation docs | `docs/validation/2026-06-24-ct-census-gt-validation.md`, ROADMAP |

## Consequences

- CLAUDE.md / AGENTS.md 只写现状陈述，不复述以上日期与过程；需要"为什么变成
  这样"时来查本表。
- 新的 pivot / 迁移 / 拆分在落地的同一个 commit 中向本表追加一行
  （repo-rules "文件移动必须同步更新文档"的执行位）。
