"""Regenerate an evidence-linked report from a saved local match.json."""

import argparse
import json
from pathlib import Path

from .diagnostics import write_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match_json", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.match_json.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        parser.error("Unsupported diagnostics schema")
    write_artifacts(args.match_json.parent, payload)
    print(args.match_json.parent / "report.md")


if __name__ == "__main__":
    main()
