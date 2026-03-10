# Cape Town Rooftop Solar Panel Detection

基于航测影像的开普敦屋顶太阳能板检测与评估流水线。

## 项目进度

| Grid | 底图 | 标注 | 检测 | 评估 | 备注 |
|------|------|------|------|------|------|
| G1238 | done | done (QGIS) | done | done | 首个完整流程 Grid |
| G0001-G1190 | - | done (Google Earth, 已校准) | - | - | 弱监督标注，待分配底图 |

## 快速开始

```bash
source scripts/activate_env.sh
python building_filter.py          # 下载建筑轮廓
python tiles/build_vrt.py          # 瓦片配准 + VRT 拼接
python detect_and_evaluate.py      # 检测 + 评估（需 GPU）
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
