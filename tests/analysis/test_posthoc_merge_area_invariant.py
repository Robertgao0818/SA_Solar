"""Unit tests for the post-hoc merge scripts' merge_overlapping.

Guards the invariant that every output row's area_m2 equals its geometry's
area — both for singleton clusters (whose attributes pass through untouched
and may carry a stale upstream area_m2) and for merged multi-member clusters
(whose geometry is the union of the members). Both near-duplicate
implementations (posthoc_merge_and_spatial_eval, posthoc_merge_areaf1) are
covered until they are consolidated into a shared helper.
"""
from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

from scripts.analysis.posthoc_merge_and_spatial_eval import (
    merge_overlapping as merge_spatial_eval,
)
from scripts.analysis.posthoc_merge_areaf1 import (
    merge_overlapping as merge_areaf1,
)

CRS = "EPSG:32735"

MERGE_FNS = [merge_spatial_eval, merge_areaf1]
MERGE_IDS = ["spatial_eval", "areaf1"]


def _gdf(records):
    return gpd.GeoDataFrame(records, geometry="geometry", crs=CRS)


@pytest.mark.parametrize("merge_overlapping", MERGE_FNS, ids=MERGE_IDS)
def test_singleton_stale_area_is_corrected(merge_overlapping):
    """An isolated polygon carrying a wrong area_m2 → output area_m2 equals
    the geometry's true area."""
    gdf = _gdf([
        {"geometry": box(0, 0, 10, 10), "confidence": 0.9, "area_m2": 999.0},
    ])
    out = merge_overlapping(gdf, iou_thresh=0.1, score_col="confidence")
    assert len(out) == 1
    assert out.iloc[0]["area_m2"] == out.iloc[0].geometry.area == 100.0


@pytest.mark.parametrize("merge_overlapping", MERGE_FNS, ids=MERGE_IDS)
def test_two_member_cluster_area_equals_union(merge_overlapping):
    """Two overlapping polygons merge into their union; area_m2 equals the
    union's area."""
    gdf = _gdf([
        {"geometry": box(0, 0, 10, 10), "confidence": 0.9, "area_m2": 999.0},
        {"geometry": box(5, 0, 15, 10), "confidence": 0.8, "area_m2": 999.0},
    ])
    out = merge_overlapping(gdf, iou_thresh=0.1, score_col="confidence")
    assert len(out) == 1
    row = out.iloc[0]
    assert row["n_merged"] == 2
    assert row.geometry.area == 150.0          # union box(0,0,15,10)
    assert row["area_m2"] == row.geometry.area


@pytest.mark.parametrize("merge_overlapping", MERGE_FNS, ids=MERGE_IDS)
def test_invariant_holds_across_mixed_clusters(merge_overlapping):
    """A merged pair alongside an isolated singleton with a stale area_m2:
    every output row satisfies area_m2 == geometry.area."""
    gdf = _gdf([
        {"geometry": box(0, 0, 10, 10), "confidence": 0.9, "area_m2": 999.0},
        {"geometry": box(5, 0, 15, 10), "confidence": 0.8, "area_m2": 999.0},
        {"geometry": box(100, 100, 110, 110), "confidence": 0.7, "area_m2": 777.0},
    ])
    out = merge_overlapping(gdf, iou_thresh=0.1, score_col="confidence")
    assert len(out) == 2
    for _, row in out.iterrows():
        assert abs(row["area_m2"] - row.geometry.area) < 1e-6
    # The isolated singleton keeps its own true area, not the stale 777.
    singleton = out[out.geometry.area == 100.0]
    assert len(singleton) == 1
    assert singleton.iloc[0]["area_m2"] == 100.0
