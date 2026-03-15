# CLAUDE.md

Cape Town rooftop solar panel detection & evaluation pipeline. Uses geoai (Mask R-CNN ResNet50-FPN) to detect solar panels from aerial GeoTIFFs, evaluates against hand-labeled ground truth (weak supervision). Supports fine-tuning on Cape Town annotations.

## Directory Structure

```
data/
  task_grid.gpkg              — Grid 编号集合
  annotations/                — 弱监督标注（详见 annotations/README.md）
    G1238.gpkg                — QGIS 航测图标注 (124 polygons, layer g1238__solar_panel__cape_town_g1238_)
    solarpanel_g0001_g1190.gpkg — Google Earth 标注（已校准, G1189=58, G1190=76, 其余少量）
  coco/                       — COCO 格式训练数据（export_coco_dataset.py 生成）
tiles/<GridID>/               — 各 Grid 的航测瓦片 + VRT
results/<GridID>/             — 检测结果、评估报告、图表
  masks/                      — per-tile 检测掩膜
  vectors/                    — per-tile 矢量化结果
checkpoints/                  — 微调模型权重
docs/                         — 工作流文档
```

## Scripts

- `detect_and_evaluate.py` — 主流程（检测→过滤→评估→可视化），支持 `--model-path` 加载自定义权重
- `export_coco_dataset.py` — 标注→COCO 实例分割数据集导出（chip 切分 + train/val 划分）
- `train.py` — Mask R-CNN 微调训练（两阶段：heads-only → full fine-tune），需要 CUDA GPU
- `building_filter.py` — OSM+Microsoft 建筑轮廓 → buildings.gpkg + tile_manifest.csv
- `tiles/build_vrt.py` — WMS 瓦片配准 + VRT 拼接，GRID_ID 变量控制目标 Grid
- `grid_utils.py` — Grid 路径/坐标工具函数

## Fine-tuning Workflow

```bash
# 1. 导出 COCO 数据集（400×400 chips, 0.25 overlap, 80/20 split）
python export_coco_dataset.py --output-dir data/coco

# 2. 训练（需要 CUDA GPU）
python train.py --coco-dir data/coco --output-dir checkpoints

# 3. 使用微调模型推理
python detect_and_evaluate.py --model-path checkpoints/best_model.pth --force
```

## Inference

```bash
python building_filter.py
python tiles/build_vrt.py
python detect_and_evaluate.py   # 默认使用 geoai 内置权重, requires GPU
python detect_and_evaluate.py --model-path checkpoints/best_model.pth  # 微调权重
```

Detection writes `results/<GridID>/config.json` alongside predictions and only reuses prior outputs when the saved config matches current code/parameters. Use `--force` to re-run detection explicitly.
