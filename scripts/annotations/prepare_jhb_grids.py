#!/usr/bin/env python3
"""Prepare Johannesburg 6-grid inputs for the existing detection pipeline."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from shapely import force_2d
from shapely.geometry import box


PROJECT_ROOT = Path(__file__).resolve().parents[1]
JHB_DIR = PROJECT_ROOT / "johnberg"
ANNOTATION_SOURCE = JHB_DIR / "JHB.gpkg"
SOURCE_GRID_TIFS = sorted(JHB_DIR.glob("JHB-*_solar.tif"))
OFFICIAL_AERIAL_DIR = JHB_DIR / "official_aerial_2023_fullres"
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"
TASK_GRID_PATH = PROJECT_ROOT / "data" / "jhb_task_grid.gpkg"
TILES_ROOT = PROJECT_ROOT / "tiles"
SUMMARY_PATH = JHB_DIR / "jhb_grid_summary.csv"

GRID_LAYOUT = [
    ["JHB01", "JHB02", "JHB03"],
    ["JHB04", "JHB05", "JHB06"],
]


def build_grid_gdf() -> gpd.GeoDataFrame:
    records = []
    for tif_path in SOURCE_GRID_TIFS:
        grid_id = tif_path.stem.split("_")[0].replace("-", "")
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
        geom = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        records.append(
            {
                "gridcell_id": grid_id,
                "Name": grid_id,
                "lon": geom.centroid.x,
                "lat": geom.centroid.y,
                "geometry": geom,
            }
        )
    return gpd.GeoDataFrame(records, crs="EPSG:4326").sort_values("gridcell_id").reset_index(drop=True)


def split_annotations(grids: gpd.GeoDataFrame) -> pd.DataFrame:
    annotations = gpd.read_file(ANNOTATION_SOURCE).copy()
    annotations["geometry"] = annotations.geometry.map(force_2d)

    ann_metric = annotations.to_crs("EPSG:3857").copy()
    ann_metric["centroid_geom"] = ann_metric.geometry.centroid
    centroids = ann_metric.set_geometry("centroid_geom")
    grids_metric = grids.to_crs("EPSG:3857")

    joined = gpd.sjoin(
        centroids,
        grids_metric[["gridcell_id", "geometry"]],
        predicate="within",
        how="left",
    )
    if joined["gridcell_id"].isna().any():
        missing = int(joined["gridcell_id"].isna().sum())
        raise RuntimeError(f"{missing} annotation(s) could not be assigned to a JHB grid")

    annotations["grid_id"] = joined["gridcell_id"].values

    rows = []
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    for grid_id, subset in annotations.groupby("grid_id"):
        out = subset.copy().reset_index(drop=True)
        out["panel_id"] = range(1, len(out) + 1)
        out["id"] = out["panel_id"]
        out = out[["grid_id", "panel_id", "id", "geometry"]]
        out_path = ANNOTATIONS_DIR / f"{grid_id}.gpkg"
        if out_path.exists():
            out_path.unlink()
        out.to_file(out_path, driver="GPKG")
        rows.append({"grid_id": grid_id, "annotation_count": len(out)})

    return pd.DataFrame(rows).sort_values("grid_id").reset_index(drop=True)


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def prepare_tiles() -> pd.DataFrame:
    rows = []
    for tif_path in sorted(OFFICIAL_AERIAL_DIR.glob("*.tif")):
        if "_mosaic" in tif_path.stem:
            continue
        stem = tif_path.stem
        row_idx = int(stem.split("_r")[1].split("_c")[0]) - 1
        col_idx = int(stem.split("_c")[1]) - 1

        grid_row = row_idx // 3
        grid_col = col_idx // 3
        local_row = row_idx % 3
        local_col = col_idx % 3
        grid_id = GRID_LAYOUT[grid_row][grid_col]

        dst = TILES_ROOT / grid_id / f"{grid_id}_{local_col}_{local_row}_geo.tif"
        link_or_copy(tif_path, dst)
        rows.append(
            {
                "grid_id": grid_id,
                "source_tile": tif_path.name,
                "linked_tile": dst.name,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    grids = build_grid_gdf()
    TASK_GRID_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TASK_GRID_PATH.exists():
        TASK_GRID_PATH.unlink()
    grids.to_file(TASK_GRID_PATH, driver="GPKG")

    ann_summary = split_annotations(grids)
    tile_summary = prepare_tiles()
    tile_counts = tile_summary.groupby("grid_id").size().rename("tile_count").reset_index()
    summary = ann_summary.merge(tile_counts, on="grid_id", how="outer").fillna(0)
    summary = summary.sort_values("grid_id").reset_index(drop=True)
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")

    print(summary.to_string(index=False))
    print(f"\nWrote {TASK_GRID_PATH}")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
