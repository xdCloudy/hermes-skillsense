#!/usr/bin/env python3
"""Transparent synthetic skill-routing evaluation.

This is a development smoke suite, NOT a held-out, human-labelled test set or
a claim of real-world correctness. It requires no Hermes, network, or model.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from routing_import import router_class  # lazy synthetic standalone import


def parse_names(hint: str | None) -> list[str]:
    if not hint:
        return []
    result = []
    for line in hint.splitlines():
        if line.startswith("- "):
            result.append(line[2:].split(" (matched:", 1)[0].strip())
    return result


def evaluate(catalogue: list[dict], cases: list[dict], variant: str) -> dict:
    Router = router_class()
    data = []
    for item in catalogue:
        record = dict(item)
        if variant == "names":
            record.update(description="",tags=[],aliases=[],intents=[])
        elif variant == "source":
            record.update(aliases=[],intents=[])
        data.append(record)
    router = Router(data)
    top1 = hits = relevant = no_skill = false_positives = correct_abstentions = 0
    times = []
    errors = []
    for case in cases:
        start = time.perf_counter_ns()
        suggested = parse_names(router.suggest(case["prompt"]))
        times.append((time.perf_counter_ns() - start) / 1e6)
        expected = set(case["gold"])
        if expected:
            relevant += 1
            top1 += int(bool(suggested) and suggested[0] in expected)
            hits += int(bool(expected.intersection(suggested[:3])))
            if not expected.intersection(suggested[:3]):
                errors.append({"id":case["id"],"expected":sorted(expected),"actual":suggested})
        else:
            no_skill += 1
            false_positives += int(bool(suggested))
            correct_abstentions += int(not suggested)
            if suggested:
                errors.append({"id":case["id"],"expected":[],"actual":suggested})
    sorted_times = sorted(times)
    return {
        "variant":variant, "total":len(cases), "relevant":relevant, "no_skill":no_skill,
        "precision_at_1_on_positive":round(top1/relevant,4) if relevant else 0,
        "recall_at_3_on_positive":round(hits/relevant,4) if relevant else 0,
        "no_skill_false_positive_rate":round(false_positives/no_skill,4) if no_skill else 0,
        "latency_ms_p50":round(statistics.median(times),4) if times else 0,
        "latency_ms_p95":round(sorted_times[min(len(times)-1, int(len(times)*.95))],4) if times else 0,
        "misses_and_false_positives":errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json",action="store_true",help="Machine-readable output")
    args = parser.parse_args()
    cat = json.loads((ROOT/"benchmarks/selection-catalogue-v1.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT/"benchmarks/selection-cases-v1.json").read_text(encoding="utf-8"))
    cases = fixture["cases"]
    known = {r["name"] for r in cat["skills"]}
    if not cases or len({case["id"] for case in cases}) != len(cases):
        raise ValueError("no cases or duplicate case IDs")
    if any(not isinstance(c.get("gold"),list) or not set(c["gold"]).issubset(known)
           for c in cases):
        raise ValueError("missing or unknown ground truth IDs")
    reports = [evaluate(cat["skills"],cases,variant) for variant in ("names","source","enriched")]
    if args.json:
        print(json.dumps({"dataset":fixture["source"],"results":reports},indent=2))
    else:
        print("Synthetic development set, NOT independent model quality evidence")
        for r in reports:
            print(f"{r['variant']:<10} top1={r['precision_at_1_on_positive']:.3f} "
                  f"recall@3={r['recall_at_3_on_positive']:.3f} "
                  f"no-skill-FPR={r['no_skill_false_positive_rate']:.3f} "
                  f"p95={r['latency_ms_p95']:.3f}ms, errors={len(r['misses_and_false_positives'])}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
