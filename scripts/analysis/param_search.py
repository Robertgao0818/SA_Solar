"""
参数网格搜索：扫描 chip_size / overlap / min_object_area 组合
Parameter Grid Search for Solar Panel Detection

用法：
  python param_search.py          # 运行全部组合
  python param_search.py --dry    # 只打印组合，不实际运行
  python param_search.py --force  # 忽略已有实验结果并重跑

每组实验输出到 results/<GRID_ID>/param_search/<experiment_id>/
汇总表输出到 results/<GRID_ID>/param_search/summary.csv
"""

import argparse
import itertools
import sys
import time

import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import detect_and_evaluate as pipeline
from core.grid_utils import DEFAULT_GRID_ID, normalize_grid_id

# ════════════════════════════════════════════════════════════════════════
# 搜索空间
# GSD ≈ 0.08 m/pixel，chip_size=400 只覆盖 ~30m，大阵列容易被切断
# 偏向大 chip 搜索；同时搜索 epsilon（orthogonalize 简化强度）
# ════════════════════════════════════════════════════════════════════════
PARAM_GRID = {
    "chip_size": [(400, 400), (640, 640), (800, 800), (1024, 1024)],
    "overlap": [0.25, 0.35],
    "min_object_area": [1.0, 2.0],
}

def run_search(dry_run: bool = False,
               force: bool = False,
               grid_id: str = DEFAULT_GRID_ID):
    """遍历参数组合，每组跑检测 + 评估。"""
    pipeline.set_grid_context(normalize_grid_id(grid_id))
    search_dir = pipeline.OUTPUT_DIR / "param_search"

    combos = list(itertools.product(
        PARAM_GRID["chip_size"],
        PARAM_GRID["overlap"],
        PARAM_GRID["min_object_area"],
    ))
    print(f"参数搜索: {len(combos)} 组实验")
    print(f"Grid: {pipeline.GRID_ID}")
    print(f"输出目录: {search_dir}\n")

    if dry_run:
        for i, (cs, ov, ma) in enumerate(combos, 1):
            print(f"  [{i:02d}] chip_size={cs}, overlap={ov}, min_area={ma}")
        return

    search_dir.mkdir(parents=True, exist_ok=True)

    # 预加载 GT（只加载一次）
    gt = pipeline.load_ground_truth()

    results = []
    summary_path = search_dir / "summary.csv"

    for i, (cs, ov, ma) in enumerate(combos, 1):
        exp_id = f"cs{cs[0]}_ov{ov:.2f}_ma{ma:.1f}"
        exp_dir = search_dir / exp_id

        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(combos)}] {exp_id}")
        print(f"  chip_size={cs}, overlap={ov}, min_object_area={ma}")

        exp_config = pipeline.build_detection_config(
            chip_size=cs,
            overlap=ov,
            min_object_area=ma,
            output_dir=exp_dir,
        )
        reuse_existing = pipeline.should_reuse_predictions(
            exp_dir, exp_config, force=force
        )
        pred_metric_path = exp_dir / "predictions_metric.gpkg"
        pred_path = exp_dir / "predictions.geojson"

        if reuse_existing:
            print("  [SKIP] 现有实验结果与 config.json 一致，直接评估")
        else:
            t0 = time.time()
            try:
                pipeline.detect_solar_panels(
                    chip_size=cs,
                    overlap=ov,
                    min_object_area=ma,
                    output_dir=str(exp_dir),
                )
            except Exception as e:
                print(f"  [ERROR] 检测失败: {e}")
                results.append({
                    "experiment_id": exp_id,
                    "chip_size": cs[0],
                    "overlap": ov,
                    "min_object_area": ma,
                    "status": "error",
                    "error": str(e),
                })
                continue
            elapsed = time.time() - t0
            print(f"  检测耗时: {elapsed:.1f}s")

        # 评估
        try:
            import geopandas as gpd
            load_path = pred_metric_path if pred_metric_path.exists() else pred_path
            pred = gpd.read_file(str(load_path))
            if pred.crs is None:
                assumed_crs = (
                    pipeline.METRIC_CRS
                    if load_path == pred_metric_path
                    else pipeline.EXPORT_CRS
                )
                pred = pred.set_crs(assumed_crs)
            pred = pred.to_crs(pipeline.METRIC_CRS)
            pred = pred[pred.geometry.notnull() & pred.is_valid].copy()

            metrics = pipeline.iou_matching(
                gt, pred, iou_threshold=pipeline.DEFAULT_IOU
            )

            row = {
                "experiment_id": exp_id,
                "chip_size": cs[0],
                "overlap": ov,
                "min_object_area": ma,
                "n_pred": len(pred),
                "tp": metrics["tp"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
                "precision": round(metrics["precision"], 4),
                "recall": round(metrics["recall"], 4),
                "f1": round(metrics["f1"], 4),
                "status": "done",
            }
            results.append(row)
            print(f"  P={row['precision']:.4f}  R={row['recall']:.4f}  "
                  f"F1={row['f1']:.4f}  (TP={row['tp']} FP={row['fp']} FN={row['fn']})")

        except Exception as e:
            print(f"  [ERROR] 评估失败: {e}")
            results.append({
                "experiment_id": exp_id,
                "chip_size": cs[0],
                "overlap": ov,
                "min_object_area": ma,
                "status": "eval_error",
                "error": str(e),
            })

        # 每组实验后增量保存汇总
        pd.DataFrame(results).to_csv(
            str(summary_path), index=False, encoding="utf-8-sig"
        )

    # 最终汇总
    df = pd.DataFrame(results)
    df.to_csv(str(summary_path), index=False, encoding="utf-8-sig")

    print(f"\n{'=' * 60}")
    print(f"参数搜索完成! 汇总表: {summary_path}")
    if "f1" in df.columns:
        done = df[df["status"] == "done"].sort_values("f1", ascending=False)
        if len(done) > 0:
            print(f"\nTop 5 by F1:")
            print(done.head(5)[["experiment_id", "precision", "recall", "f1",
                                "tp", "fp", "fn"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="参数网格搜索：扫描 chip_size / overlap / min_object_area"
    )
    parser.add_argument(
        "--grid-id",
        default=DEFAULT_GRID_ID,
        help=f"目标 grid，默认 {DEFAULT_GRID_ID}",
    )
    parser.add_argument("--dry", action="store_true", help="只打印实验组合")
    parser.add_argument(
        "--force",
        action="store_true",
        help="忽略已有实验结果和 config.json，重新跑所有组合",
    )
    args = parser.parse_args()
    try:
        run_search(
            dry_run=args.dry,
            force=args.force,
            grid_id=args.grid_id,
        )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
