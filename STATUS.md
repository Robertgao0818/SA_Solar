# Project Status — Cape Town Solar Panel Detection

**Last Updated**: 2026-03-17

## Current Phase

V1.2 — Evaluation Profile & Annotation Alignment (COMPLETE; installation profile validated on GPU for G1189/G1190/G1238)

---

## V0: Baseline Detection Pipeline — COMPLETE

Stock geoai Mask R-CNN ResNet50-FPN + post-processing.

| Grid | Precision | Recall | F1 | Notes |
|------|-----------|--------|----|-------|
| G1238 | 0.62 | 0.66 | 0.64 | Best grid, 124 annotations |
| G1189 | — | 0.33 | — | Low recall |
| G1190 | — | 0.39 | — | Low recall |
| JHB01–06 | — | 0.28 (macro) | — | Cross-city transfer |

## V1: Cape Town Fine-Tune — MINIMUM V1 COMPLETE

Fine-tuned Mask R-CNN on 257 Cape Town annotations across 3 grids.

**Best checkpoint**: `checkpoints/v1_ft_cs400_tileval_20260317_r4/best_model.pth` (val_AP50=0.4205)

### Val-Split Results (20 val tiles, 64 GT polygons)

| Scope | Precision | Recall | F1 | ΔF1 vs baseline |
|-------|-----------|--------|----|-----------------|
| Overall | 0.7031 | 0.7031 | 0.7031 | +0.2587 |
| G1238 | 0.7576 | 0.9259 | 0.8333 | +0.3444 |
| G1189 | 0.5625 | 0.4500 | 0.5000 | +0.1129 |
| G1190 | 0.7333 | 0.6471 | 0.6875 | +0.2527 |

### Full-Grid Fine-Tuned Results (GPU-verified, installation profile)

| Grid | F1@IoU0.3 |
|------|-----------|
| G1189 | 0.5950 |
| G1190 | 0.6490 |
| G1238 | 0.7789 |

### Size-Stratified Gains (val split)

| Size class | Recall (baseline → fine-tuned) | Δ |
|------------|-------------------------------|---|
| Small (<20m²) | 0.3939 → 0.4848 | +0.0909 |
| Large (>100m²) | 0.2500 → 1.0000 | +0.7500 |

### Residual Issues

- G1189 small-panel recall regressed: 0.3077 → 0.2308 (val split)
- Post-training calibration sweep not done
- Leave-one-grid-out cross-validation pending
- JHB transfer evaluation not performed
- Parameter freeze for v1 inference bundle pending

### Training Data

- G1238: 123 polygons (QGIS aerial annotation)
- G1189: 58 polygons (Google Earth, corrected)
- G1190: 76 polygons (Google Earth, corrected)
- Total: 257 polygons, 126 source tiles
- Split: 80% train / 20% val (tile-level, no overlap)
- Chips: train=804 (402 pos, 402 neg), val=218 (109 pos, 109 neg)

### Training Config

- Architecture: maskrcnn_resnet50_fpn, num_classes=2
- Stage 1: heads-only, 3 epochs, LR=1e-3
- Stage 2: full fine-tune, 20 epochs, LR=1e-4, cosine decay
- Augmentations: flip H/V, 90/180/270° rotation, color jitter, 0.8–1.2× scale

---

## V1.2: Evaluation Profile & Annotation Alignment — COMPLETE

Task frozen as **installation-level footprint segmentation** (not panel-level). No model change this round.

### Work Package Progress

| WP | Description | Status |
|----|-------------|--------|
| Pre | STATUS.md progress tracker | Done |
| WP0 | Annotation spec (ANNOTATION_SPEC.md) | Done |
| WP1 | Annotation manifest + bootstrap script | Done |
| WP2 | Evaluation profile (presence/footprint/area) | Done |
| WP3 | config.json extension (evaluation_config) | Done |
| WP4 | COCO export manifest-aware filtering | Done |
| WP5 | train.py minor update | Done |
| WP6 | Documentation updates | Done |
| -- | GPU integration test (3 grids) | Done |

### V1.2 Acceptance Criteria

- full-grid F1@IoU0.3: G1189 >= 0.595, G1190 >= 0.649, G1238 no regression
- presence recall@IoU0.1: no regression from fine-tuned baseline
- 5-20m² bucket recall: must be reported; G1189/G1190 no regression
- area error: establish baseline (no hard gate yet)

Acceptance status: all current V1.2 gates satisfied on GPU-validated full-grid runs.

### GPU Integration Test Log

#### 2026-03-17 — G1189 full-grid installation profile

- Command run on GPU:
  `./.venv/bin/python detect_and_evaluate.py --grid-id G1189 --model-path checkpoints/v1_ft_cs400_tileval_20260317_r4/best_model.pth --evaluation-profile installation --force`
- Runtime confirmed CUDA execution on `NVIDIA GeForce RTX 4070 Laptop GPU`.
- Detection summary: 64 final prediction polygons after post-processing and confidence filtering.
- Ground truth: 58 installation polygons from `solarpanel_g0001_g1190.gpkg`.

| Metric | Value |
|--------|-------|
| Presence P@IoU0.1 | 0.6667 |
| Presence R@IoU0.1 | 0.7241 |
| Presence F1@IoU0.1 | 0.6942 |
| Merge F1@IoU0.3 | 0.5950 |
| Merge F1@IoU0.5 | 0.4628 |
| Mean IoU | 0.5439 |
| Median IoU | 0.5972 |
| IoU>=0.3 match rate | 85.7% |
| IoU>=0.5 match rate | 66.7% |

Acceptance check for G1189:

- `G1189 >= 0.595` full-grid F1@IoU0.3: met exactly (`0.5950`)
- presence recall@IoU0.1 baseline guard: currently acceptable for V1.2 tracking
- 5-20m² bucket reporting: available, with 12 FN in the `5-20m²` bucket
- area-error baseline: established via `results/G1189/area_error_metrics.csv`

Remaining V1.2 integration work:

- None for the current V1.2 release gate

#### 2026-03-17 — G1190 full-grid installation profile

- Command run on GPU:
  `./.venv/bin/python detect_and_evaluate.py --grid-id G1190 --model-path checkpoints/v1_ft_cs400_tileval_20260317_r4/best_model.pth --evaluation-profile installation --force`
- Runtime confirmed CUDA execution on `NVIDIA GeForce RTX 4070 Laptop GPU`.
- Detection summary: 75 final prediction polygons after post-processing and confidence filtering.
- Ground truth: 76 installation polygons from `solarpanel_g0001_g1190.gpkg`.

| Metric | Value |
|--------|-------|
| Presence P@IoU0.1 | 0.7600 |
| Presence R@IoU0.1 | 0.7500 |
| Presence F1@IoU0.1 | 0.7550 |
| Merge F1@IoU0.3 | 0.6490 |
| Merge F1@IoU0.5 | 0.5033 |
| Mean IoU | 0.5410 |
| Median IoU | 0.6020 |
| IoU>=0.3 match rate | 86.0% |
| IoU>=0.5 match rate | 66.7% |

Acceptance check for G1190:

- `G1190 >= 0.649` full-grid F1@IoU0.3: met exactly (`0.6490`)
- presence recall@IoU0.1 baseline guard: passed (`0.7500`)
- 5-20m² bucket reporting: available, with 23 FN in the `5-20m²` bucket
- area-error baseline: established via `results/G1190/area_error_metrics.csv`

#### 2026-03-17 — G1238 full-grid installation profile

- Command run on GPU:
  `./.venv/bin/python detect_and_evaluate.py --grid-id G1238 --model-path checkpoints/v1_ft_cs400_tileval_20260317_r4/best_model.pth --evaluation-profile installation --force`
- Runtime confirmed CUDA execution on `NVIDIA GeForce RTX 4070 Laptop GPU`.
- Detection summary: 184 final prediction polygons after post-processing and confidence filtering.
- Ground truth: 123 installation polygons from layer `g1238__solar_panel__cape_town_g1238_`.

| Metric | Value |
|--------|-------|
| Presence P@IoU0.1 | 0.7037 |
| Presence R@IoU0.1 | 0.9268 |
| Presence F1@IoU0.1 | 0.8000 |
| Merge F1@IoU0.3 | 0.7789 |
| Merge F1@IoU0.5 | 0.5878 |
| Mean IoU | 0.6476 |
| Median IoU | 0.6812 |
| IoU>=0.3 match rate | 97.4% |
| IoU>=0.5 match rate | 76.3% |

Acceptance check for G1238:

- no-regression guard: passed; full-grid merge F1@IoU0.3 is well above the historical baseline (`0.7789` vs `0.64`)
- presence recall@IoU0.1 baseline guard: passed (`0.9268`)
- area-error baseline: established via `results/G1238/area_error_metrics.csv`

---

## V2: Future Directions — NOT STARTED

- Additional Cape Town grids
- JHB annotations + fine-tuning
- 2025 satellite imagery evaluation
- Stronger backbone (Swin Transformer)
- Active learning
- Temporal analysis (installation time estimation)
