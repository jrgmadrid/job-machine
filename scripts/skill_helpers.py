"""Small CLI shims for the on-demand Claude Code skills (tailor, cover, research, followup).

Subcommands:
    application <id>         print the application row as JSON, or "null" if not found (rc=1)
    resume                   print the resume markdown blob (or empty if unset)
    brief <company>          print the cached company brief (or empty if missing/stale)
    save-brief <company>     read a brief from stdin and persist it to Turso
    company-from <arg>       if <arg> is an application_id, print the row's company; else echo <arg>
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from scripts.db import Database


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_app = sub.add_parser("application")
    p_app.add_argument("id")

    sub.add_parser("resume")

    p_brief = sub.add_parser("brief")
    p_brief.add_argument("company")

    p_save = sub.add_parser("save-brief")
    p_save.add_argument("company")

    p_co = sub.add_parser("company-from")
    p_co.add_argument("arg")

    args = parser.parse_args()
    db = Database.from_env()

    if args.cmd == "application":
        a = db.get(args.id)
        if a is None:
            print("null")
            return 1
        print(json.dumps(asdict(a)))
        return 0

    if args.cmd == "resume":
        print(db.get_resume() or "", end="")
        return 0

    if args.cmd == "brief":
        print(db.get_research(args.company) or "", end="")
        return 0

    if args.cmd == "save-brief":
        db.save_research(args.company, sys.stdin.read())
        return 0

    if args.cmd == "company-from":
        a = db.get(args.arg)
        print(a.company if a else args.arg)
        return 0

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
