#!/usr/bin/env python3
"""Print the description of the pull request being built, for the PR-text language gate.

Jenkins does not expose the PR description as a variable, so it is read from the forge API. The server
is derived from CHANGE_URL (set by the multibranch job), never written down here: this file is public.
Reads CHANGE_URL and API_TOKEN from the environment. Fails (rc != 0) if the body cannot be read, so a
broken lookup can never look like an empty, clean description.
"""
import json
import os
import sys
import urllib.request
from urllib.parse import urlsplit


def main() -> int:
    url = os.environ.get("CHANGE_URL", "")
    token = os.environ.get("API_TOKEN", "")
    parts = urlsplit(url)
    segs = [s for s in parts.path.split("/") if s]  # <owner>/<repo>/pulls/<n>
    if not (parts.scheme and parts.netloc and len(segs) >= 4 and segs[-2] == "pulls" and token):
        print("fetch-pr-body: need CHANGE_URL (<server>/<owner>/<repo>/pulls/<n>) and API_TOKEN", file=sys.stderr)
        return 2
    api = f"{parts.scheme}://{parts.netloc}/api/v1/repos/{segs[-4]}/{segs[-3]}/pulls/{segs[-1]}"
    req = urllib.request.Request(api, headers={"Authorization": f"token {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp).get("body")
    if body is None:
        print("fetch-pr-body: the API answer has no 'body' field", file=sys.stderr)
        return 3
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
