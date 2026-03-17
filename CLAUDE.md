# CLAUDE.md

Cape Town rooftop solar installation detection & evaluation pipeline. Uses geoai (Mask R-CNN ResNet50-FPN) to detect solar installations from aerial GeoTIFFs, evaluates against hand-labeled ground truth (weak supervision). Supports fine-tuning on Cape Town annotations.

**Task definition (V1.2)**: installation-level footprint segmentation — one polygon per solar installation, not per panel. See `data/annotations/ANNOTATION_SPEC.md`.

## Directory Structure

```
data/
  task_grid.gpkg              — Grid 编号集合
  annotations/                — 弱监督标注（详见 annotations/README.md）
    G1238.gpkg                — QGIS 航测图标注 (124 polygons, layer g1238__solar_panel__cape_town_g1238_)
    solarpanel_g0001_g1190.gpkg — Google Earth 标注（已校准, G1189=58, G1190=76, 其余少量）
    ANNOTATION_SPEC.md        — V1.2 标注规范（installation footprint 定义）
    annotation_manifest.csv   — 标注 manifest (quality tier T1/T2, review status)
  coco/                       — COCO 格式训练数据（export_coco_dataset.py 生成）
tiles/<GridID>/               — 各 Grid 的航测瓦片 + VRT
results/<GridID>/             — 检测结果、评估报告、图表
  masks/                      — per-tile 检测掩膜
  vectors/                    — per-tile 矢量化结果
  presence_metrics.csv        — V1.2 installation presence P/R/F1
  footprint_metrics.csv       — V1.2 footprint IoU/Dice 分布
  area_error_metrics.csv      — V1.2 面积误差分桶
checkpoints/                  — 微调模型权重
docs/                         — 工作流文档
scripts/
  bootstrap_manifest.py       — 从 GPKG 生成初始 annotation manifest
```

## Scripts

- `detect_and_evaluate.py` — 主流程（检测→过滤→评估→可视化），支持 `--model-path`、`--evaluation-profile`、`--data-scope`
- `export_coco_dataset.py` — 标注→COCO 实例分割数据集导出（chip 切分 + train/val 划分 + georeferenced chips），支持 `--manifest`、`--tier-filter`、`--category-name`
- `train.py` — Mask R-CNN 微调训练（两阶段：heads-only → full fine-tune），需要 CUDA GPU
- `building_filter.py` — OSM+Microsoft 建筑轮廓 → buildings.gpkg + tile_manifest.csv
- `tiles/build_vrt.py` — WMS 瓦片配准 + VRT 拼接，GRID_ID 变量控制目标 Grid
- `grid_utils.py` — Grid 路径/坐标工具函数
- `scripts/bootstrap_manifest.py` — 标注 manifest 初始化

## Fine-tuning Workflow

```bash
# 0. 生成标注 manifest（首次或标注变更后）
python3 scripts/bootstrap_manifest.py

# 1. 导出 COCO 数据集（400×400 chips, 0.25 overlap, 80/20 split）
python export_coco_dataset.py --output-dir data/coco

# 1b. 仅用 T1 标注导出（可选）
python export_coco_dataset.py --output-dir data/coco_t1 \
  --manifest data/annotations/annotation_manifest.csv --tier-filter T1

# 2. 训练前检查依赖和 CUDA（train.py 会强制要求 GPU）
./scripts/check_env.sh

# 3. 训练（需要 CUDA GPU）
python train.py --coco-dir data/coco --output-dir checkpoints

# 4. 使用微调模型推理 + installation profile 评估
python detect_and_evaluate.py --model-path checkpoints/best_model.pth --force
```

## Inference

```bash
python building_filter.py
python tiles/build_vrt.py
python detect_and_evaluate.py   # 默认使用 geoai 内置权重, requires GPU
python detect_and_evaluate.py --model-path checkpoints/best_model.pth  # 微调权重

# V1.2: 选择评估模式
python detect_and_evaluate.py --evaluation-profile installation  # 默认: 三层指标
python detect_and_evaluate.py --evaluation-profile legacy_instance  # 旧版兼容
```

Detection writes `results/<GridID>/config.json` alongside predictions and only reuses prior outputs when the saved config matches current code/parameters. Use `--force` to re-run detection explicitly. V1.2 adds `evaluation_config` section to config.json for traceability.

Training dependencies beyond baseline inference include `torch`, `torchvision`, `opencv-python-headless`, `huggingface_hub`, and `pycocotools`. Empty-target chips are retained in the exported dataset and are intentionally passed through training so the detector learns hard negatives.
