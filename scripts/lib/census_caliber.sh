#!/usr/bin/env bash
# census_caliber.sh — single source of truth for the production / census-caliber
# `detect_direct.py -> finalize.py` invocation. Sourced by ct_census_run.sh,
# ct_census_setup.sh and runpod_detect_direct_template.sh so the three launch
# scripts cannot silently drift on detector flags / postproc config / merge-mode.
#
# Census caliber (authority): detect_direct.py -> finalize.py --merge-mode
# per-detection with configs/postproc/v4_canonical.json. See
#   - docs/workflows.md  "Production Census Inference (detect_direct -> finalize)"
#   - docs/evaluation_protocol.md §3 (merge-mode discipline): 2026-06-12 the direct
#     chain MUST state --merge-mode on the CLI and v4_canonical.json carries no
#     merge_mode key (finalize.py raises on CLI-vs-JSON conflict).
# Both merge modes stay first-class (a model-dependent lever) — the red line is a
# SILENT default, not the existence of two modes.
#
# Named diagnostic profile: override any CENSUS_CALIBER_* var explicitly, e.g.
#   CENSUS_CALIBER_MERGE_MODE=pixel-or bash scripts/<launcher>.sh ...
# but NEVER drop --merge-mode / --postproc-config from a finalize call.
#
# Out of scope (throughput / resumability, not caliber): --batch-size,
# --num-workers, --prefetch-factor, --allow-overwrite-canonical — stay per-script.
#
# Idempotent + re-source-safe: every var uses ${VAR:-default} and the arrays are
# rebuilt from the scalars each source, so this can be re-sourced inside an
# `xargs -P ... bash -c` subshell (bash cannot export array variables across that
# fork — the subshell re-sources this to rebuild the arrays from exported scalars).

# Repo root = parent-of-parent of scripts/lib/ (self-locating; callers need not
# pre-agree on a $REPO / $ZAS variable name).
_census_caliber_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CENSUS_CALIBER_REPO_ROOT="${CENSUS_CALIBER_REPO_ROOT:-$(cd "$_census_caliber_lib_dir/../.." && pwd)}"

# ── caliber values (each independently override-able for a named profile) ──────
CENSUS_CALIBER_POSTPROC="${CENSUS_CALIBER_POSTPROC:-$CENSUS_CALIBER_REPO_ROOT/configs/postproc/v4_canonical.json}"
CENSUS_CALIBER_MERGE_MODE="${CENSUS_CALIBER_MERGE_MODE:-per-detection}"
CENSUS_CALIBER_CHIP_SIZE="${CENSUS_CALIBER_CHIP_SIZE:-400}"
CENSUS_CALIBER_OVERLAP="${CENSUS_CALIBER_OVERLAP:-0.25}"
CENSUS_CALIBER_MASK_THRESHOLD="${CENSUS_CALIBER_MASK_THRESHOLD:-0.3}"
CENSUS_CALIBER_DETECTIONS_PER_IMG="${CENSUS_CALIBER_DETECTIONS_PER_IMG:-300}"
CENSUS_CALIBER_SCORE_THRESHOLD="${CENSUS_CALIBER_SCORE_THRESHOLD:-0.05}"
CENSUS_CALIBER_RAW_MASK_STORAGE="${CENSUS_CALIBER_RAW_MASK_STORAGE:-crop}"

# ── convenience arrays for the two engine calls ───────────────────────────────
# Most of these match detect_direct.py's argparse defaults; --detections-per-img
# is the exception — its argparse default is None and the census value 300 is only
# derived downstream in direct mode. That is exactly why every value is passed
# EXPLICITLY here (removing the restatement/drift risk — the point of this fragment);
# do NOT drop the explicit pass on the assumption an argparse default covers it.
CENSUS_CALIBER_DETECT_ARGS=(
  --detections-per-img "$CENSUS_CALIBER_DETECTIONS_PER_IMG"
  --chip-size "$CENSUS_CALIBER_CHIP_SIZE"
  --overlap "$CENSUS_CALIBER_OVERLAP"
  --mask-threshold "$CENSUS_CALIBER_MASK_THRESHOLD"
  --detector-score-threshold "$CENSUS_CALIBER_SCORE_THRESHOLD"
  --raw-mask-storage "$CENSUS_CALIBER_RAW_MASK_STORAGE"
)
CENSUS_CALIBER_FINALIZE_ARGS=(
  --postproc-config "$CENSUS_CALIBER_POSTPROC"
  --merge-mode "$CENSUS_CALIBER_MERGE_MODE"
)
