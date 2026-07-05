"""Shell-layer caliber guard: the three production census launchers must all
source the single source of truth (scripts/lib/census_caliber.sh) instead of
restating detector flags / postproc config / merge-mode as drift-prone literals.

Mirrors tests/analysis/test_benchmark_caliber_guard.py (the Python-side caliber
guard) for the bash launch scripts, which had no such guard. Static text checks
only — no execution (no GPU / tiles in CI).

Issue #4 (defect ②): the RunPod detect_direct template had silently drifted to
`--merge-mode pixel-or`, contradicting the per-detection + v4_canonical census
caliber. This test fails if that literal ever creeps back into a launcher.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
FRAGMENT = BASE_DIR / "scripts" / "lib" / "census_caliber.sh"
LAUNCHERS = [
    BASE_DIR / "scripts" / "runpod_detect_direct_template.sh",
    BASE_DIR / "scripts" / "ct_census_setup.sh",
    BASE_DIR / "scripts" / "ct_census_run.sh",
]

_SOURCE_RE = re.compile(r"source\b.*census_caliber\.sh")


def test_fragment_exists_and_declares_census_caliber():
    assert FRAGMENT.exists(), f"missing single source of truth: {FRAGMENT}"
    text = FRAGMENT.read_text()
    # per-detection is the census-caliber default merge-mode
    assert "CENSUS_CALIBER_MERGE_MODE:-per-detection}" in text, (
        "fragment must default the merge-mode to per-detection"
    )
    # the fragment must cite/point at the canonical postproc config
    assert "v4_canonical.json" in text, (
        "fragment must reference configs/postproc/v4_canonical.json"
    )
    # both convenience arrays must be defined
    assert "CENSUS_CALIBER_DETECT_ARGS=(" in text
    assert "CENSUS_CALIBER_FINALIZE_ARGS=(" in text


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=lambda p: p.name)
def test_launcher_sources_fragment(launcher: Path):
    assert launcher.exists(), f"missing launcher: {launcher}"
    text = launcher.read_text()
    assert _SOURCE_RE.search(text), (
        f"{launcher.name} must `source` scripts/lib/census_caliber.sh instead of "
        "restating caliber flags"
    )


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=lambda p: p.name)
def test_launcher_has_no_silent_pixel_or(launcher: Path):
    """No launcher may hardcode `--merge-mode pixel-or` — that is the exact
    drift issue #4 fixed. A pixel-or diagnostic run must go through an explicit
    CENSUS_CALIBER_MERGE_MODE=pixel-or override, not a baked-in literal."""
    text = launcher.read_text()
    assert "--merge-mode pixel-or" not in text, (
        f"{launcher.name} hardcodes `--merge-mode pixel-or` — the caliber drift "
        "from issue #4 has crept back in; use a CENSUS_CALIBER_MERGE_MODE override"
    )


@pytest.mark.parametrize("launcher", LAUNCHERS, ids=lambda p: p.name)
def test_launcher_finalize_never_silent_default(launcher: Path):
    """Every finalize.py call must state a merge-mode: either the shared
    CENSUS_CALIBER_FINALIZE_ARGS array or an explicit --merge-mode literal.
    A finalize call with neither would rely on finalize.py's silent fallback."""
    text = launcher.read_text()
    if "finalize.py" not in text:
        pytest.skip(f"{launcher.name} makes no finalize.py call")
    assert (
        "CENSUS_CALIBER_FINALIZE_ARGS" in text or "--merge-mode" in text
    ), f"{launcher.name} calls finalize.py without an explicit merge-mode source"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
