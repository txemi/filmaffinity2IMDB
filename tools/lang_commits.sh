#!/usr/bin/env bash
# English-only gate for commit messages.
#
#   lang_commits.sh <base> [<head>]   judge the messages in <base>..<head> (head defaults to HEAD)
#   lang_commits.sh --last <commit>   judge one commit (a push that creates a branch has no base)
#
# No --strict: layer 3 blocks honest English on a subject line (an English subject dominated by an
# invented identifier was measured coming back Tagalog at 0.86 confidence). PR text keeps --strict,
# where the input is prose. Pin: tools/darnlang_ref.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=darnlang_ref.sh
. tools/darnlang_ref.sh
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

if [ "${1:-}" = "--last" ]; then
  git log -1 --format=%B "${2:?usage: lang_commits.sh --last <commit>}" > "$tmp/msgs.txt"
else
  base="${1:?usage: lang_commits.sh <base> [<head>] | --last <commit>}"
  git log --format=%B "${base}..${2:-HEAD}" > "$tmp/msgs.txt"
fi
uvx --from "$DARNLANG_REF" darnlang prose "$tmp/msgs.txt" --label "set of commit messages"
