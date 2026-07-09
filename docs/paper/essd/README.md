# ESSD Data Descriptor — draft workspace

**Status**: v0 draft in progress (2026-07-06). NOT committed; location `docs/paper/essd/`
is the handoff suggestion — confirm with owner before first commit (and update
`docs/architecture.md` in the same commit per repo doc-sync rules).

**Master reference**: `docs/plans/2026-07-06-storyline-tech-plan-v2.md` (draft v3).
Handoff: `/tmp/handoff_essd_draft_2026-07-06.md`.

## Scope decisions (as drafted)

1. **Census-only** (Cape Town + Johannesburg detection inventories). The JHB temporal
   panel is NOT included; §7 keeps an extension slot for it as an ESSD living-data
   update. Rationale: census-only depends on no unclosed gate (plan doc §4);
   the P0 chain (displacement audit → Panel v2 → ISSUE-11) gates every temporal claim.
2. **No event-study commitment anywhere.** Load-shedding appears in the introduction
   as motivation only (plan doc §4 risk register, last row).
3. **JHB install-date columns are withheld from the v1 data release** (not just empty):
   the JHB economic table has dates, but no independent accuracy claim is allowed
   before Panel v2 + ISSUE-11 (claim-gate table, plan doc §4). CT date block ships
   empty with `undated_reason=ct_backdating_pending` — as the schema contract says.
   ← OWNER DECISION: confirm withhold-vs-ship-with-caveat for JHB dates.

## Evidence discipline

Every number in the draft carries its caliber inline (analysis unit, IoU/matching,
merge-mode, GT tier) and a source path in an HTML comment. Claims are graded
`[F]` (file/number-backed, path attached) / `[H]` (must verify before submission)
per memory `verdict_evidence_grading`. Cross-caliber comparisons are forbidden —
including comparisons against curated-benchmark literature numbers (Dice 0.998-class);
the GT-ceiling decomposition replaces them.

## Files

- `essd_draft_v0.md` — the manuscript draft (English).
- `research_verification_memo_2026-07-06.md` — deep-research results for the five
  pre-submission [H] clusters (global product positioning, Vexcel license,
  Overture/GOB lineage, ESSD mechanics, load-shedding/SARS series). Written from
  workflow `wf_51286802-2e8` output.

## Known blocking items (tracked in draft as PENDING blocks)

- **Vexcel derived-vector license**: the public September 2024 Vexcel EULA defines
  Derivatives as extracted features/attributes and licenses them for *Internal Use
  only*; "Commercial Purpose" explicitly includes "use in any books, news
  publication, or journal", and Derivatives must be destroyed on termination
  (§2.1(c), §2.2(c), definitions). Under that baseline, publishing JHB polygons
  CC-BY is **not permitted** — the actual Customer Agreement terms must be checked
  and/or written permission obtained from Vexcel before submission. CT (municipal
  WMS) is unaffected.
- ESSD requires the dataset deposited with DOI before/at submission — Zenodo record
  must exist first (verify exact requirement in research memo).
