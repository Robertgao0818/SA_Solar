"""Unit tests for sam_refine_maskbox.build_refined_row.

The SAM model cannot run in-process, so the out_row construction is factored
into a pure function and tested directly: a source row carrying a stale
(pre-SAM) area_m2 must yield an output row whose area_m2 equals the REFINED
polygon's area, with orig_area_m2/sam_area_m2 recording provenance.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from core.postproc import compute_geometric_properties
from scripts.analysis.sam_refine_maskbox import build_refined_row


def _source_row():
    # Pre-SAM geometry 20x20 (area 400); area_m2 copied from finalize.py.
    return pd.Series({
        "geometry": box(0, 0, 20, 20),
        "confidence": 0.93,
        "score": 0.93,
        "area_m2": 400.0,
        "elongation": 1.0,
        "solidity": 1.0,
    })


def test_area_m2_follows_refined_geometry():
    src = _source_row()
    refined = box(0, 0, 18, 18)  # SAM tightens: area 324, not the pre-SAM 400
    out = build_refined_row(
        src, src.index, refined,
        orig_area_m2=src["geometry"].area,
        sam_score=0.77, sam_mask_idx=1,
    )
    assert out["area_m2"] == refined.area == 324.0
    assert out["area_m2"] != src["area_m2"]
    assert out["geometry"] is refined


def test_provenance_and_copied_attributes():
    src = _source_row()
    refined = box(0, 0, 18, 18)
    out = build_refined_row(
        src, src.index, refined,
        orig_area_m2=src["geometry"].area,
        sam_score=0.77, sam_mask_idx=2,
    )
    assert out["orig_area_m2"] == 400.0       # pre-SAM area
    assert out["sam_area_m2"] == refined.area  # refined area
    assert out["sam_score"] == 0.77
    assert out["sam_mask_idx"] == 2
    assert out["confidence"] == 0.93           # copied attribute preserved
    assert "geometry" in out


def test_grid_recompute_fixes_all_geometry_derived_columns():
    """run_one_grid wraps build_refined_row outputs in a GeoDataFrame and runs
    compute_geometric_properties; that recompute must overwrite the stale
    pre-SAM elongation/solidity (not just area_m2) with the refined polygon's
    values."""
    src = _source_row()          # square pre-SAM: elongation 1.0, solidity 1.0
    refined = box(0, 0, 40, 4)   # elongated 10:1 sliver
    row = build_refined_row(
        src, src.index, refined,
        orig_area_m2=src["geometry"].area,
        sam_score=0.5, sam_mask_idx=0,
    )
    gdf = gpd.GeoDataFrame([row], crs="EPSG:32735")
    gdf = compute_geometric_properties(gdf)
    r = gdf.iloc[0]
    assert r["area_m2"] == refined.area == 160.0
    assert abs(r["elongation"] - 10.0) < 1e-6   # was copied as 1.0 pre-SAM
    assert abs(r["solidity"] - 1.0) < 1e-6      # convex sliver

