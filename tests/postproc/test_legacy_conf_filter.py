"""Regression tests for the legacy post_conf/conf_tiered filter
(originally the 2026-06-10 F1-gap Tier A2 / C11 fix; tier semantics updated by
the 2026-07-05 D5 ruling — see below).

The 2026-06-10 fix made the legacy path (detect_and_evaluate.py geoai path A)
honor ``--postproc-config``: before it, as soon as predictions had an
``area_m2`` column the hardcoded module-level ``CONF_TIERED`` was applied
unconditionally, ``conf_tiered`` could not be injected (unknown key, silently
ignored) and the config's ``post_conf_threshold`` was dead.

**D5 ruling (2026-07-05, ADR-0001):** the tier-iteration semantics of the two
paths are UNIFIED onto **first-match-wins** (``~matched`` — each polygon is
judged only by its highest-``min_area`` tier), the semantics production/census
(``core/postproc._apply_tiered_keep`` via finalize.py) has always used. The
legacy path's earlier ``fall-through`` (``~keep_mask`` — a polygon failing a
high tier could be rescued by a lower tier) is retired. Only the band
area>=200 m² & conf in [0.65, 0.70) changes (fall-through kept it, first-match
drops it); production inventory is unaffected (already first-match).

These tests pin:

1. the legacy config parser accepts ``conf_tiered``;
2. an injected ``conf_tiered`` actually takes effect (fails pre-2026-06-10);
3. default behavior (no config) is per-polygon identical to the canonical
   first-match oracle;
4. the re-pinned ``configs/postproc/batch003_best_f1.json`` reproduces the
   canonical first-match behavior per polygon (re-pin correctness);
5. the two paths now CONVERGE (D5): the former divergence band
   area>=200 m² & conf in [0.65, 0.70) is dropped by both, and the legacy
   path is byte-identical to ``core/postproc._apply_tiered_keep``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detect_and_evaluate import (  # noqa: E402
    CONF_TIERED,
    apply_conf_filter,
    load_postproc_config,
)
from core.postproc import apply_postproc_filters  # noqa: E402

REPINNED_CONFIG = ROOT / "configs" / "postproc" / "batch003_best_f1.json"


def _gdf(rows):
    geoms = [box(0, 0, 1, 1) for _ in rows]
    return gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:32734")


def _legacy_fallthrough_conf_filter(pred_gdf, tiers):
    """Retired pre-D5 fall-through oracle (``~keep_mask``), kept only to prove
    the D5 divergence band actually moved.

    Source: detect_and_evaluate.py:796-804 @ commit 0b6147e.
    """
    keep_mask = pd.Series(False, index=pred_gdf.index)
    for min_area, thresh in tiers:
        tier_mask = (pred_gdf["area_m2"] >= min_area) & ~keep_mask
        keep_mask |= tier_mask & (pred_gdf["confidence"] >= thresh)
    return pred_gdf[keep_mask].copy()


def _first_match_conf_filter(pred_gdf, tiers):
    """Canonical first-match-wins oracle (post-D5), mirroring
    ``core/postproc._apply_tiered_keep`` (``~matched``)."""
    keep = pd.Series(False, index=pred_gdf.index)
    matched = pd.Series(False, index=pred_gdf.index)
    for min_area, thresh in tiers:
        tier_rows = (pred_gdf["area_m2"] >= min_area) & ~matched
        keep |= tier_rows & (pred_gdf["confidence"] >= thresh)
        matched |= tier_rows
    return pred_gdf[keep].copy()


def _synthetic_frame():
    """Boundary-heavy synthetic predictions covering every tier edge."""
    rng = np.random.default_rng(20260610)
    rows = []
    # Dense boundary cases around tier edges (areas 99/100/101, 199/200/201;
    # confs at 0.649/0.65/0.651, 0.699/0.70/0.701, 0.849/0.85/0.851).
    for area in [1, 5, 50, 99, 100, 101, 150, 199, 200, 201, 500, 2000]:
        for conf in [0.10, 0.649, 0.65, 0.66, 0.699, 0.70, 0.71,
                     0.849, 0.85, 0.851, 0.92, 0.99]:
            rows.append({"area_m2": float(area), "confidence": float(conf)})
    # Random fuzz.
    for _ in range(500):
        rows.append({
            "area_m2": float(rng.uniform(0, 1000)),
            "confidence": float(rng.uniform(0, 1)),
        })
    return _gdf(rows)


def test_load_postproc_config_accepts_conf_tiered(tmp_path):
    cfg = tmp_path / "pp.json"
    cfg.write_text(
        '{"conf_tiered": [[200, 0.7], [100, 0.65], [0, 0.85]],'
        ' "post_conf_threshold": 0.92}',
        encoding="utf-8",
    )
    params = load_postproc_config(cfg)
    assert params["conf_tiered"] == [(200.0, 0.7), (100.0, 0.65), (0.0, 0.85)]
    assert params["post_conf_threshold"] == 0.92


def test_injected_conf_tiered_takes_effect():
    """Pre-fix this fails: no injection point existed; CONF_TIERED always won."""
    gdf = _gdf([
        {"area_m2": 50.0, "confidence": 0.60},   # default tiers: drop (needs 0.85)
        {"area_m2": 50.0, "confidence": 0.90},   # default tiers: keep
    ])
    strict, _ = apply_conf_filter(gdf, conf_tiered=[(0.0, 0.95)])
    assert len(strict) == 0
    loose, _ = apply_conf_filter(gdf, conf_tiered=[(0.0, 0.5)])
    assert len(loose) == 2
    default, _ = apply_conf_filter(gdf)
    assert len(default) == 1


def test_default_behavior_matches_first_match_oracle():
    gdf = _synthetic_frame()
    expected = _first_match_conf_filter(gdf, CONF_TIERED)
    actual, _ = apply_conf_filter(gdf)
    assert list(actual.index) == list(expected.index)


def test_repinned_batch003_reproduces_first_match_behavior_per_polygon():
    """Acceptance check: the re-pinned preset == canonical first-match behavior."""
    params = load_postproc_config(REPINNED_CONFIG)
    assert "conf_tiered" in params, "batch003_best_f1.json must be re-pinned"
    gdf = _synthetic_frame()
    expected = _first_match_conf_filter(gdf, params["conf_tiered"])
    actual, _ = apply_conf_filter(gdf, conf_tiered=params["conf_tiered"])
    assert list(actual.index) == list(expected.index)


def test_conf_tier_unified_to_first_match():
    """D5 ruling (2026-07-05): legacy and direct paths CONVERGE on first-match.

    The former divergence band (area>=200 & conf in [0.65,0.70)) is now dropped
    by BOTH paths; the retired fall-through would have kept it. This pins the
    ruling so a silent regression back to fall-through fails CI.
    """
    row = {"area_m2": 250.0, "confidence": 0.66,
           "elongation": 1.0, "mean_r": 100, "mean_g": 100, "mean_b": 100}
    gdf = _gdf([row])
    # Both canonical paths now drop it (first-match: 250 m² -> tier 0.70, 0.66<0.70).
    legacy_kept, _ = apply_conf_filter(gdf)
    assert len(legacy_kept) == 0, "unified first-match must drop it"
    direct_kept, _ = apply_postproc_filters(gdf, {})
    assert len(direct_kept) == 0, "direct first-match-wins drops it (unchanged)"
    # The retired fall-through is what actually moved (kept it before D5).
    assert len(_legacy_fallthrough_conf_filter(gdf, CONF_TIERED)) == 1


def test_legacy_path_byte_identical_to_core_tiered_keep():
    """D5 dedup-readiness (unblocks #12): the legacy conf filter is now
    per-polygon identical to core/postproc._apply_tiered_keep, so the two tier
    implementations can be collapsed to one."""
    from core.postproc import _apply_tiered_keep

    gdf = _synthetic_frame()
    legacy, _ = apply_conf_filter(gdf)
    core_kept = _apply_tiered_keep(gdf, "confidence", CONF_TIERED, op=">=")
    assert list(legacy.index) == list(core_kept.index)


def test_no_area_column_falls_back_to_post_conf():
    gdf = _gdf([{"confidence": 0.90}, {"confidence": 0.93}])
    out, desc = apply_conf_filter(gdf, conf_tiered=[(0.0, 0.5)],
                                  post_conf_threshold=0.92)
    assert len(out) == 1
    assert "0.92" in desc
