#!/usr/bin/env bash
# Run an OpenFOAM command inside the ESI OpenFOAM Docker image with the CFD
# tree mounted. Usage: run/of.sh blockMesh   (run from any dir under cfd/)
set -euo pipefail
IMAGE="opencfd/openfoam-default:2406"
CFD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker run --rm -v "${CFD_ROOT}:/cfd" -w "/cfd/${PWD##*/cfd/}" "${IMAGE}" \
  bash -lc "source /openfoam/bash.rc 2>/dev/null || true; $*"
