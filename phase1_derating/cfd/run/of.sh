#!/usr/bin/env bash
# Run an OpenFOAM command inside the ESI OpenFOAM Docker image with the CFD
# tree mounted at /cfd. Usage: run/of.sh blockMesh   (run from any dir under cfd/)
#
# NOTE: the image ENTRYPOINT cd's to $HOME before running the command, so a
# docker -w flag is ignored. We instead cd to the case dir inside the command.
set -euo pipefail
IMAGE="opencfd/openfoam-default:2406"
CFD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REL="${PWD#"$CFD_ROOT"}"                 # "" at cfd root, "/heater_unitcell" in a subdir
case "$REL" in "$PWD") REL="" ;; esac    # PWD not under CFD_ROOT -> treat as cfd root
docker run --rm -v "${CFD_ROOT}:/cfd" "${IMAGE}" \
  bash -lc "cd \"/cfd${REL}\" && { source /openfoam/bash.rc 2>/dev/null || true; }; $*"
