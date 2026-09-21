#!/usr/bin/env bash
# English-only gate, one entry point for every place that runs it (GitHub Actions, Jenkins, by hand).
#
#   lang-gate.sh tree                  judge every tracked file
#   lang-gate.sh commits <git-range>   judge the commit messages of a range, e.g. origin/master..HEAD
#   lang-gate.sh pr-text               judge $PR_TITLE and $PR_BODY (read from the environment)
#
# The callers only decide WHICH range and WHERE the PR text comes from; what is judged and how lives
# here, so the two CI systems cannot drift apart. Pin: tools/darnlang_ref.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."
# shellcheck source=../darnlang_ref.sh
. tools/darnlang_ref.sh
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

case "${1:-}" in
  tree)
    # Fail-closed: the tree is at 0 findings.
    uvx --from "$DARNLANG_REF" darnlang check --ext all
    ;;
  commits)
    range="${2:?usage: lang-gate.sh commits <git-range>}"
    # shellcheck disable=SC2086  # the range may be "<sha> -1" (root push), so it must word-split
    git log --format=%B $range > "$tmp/msgs.txt"
    # No --strict: layer 3 blocks honest English on a subject line (an English subject dominated by an
    # invented identifier was measured coming back Tagalog at 0.86 confidence). The PR-text step keeps
    # --strict, where the input is prose.
    uvx --from "$DARNLANG_REF" darnlang prose "$tmp/msgs.txt" --label "set of commit messages"
    ;;
  pr-text)
    # Title and body arrive through the environment, never interpolated into a shell line: both are
    # attacker-controlled on a public repo.
    printf '%s\n\n%s\n' "${PR_TITLE:-}" "${PR_BODY:-}" > "$tmp/pr.txt"
    uvx --from "darnlang[strict] @ $DARNLANG_REF" darnlang prose "$tmp/pr.txt" --strict --label "PR title/description"
    ;;
  *)
    echo "usage: lang-gate.sh tree | commits <git-range> | pr-text" >&2
    exit 2
    ;;
esac
