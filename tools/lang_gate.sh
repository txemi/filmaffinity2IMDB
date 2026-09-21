#!/usr/bin/env bash
# English-only gate for the tracked tree and for PR text. Same entry point for every place that runs
# it (GitHub Actions, Jenkins, by hand); commit messages have their own script (lang_commits.sh).
#
#   lang_gate.sh tree             judge every tracked file
#   lang_gate.sh pr-text <file>   judge a file holding the PR title and description
#
# The callers only decide WHERE the PR text comes from; what is judged and how lives here, so the
# two CI systems cannot drift apart. Pin: tools/darnlang_ref.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=darnlang_ref.sh
. tools/darnlang_ref.sh

case "${1:-}" in
  tree)
    # Fail-closed: the tree is at 0 findings.
    uvx --from "$DARNLANG_REF" darnlang check --ext all
    ;;
  pr-text)
    f="${2:?usage: lang_gate.sh pr-text <file>}"
    uvx --from "darnlang[strict] @ $DARNLANG_REF" darnlang prose "$f" --strict --label "PR title/description"
    ;;
  *)
    echo "usage: lang_gate.sh tree | pr-text <file>" >&2
    exit 2
    ;;
esac
