#!/usr/bin/env bash
# Run an OpenFOAM command inside the ESI OpenFOAM Docker image with the CFD
# tree mounted. Usage: run/of.sh blockMesh   (run from any dir under cfd/)
set -euo pipefail
IMAGE="opencfd/openfoam-default:2406"
CFD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REL="${PWD#"$CFD_ROOT"}"          # "" at root, "/heater_unitcell" in a subdir
case "$REL" in "$PWD") REL="" ;; esac   # PWD not under CFD_ROOT -> treat as root
docker run --rm -v "${CFD_ROOT}:/cfd" -w "/cfd${REL}" "${IMAGE}" \
  bash -lc "source /openfoam/bash.rc 2>/dev/null || true; $*"
