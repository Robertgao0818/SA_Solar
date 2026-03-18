#!/usr/bin/env python3
"""Create per-grid satellite tiles for Johannesburg from the 2025 mosaic."""

from __future__ import annotations

from pathlib import Path

import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_GRID_DIR = PROJECT_ROOT / "johnberg"
SATELLITE_VRT = SOURCE_GRID_DIR / "official_satellite_2025_fullres" / "jhb_2025_satellite_mosaic.vrt"
OUTPUT_ROOT = PROJECT_ROOT / "tiles_satellite_2025"


def iter_grid_sources():
    for path in sorted(SOURCE_GRID_DIR.glob("JHB-*_solar.tif")):
        grid_id = path.stem.split("_")[0].replace("-", "")
        yield grid_id, path


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(SATELLITE_VRT) as sat_src:
        for grid_id, grid_path in iter_grid_sources():
            with rasterio.open(grid_path) as grid_src:
                bounds4326 = grid_src.bounds
            bounds3857 = transform_bounds("EPSG:4326", sat_src.crs, *bounds4326, densify_pts=21)
            grid_window = from_bounds(*bounds3857, transform=sat_src.transform)
            grid_window = grid_window.round_offsets().round_lengths()

            col_step = grid_window.width / 3.0
            row_step = grid_window.height / 3.0

            grid_out_dir = OUTPUT_ROOT / grid_id
            grid_out_dir.mkdir(parents=True, exist_ok=True)

            for row in range(3):
                row_off = int(round(grid_window.row_off + row * row_step))
                next_row = int(round(grid_window.row_off + (row + 1) * row_step))
                height = next_row - row_off
                for col in range(3):
                    col_off = int(round(grid_window.col_off + col * col_step))
                    next_col = int(round(grid_window.col_off + (col + 1) * col_step))
                    width = next_col - col_off
                    window = rasterio.windows.Window(col_off, row_off, width, height)
                    data = sat_src.read(window=window)
                    transform = sat_src.window_transform(window)
                    profile = sat_src.profile.copy()
                    profile.update(
                        driver="GTiff",
                        width=width,
                        height=height,
                        transform=transform,
                        compress="lzw",
                        tiled=True,
                    )
                    out_path = grid_out_dir / f"{grid_id}_{col}_{row}_geo.tif"
                    with rasterio.open(out_path, "w", **profile) as dst:
                        dst.write(data)
                    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
