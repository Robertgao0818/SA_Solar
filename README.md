# Cape Town Rooftop Solar Panel Detection

基于航测影像的开普敦屋顶太阳能安装检测与评估流水线。

**V1.2 任务定义**: installation-level footprint segmentation — 每个 polygon 表示一个太阳能安装的轮廓，非逐 panel 分割。

## 项目进度

| Grid | 底图 | 标注 | 检测 | 评估 | 备注 |
|------|------|------|------|------|------|
| G1238 | done | done (QGIS) | done | done | 首个完整流程 Grid |
| G1189 | done | done (Google Earth, 已校准) | done | done | Fine-tuned F1≈0.595 |
| G1190 | done | done (Google Earth, 已校准) | done | done | Fine-tuned F1≈0.649 |

详细进度见 `STATUS.md` 和 `ROADMAP.md`。

## 快速开始

```bash
./scripts/bootstrap_env.sh         # 首次创建/更新 .venv
source scripts/activate_env.sh
./scripts/check_env.sh             # 同时检查训练依赖与 CUDA 可用性
python building_filter.py          # 下载建筑轮廓
python tiles/build_vrt.py          # 瓦片配准 + VRT 拼接
python detect_and_evaluate.py      # 检测 + 评估（需 GPU, 默认 installation profile）
python detect_and_evaluate.py --evaluation-profile legacy_instance  # 旧版兼容模式
python detect_and_evaluate.py --force
```

## 本地环境

```bash
./scripts/bootstrap_env.sh         # 首次创建/更新 .venv
source scripts/activate_env.sh     # 进入项目环境
./scripts/check_env.sh             # 检查关键依赖和运行时目录
./scripts/run_multigrid_gpu.sh     # 在你的 WSL 终端里用 GPU 跑 3-grid baseline + 泛化验证
```

- 虚拟环境固定在 `./.venv`
- 运行时缓存也固定在仓库内：`.cache/`、`.config/`、`.local/`、`.tmp/`
- 当前环境快照已写入 `requirements.lock.txt`，重建时优先使用它
- `train.py` 会强制验证 CUDA；如果 `./scripts/check_env.sh` 显示 `cuda_available=False`，训练不会启动

## 目录结构

```
data/               GIS 数据（task grid、标注）
tiles/<GridID>/     各 Grid 的航测瓦片
results/<GridID>/   各 Grid 的检测结果与评估
docs/               工作流文档
```

## CRS 约定

- QGIS 标注导出、人工交换格式：`EPSG:4326`
- 航测瓦片地理参考：`EPSG:4326`
- 检测后处理、面积/长度/buffer、IoU 评估：`EPSG:32734`
- 最终给 QGIS 回看的导出结果：`results/<GridID>/predictions.geojson`（`EPSG:4326`）
- 若需保留米制计算结果：`results/<GridID>/predictions_metric.gpkg`（`EPSG:32734`）

## 结果复用规则

- 每次检测都会在 `results/<GridID>/config.json` 记录本次运行参数和脚本指纹
- 若已有 `predictions_metric.gpkg` / `predictions.geojson`，脚本只会在 `config.json` 与当前配置完全一致时复用旧结果
- 若结果缺少 `config.json`，或配置/代码已变化，请使用 `python detect_and_evaluate.py --force` 重新检测
- 参数搜索同样会在 `results/<GridID>/param_search/<experiment_id>/config.json` 记录每组实验配置，并支持 `python param_search.py --force`

## Fine-tuning

```bash
source scripts/activate_env.sh
./scripts/check_env.sh

python export_coco_dataset.py --output-dir data/coco
python export_coco_dataset.py --output-dir data/coco_t1 \
  --manifest data/annotations/annotation_manifest.csv --tier-filter T1  # 仅 T1
python train.py --coco-dir data/coco --output-dir checkpoints
python detect_and_evaluate.py --model-path checkpoints/best_model.pth --force
```

- `export_coco_dataset.py` 会导出带地理参考的 `400x400` chip、`train.json` / `val.json` 和 provenance CSV
- 训练集会保留空标注 chip，负样本会真正进入 Mask R-CNN 训练，而不是只在导出阶段平衡
- 若你重建环境，训练相关依赖需要 `torch`、`torchvision`、`opencv-python-headless`、`huggingface_hub`、`pycocotools`
