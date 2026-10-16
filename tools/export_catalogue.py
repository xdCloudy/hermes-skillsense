#!/usr/bin/env python3
"""Export a local, canonical SkillSense skill catalogue for offline evaluation.

No model calls, web calls, prompt history, or implicit file uploads.
This output may still contain private skill names and descriptions. Review
before sharing or publishing it.
"""
from __future__ import annotations

import argparse
import json
import os
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

    # Exporter-only opaque IDs avoid exposing absolute profile/skill paths.
    # The evaluator uses name-based labels, not native internal identities.
    skills = [
        {
            "id": f"export::{position:05d}",
            "name": record["name"],
            "description": record.get("description", ""),
            "tags": record.get("tags", []),
            "aliases": record.get("aliases", []),
            "intents": record.get("intents", []),
            "negative_intents": record.get("negative_intents", []),
        }
        for position, record in enumerate(
            sorted(records, key=lambda x: (x["name"], x["id"])), start=1
        )
    ]
    payload = {"schema_version": 1, "skills": skills}
    # Metadata may contain private skill names/descriptions. Limit access on
    # newly created output files instead of relying on the process umask.
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # Incomplete exports must not be mistaken for valid evaluation data.
        try:
            output.unlink()
        except OSError:
            pass
        raise
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
