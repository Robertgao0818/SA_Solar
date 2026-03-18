#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

git config core.hooksPath .githooks
echo "[hooks] core.hooksPath -> .githooks"
echo "[hooks] post-commit progress hook enabled"
