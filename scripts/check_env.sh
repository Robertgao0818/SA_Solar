#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "Virtual environment not found at $VENV_PATH"
  echo "Run: ./scripts/bootstrap_env.sh"
  exit 1
fi

export PROJECT_ROOT
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VIRTUAL_ENV/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export XDG_CACHE_HOME="$PROJECT_ROOT/.cache"
export XDG_CONFIG_HOME="$PROJECT_ROOT/.config"
export XDG_DATA_HOME="$PROJECT_ROOT/.local/share"
export MPLCONFIGDIR="$XDG_CACHE_HOME/matplotlib"
export JOBLIB_TEMP_FOLDER="$PROJECT_ROOT/.tmp/joblib"

if [[ -d "/usr/lib/wsl/lib" ]]; then
  export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

mkdir -p \
  "$XDG_CACHE_HOME" \
  "$XDG_CONFIG_HOME" \
  "$XDG_DATA_HOME" \
  "$MPLCONFIGDIR" \
  "$JOBLIB_TEMP_FOLDER"

python - <<'PY'
import importlib
import os
import sys

modules = [
    "geopandas",
    "pandas",
    "shapely",
    "rasterio",
    "rasterstats",
    "matplotlib",
    "seaborn",
    "sklearn",
    "geoai",
    "osmnx",
    "requests",
]

print(f"python={sys.executable}")
print(f"version={sys.version.split()[0]}")
print(f"mplconfigdir={os.environ.get('MPLCONFIGDIR')}")
print(f"joblib_temp={os.environ.get('JOBLIB_TEMP_FOLDER')}")

for name in modules:
    mod = importlib.import_module(name)
    version = getattr(mod, "__version__", "unknown")
    print(f"{name}={version}")
PY
