#!/usr/bin/env bash
# Link gate: fetch the darnlink recipe pinned in darnlink-gate.json, verify its checksum, run it fail-closed.
# Run by the Jenkinsfile. Same wrapper as tools/darnlink_gate.sh in https://github.com/txemi/darnlang (no shared package yet).
set -euo pipefail
cd "$(dirname "$0")/.."
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
ver=$(grep -oE 'darnlink@(v[0-9]+[.][0-9]+[.][0-9]+|[0-9a-f]{40})' darnlink-gate.json | head -1 | cut -d@ -f2)
test -n "$ver" || { echo "ERROR: could not derive the darnlink version from darnlink-gate.json"; exit 1; }
curl -fsSL "https://raw.githubusercontent.com/txemi/darnlink/${ver}/recipes/darnlink-gate" -o "$work/darnlink-gate"
want=$(python3 -c 'import json;print(json.load(open("darnlink-gate.json")).get("recipe_sha256",""))')
if [ -n "$want" ]; then
  got=$(sha256sum "$work/darnlink-gate" | cut -d' ' -f1)
  [ "$got" = "$want" ] || { echo "ERROR: recipe checksum mismatch for ${ver}: expected ${want}, got ${got}"; exit 1; }
else
  echo "WARNING: darnlink-gate.json has no recipe_sha256 - this fetch is UNVERIFIED."
fi
chmod +x "$work/darnlink-gate"
DARNLINK_GATE_FAIL_CLOSED=1 "$work/darnlink-gate"
