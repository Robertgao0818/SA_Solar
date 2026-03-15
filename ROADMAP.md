# Roadmap — Cape Town Solar Panel Detection

## V0: Baseline Detection Pipeline — DONE

Stock geoai `SolarPanelDetector` (Mask R-CNN ResNet50-FPN) + post-processing.

### Completed
- [x] Detection pipeline (`detect_and_evaluate.py`): geoai → mask → vectorize → filter → evaluate
- [x] Building footprint filter (`building_filter.py`): OSM + Microsoft buildings
- [x] Tile pipeline (`tiles/build_vrt.py`): WMS download → GeoTIFF → VRT mosaic
- [x] Multi-threshold IoU evaluation (0.1–0.7), merge-matching and strict modes
- [x] Size-stratified recall analysis (<10m², 10–50m², 50–100m², >100m²)
- [x] Per-tile evaluation, error analysis (FP/FN classification), confidence histograms
- [x] Parameter tuning: chip_size=400, overlap=0.25, conf=0.3, post_conf=0.70

### Baseline Numbers (stock weights)
| Grid | Precision | Recall | F1 | Notes |
|------|-----------|--------|----|-------|
| G1238 | 0.62 | 0.66 | 0.64 | Best grid, 124 annotations |
| G1189 | — | 0.33 | — | Low recall |
| G1190 | — | 0.39 | — | Low recall |
| JHB01–06 | — | 0.28 (macro) | — | Cross-city transfer |

### Known Issues
- Low recall on G1189/G1190
- Large arrays (>100m²) match at low IoU — mask quality insufficient
- JHB generalization poor with stock weights

---

## V1: Cape Town Fine-Tune — IN PROGRESS

Fine-tune Mask R-CNN on 257 Cape Town annotations across 3 grids.

### Completed
- [x] `export_coco_dataset.py`: annotation → COCO exporter with 400×400 chips, tile-level 80/20 split, 1:1 pos:neg balancing
- [x] `train.py`: 2-stage training (heads-only 3 epochs → full fine-tune 20 epochs), cosine LR, augmentations (flip/rotate/color jitter/scale)
- [x] `detect_and_evaluate.py --model-path`: CLI integration for custom weights
- [x] Smoke test: annotation loading, tile splitting, chip extraction logic verified

### TODO
- [ ] Export COCO dataset: `python export_coco_dataset.py`
- [ ] Record baseline snapshot: run stock weights on exact val split → P/R/F1 per grid
- [ ] Train on CUDA machine: `python train.py --coco-dir data/coco`
- [ ] Acceptance: Cape Town val F1 ≥ baseline + 0.08
- [ ] Post-training calibration sweep (confidence, mask, post_conf thresholds)
- [ ] Freeze best parameter set as v1 inference bundle
- [ ] Leave-one-grid-out cross-validation
- [ ] JHB transfer evaluation (reporting only, baseline macro recall = 0.281)
- [ ] Size-stratified recall diagnostics (IoU 0.1/0.3/0.5, focus >100m²)

### Training Data
- G1238: 123 valid polygons (layer `g1238__solar_panel__cape_town_g1238_`)
- G1189: 58 polygons (from combined GPKG, Name prefix filter)
- G1190: 76 polygons (from combined GPKG, Name prefix filter)
- Total: 257 polygons across 126 source tiles (42 per grid)
- Split: ~80% train / ~20% val per grid, tile-level, no tile overlap

### Training Config
- Architecture: `maskrcnn_resnet50_fpn`, num_classes=2, init from geoai weights
- Stage 1: heads-only, 3 epochs, LR=1e-3
- Stage 2: full, ≤20 epochs, LR=1e-4, cosine decay
- SGD momentum=0.9, weight_decay=1e-4, batch_size=4
- Augmentations: flip H/V, 90°/180°/270° rotation, color jitter, 0.8–1.2× scale
- Checkpoint: best val `segm_AP50`

---

## V2: Future Directions (not started)

- [ ] Include additional Cape Town grids (G0854, G0855, G0910, etc.) if tiles downloaded
- [ ] JHB annotations + fine-tuning for cross-city generalization
- [ ] 2025 satellite imagery evaluation
- [ ] Stronger backbone (Swin Transformer) if large-array IoU still stalls
- [ ] Active learning: prioritize annotation on high-uncertainty tiles
