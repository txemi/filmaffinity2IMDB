#!/usr/bin/env bash
# SINGLE SOURCE OF THE darnlang VERSION for this repo. Change the ref here and nowhere else.
#
# Pinned, never floating: a floating `darnlang` resolves to whatever is newest, so an upstream
# detector change could turn this repo red on a day nobody touched it -- which, in a repo that goes
# months between commits, means the failure would be waiting for whoever comes back to it.
export DARNLANG_REF="git+https://github.com/txemi/darnlang@v0.4.0"
