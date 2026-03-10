#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import detect_and_evaluate as pipeline
from grid_utils import DEFAULT_GRID_ID, normalize_grid_id


def parse_args():
    parser = argparse.ArgumentParser(description="Run baseline/generalization across grids")
    parser.add_argument(
        "--grid-ids",
        nargs="+",
        default=[DEFAULT_GRID_ID, "G1189", "G1190"],
        help="要运行的 grid 列表",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重跑检测",
    )
    parser.add_argument(
        "--output-subdir",
        default="baseline_default",
        help="结果子目录，默认 baseline_default",
    )
    parser.add_argument("--chip-size", type=int, default=None)
    parser.add_argument("--overlap", type=float, default=None)
    parser.add_argument("--min-object-area", type=float, default=None)
    parser.add_argument("--confidence-threshold", type=float, default=None)
    parser.add_argument("--mask-threshold", type=float, default=None)
    parser.add_argument(
        "--best-from-summary",
        default=None,
        help="从 results/<grid>/param_search/summary.csv 读取最佳参数，例如 G1238",
    )
    return parser.parse_args()


def load_best_params(grid_id: str) -> dict:
    summary_path = Path("results") / normalize_grid_id(grid_id) / "param_search" / "summary.csv"
    df = pd.read_csv(summary_path)
    best = df.sort_values("f1", ascending=False).iloc[0]
    return {
        "chip_size": int(best["chip_size"]),
        "overlap": float(best["overlap"]),
        "min_object_area": float(best["min_object_area"]),
    }


def main():
    args = parse_args()

    params = {
        "chip_size": args.chip_size,
        "overlap": args.overlap,
        "min_object_area": args.min_object_area,
        "confidence_threshold": args.confidence_threshold,
        "mask_threshold": args.mask_threshold,
    }

    if args.best_from_summary:
        best = load_best_params(args.best_from_summary)
        params.update(best)
        if args.output_subdir == "baseline_default":
            args.output_subdir = f"generalization_{normalize_grid_id(args.best_from_summary).lower()}_best"

    summary_rows = []
    for grid_id in args.grid_ids:
        gid = normalize_grid_id(grid_id)
        pipeline.main(
            force=args.force,
            grid_id=gid,
            output_subdir=args.output_subdir,
            chip_size=params["chip_size"],
            overlap=params["overlap"],
            min_object_area=params["min_object_area"],
            confidence_threshold=params["confidence_threshold"],
            mask_threshold=params["mask_threshold"],
        )

        pred = pipeline.load_predictions()
        gt = pipeline.load_ground_truth()
        metrics = pipeline.iou_matching(gt, pred, iou_threshold=pipeline.DEFAULT_IOU)
        summary_rows.append({
            "grid_id": gid,
            "output_dir": str(pipeline.OUTPUT_DIR),
            "chip_size": params["chip_size"] if params["chip_size"] is not None else pipeline.CHIP_SIZE[0],
            "overlap": params["overlap"] if params["overlap"] is not None else pipeline.OVERLAP,
            "min_object_area": (
                params["min_object_area"]
                if params["min_object_area"] is not None
                else pipeline.MIN_OBJECT_AREA
            ),
            "tp": metrics["tp"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "precision": round(metrics["precision"], 4),
            "recall": round(metrics["recall"], 4),
            "f1": round(metrics["f1"], 4),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_dir = Path("results") / "multi_grid"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_name = f"{args.output_subdir}_summary.csv"
    summary_path = summary_dir / summary_name
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(summary_df.to_string(index=False))
    print(f"[OK] saved: {summary_path}")


if __name__ == "__main__":
    main()
