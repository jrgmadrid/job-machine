#!/usr/bin/env bash
set -e
# Forbidden tokens encoded with regex character classes so the script doesn't reject its own commit.
FORBIDDEN='\b([l]ux|[m]orningstar|[v]tuber|[l]uxuria|[p]ersona)\b'
if git diff --cached -U0 | grep -iE "$FORBIDDEN"; then
  echo "OPSEC FAIL: forbidden term in staged diff" >&2
  exit 1
fi
