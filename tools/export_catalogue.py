#!/usr/bin/env python3
"""Export a local, canonical SkillSense skill catalogue for offline evaluation.

No model calls, web calls, prompt history, or implicit file uploads.
This output may still contain private skill names and descriptions. Review
before sharing or publishing it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from routing_import import router_class


def export(data_dir: Path, output: Path) -> int:
    router_class()  # Load the plugin package without installing it into Hermes.
    from skillsense_bench.store import read_native_snapshot, read_index
    from skillsense_bench.eligibility import compose_native_records

    if not data_dir.is_dir():
        raise ValueError(f"Data directory does not exist: {data_dir}")
    available = read_native_snapshot(data_dir)
    if not available:
        raise ValueError(
            "Canonical skill snapshot missing, empty or expired. "
            "Run 'hermes skillrouter refresh-native' or 'hermes skillrouter rebuild' first."
        )
    indexed = read_index(data_dir)
    records = compose_native_records(indexed, available)

    # Export exactly the fields the offline BM25 evaluator consumes.
    skills = [
        {
            "id": record["id"],
            "name": record["name"],
            "description": record.get("description", ""),
            "tags": record.get("tags", []),
            "aliases": record.get("aliases", []),
            "intents": record.get("intents", []),
            "negative_intents": record.get("negative_intents", []),
        }
        for record in sorted(records, key=lambda x: (x["name"], x["id"]))
    ]
    payload = {"schema_version": 1, "skills": skills}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation means existing local evidence is never overwritten.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return len(skills)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Local SkillSense profile data directory")
    parser.add_argument("--output", type=Path, required=True,
                        help="New local catalogue JSON file; refuses to overwrite")
    args = parser.parse_args()
    try:
        count = export(args.data_dir.expanduser(), args.output.expanduser())
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(f"Exported {count} locally verified skills. Review the output before sharing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
