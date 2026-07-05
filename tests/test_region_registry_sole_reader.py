"""Guard: core.region_registry is the SOLE reader of regions.yaml.

ADR-0001 step 5 (2026-06-12) sealed configs/datasets/regions.yaml behind
core.region_registry as the only sanctioned read path. This defect class then
regressed twice — a CPT task-grid builder yaml.safe_loaded the file and hand-dug
coverage_grids, and a JHB eval shell script grepped it by indentation (issue #5,
defect ④). Both were routed back through the registry; this test freezes that so
a third recurrence fails CI instead of the acceptance criterion's one-time
manual sweep silently rotting.

It sweeps every *.py / *.sh file in the repo for the two concrete patterns that
actually caused the regressions:

  (a) Python — a quoted string-literal token joining `regions` + `.yaml`
      (catches `Path(...) / "configs" / "datasets" / "<that file>"`-style path
      construction). Prose mentions in docstrings / help text / error messages
      use the bareword, not a quoted token, so they do not false-positive.
  (b) Shell — a read tool (grep/sed/awk/cat/head/tail/jq) or a `<` redirection
      applied on a non-comment line that also names regions.yaml. Plain `#`
      comments and echo/message strings that merely mention the path are not
      reads and are not flagged.

Allowlist = exactly two files:
  - core/region_registry.py — the sealed sole read path.
  - scripts/validate_registry.py — a pre-existing, deliberate exception from the
    original seal scope: a config cross-reference linter that must inspect the
    RAW yaml structure to validate the registry itself (chicken-and-egg). It is
    out of issue #5's scope; do NOT "fix" it into a registry client without
    reading why it reads raw.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Built by concatenation so this guard file itself carries no quoted literal
# token that pattern (a) would flag when it sweeps its own source.
_TARGET = "regions" + ".yaml"

# (a) The bare filename token closed by a quote and opened by either a quote (the
#     segmented  Path(...) / "datasets" / "<file>"  construction) OR a `/` (the
#     joined single-string  "configs/datasets/<file>"  construction — the most
#     idiomatic back-channel reintroduction, which a quote-only left anchor would
#     miss). This comment writes the target as <file>, never the literal, so the
#     sweep does not flag its own documentation.
_PY_QUOTED = re.compile(r"""(?:['"]|/)""" + re.escape(_TARGET) + r"""['"]""")

# (b) A shell read tool (incl. yq) or an input redirection into the file.
_SH_READ = re.compile(
    r"\b(?:grep|sed|awk|cat|head|tail|jq|yq)\b|<\s*\S*" + re.escape(_TARGET)
)

# Repo-relative POSIX paths permitted to read the raw yaml (see module docstring).
ALLOWLIST = {
    "core/region_registry.py",
    "scripts/validate_registry.py",
}

# Directories never worth sweeping (vendored / generated / VCS internals).
# Generated / vendored / scratch trees — not the sanctioned source this guard
# seals. `.tmp` and `.cache` are gitignored scratch (untracked one-off scripts
# live there and may open the raw yaml; they are never committed source).
_PRUNE_DIRS = {
    ".venv", ".git", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache",
    ".tmp", ".cache",
}


def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            if name.endswith((".py", ".sh")):
                files.append(Path(dirpath) / name)
    return files


def _find_back_channels() -> list[str]:
    offenders: list[str] = []
    for path in _iter_source_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        is_shell = path.suffix == ".sh"
        for lineno, line in enumerate(text.splitlines(), start=1):
            if is_shell:
                if line.lstrip().startswith("#"):
                    continue
                if _TARGET in line and _SH_READ.search(line):
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
            else:  # Python
                if _PY_QUOTED.search(line):
                    offenders.append(f"{rel}:{lineno}: {line.strip()}")
    return offenders


def test_no_raw_regions_yaml_back_channel():
    offenders = _find_back_channels()
    assert not offenders, (
        "Direct regions.yaml reader(s) found outside core.region_registry "
        "(ADR-0001 step 5 seal). Route these through core.region_registry "
        "instead of parsing/grepping the raw file:\n  "
        + "\n  ".join(offenders)
    )


def test_allowlisted_files_still_exist():
    # If an allowlisted path is renamed/removed the allowlist is stale — surface
    # it rather than let a dangling entry silently permit a new offender.
    for rel in ALLOWLIST:
        assert (REPO_ROOT / rel).exists(), f"allowlisted path missing: {rel}"
