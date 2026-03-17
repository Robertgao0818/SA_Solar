# Annotation Specification — Installation Footprint

**Version**: 1.0 (V1.2)
**Effective date**: 2026-03-17
**Label definition**: `installation_footprint`

## Scope

This specification defines the annotation standard for the Cape Town solar detection project from V1.2 onwards. All new annotations and all evaluation must conform to this spec. Historical annotations are retroactively classified under this spec with quality tiers.

## Definition

One annotation polygon represents the **footprint of one solar installation on a single roof**.

- An "installation" is a set of solar panels that form a single, physically connected or near-connected array on one roof surface.
- The polygon boundary traces the **outer envelope of the installation**, not individual panel boundaries.
- Minor gaps between panels within the same installation (e.g., mounting rail spacing) are enclosed within the polygon.

## Rules

### Merge Rule
- Panels on the **same roof** that are physically connected or clearly part of the **same system** (contiguous cluster) → **merge into one polygon**.
- Panels on the **same roof** but belonging to **physically separate systems** (e.g., different roof faces, clear gap > ~1m) → **separate polygons**.

### Boundary Rule
- The polygon should trace the installation footprint as tightly as practical.
- Do NOT trace individual panel outlines — one polygon per installation.
- Do NOT extend the polygon to cover the entire roof or building footprint.
- Small overhangs or shading structures that obscure panel boundaries: use best visual estimate.

### Edge Cases
- **Ground-mounted panels**: Annotate if visible and within the grid extent. Same merge/boundary rules apply.
- **Solar water heaters**: Do NOT annotate. Only photovoltaic installations are in scope.
- **Partially obscured by trees**: Annotate the visible portion. If >50% obscured, skip.
- **Under construction / partially installed**: Annotate what is visibly present.

## Quality Tiers

| Tier | Description | Use |
|------|-------------|-----|
| **T1** | Reviewed against this spec. Boundary follows installation footprint rules. Geometric accuracy sufficient for IoU >= 0.3 matching. | Validation set; all evaluation conclusions. |
| **T2** | Original weak-supervision annotation. Not reviewed against this spec. May have: area too large, wrong merge, geometric offset, or ambiguous boundaries. | Training set (combined with T1). |

### Tier Assignment
- All existing annotations start as **T2**.
- Annotations are upgraded to **T1** after manual review in QGIS against the aerial/satellite imagery, confirming they meet this spec.
- The annotation manifest (`annotation_manifest.csv`) tracks each annotation's tier.

## Historical Correction Policy

Existing annotations are NOT redrawn wholesale. Only fix these **three error types**:

1. **Area too large**: Polygon covers significant non-panel area (e.g., entire roof instead of just the installation).
2. **Wrong merge**: Two physically separate installations incorrectly merged into one polygon.
3. **Severe geometric offset**: Polygon position is shifted such that true IoU with the actual installation < 0.3.

All other imprecisions (slightly loose boundary, minor shape deviations) are accepted under T2 tier.

## Coordinate System

- Source annotations: EPSG:4326 (WGS84)
- Evaluation CRS: EPSG:32734 (UTM 34S) for Cape Town grids
- All area calculations use the metric CRS.

## Category Naming

- New exports and documentation use `solar_installation`.
- Legacy COCO datasets and old checkpoints retain `solar_panel` (category_id=1 is unchanged).
- Both names map to the same model class; the category name is cosmetic.
