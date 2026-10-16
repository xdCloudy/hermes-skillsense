#!/usr/bin/env python3
"""Transparent synthetic skill-routing evaluation.

This is a development smoke suite, NOT a held-out, human-labelled test set or
a claim of real-world correctness. It requires no Hermes, network, or model.
"""
from __future__ import annotations
import argparse
import json
import math
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


def wilson_95(successes: int, trials: int) -> list[float] | None:
    """95% Wilson score interval for binary outcomes."""
    if trials <= 0:
        return None
    if not 0 <= successes <= trials:
        raise ValueError("invalid binomial counts")
    z = 1.959963984540054
    p = successes / trials
    denom = 1 + z*z/trials
    center = (p + z*z/(2*trials)) / denom
    radius = z*math.sqrt(p*(1-p)/trials + z*z/(4*trials*trials))/denom
    return [round(max(0.0, center-radius), 4), round(min(1.0, center+radius), 4)]


def evaluate(catalogue: list[dict], cases: list[dict], variant: str) -> dict:
    Router = router_class()
    data = []
    for item in catalogue:
        record = dict(item)
        if variant == "names":
            record.update(description="",tags=[],aliases=[],intents=[],negative_intents=[])
        elif variant == "source":
            record.update(aliases=[],intents=[],negative_intents=[])
        data.append(record)
    router = Router(data)
    top1 = hits = relevant = no_skill = false_positives = correct_abstentions = 0
    relevant_ids = retrieved_ids = emitted_hints = correct_hints = 0
    times = []
    errors = []
    for case in cases:
        start = time.perf_counter_ns()
        # Compute true @3 retrieval with three permitted suggestions, not the
        # normal-turn default limit of two. Conservative gating may emit fewer.
        suggested = parse_names(router.suggest(case["prompt"], max_suggestions=3))
        times.append((time.perf_counter_ns() - start) / 1e6)
        expected = set(case["gold"])
        relevant_ids += len(expected)
        retrieved_ids += len(expected.intersection(suggested[:3]))
        emitted_hints += len(suggested[:3])
        correct_hints += len(expected.intersection(suggested[:3]))
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
        # Legacy v0.2 fields refer to task hit rate, not micro-averaged
        # recall or the precision of emitted hints. Preserve for consumers.
        "precision_at_1_on_positive":round(top1/relevant,4) if relevant else 0,
        "recall_at_3_on_positive":round(hits/relevant,4) if relevant else 0,
        "top1_positive_hit_rate":round(top1/relevant,4) if relevant else None,
        "top3_positive_hit_rate":round(hits/relevant,4) if relevant else None,
        "micro_recall_at_3":round(retrieved_ids/relevant_ids,4) if relevant_ids else None,
        "precision_of_emitted_hints":round(correct_hints/emitted_hints,4) if emitted_hints else None,
        "no_skill_false_positive_rate":round(false_positives/no_skill,4) if no_skill else None,
        "counts":{"positive_top1_hits":top1,"positive_top3_hits":hits,
                  "relevant_skill_labels":relevant_ids,"retrieved_relevant_labels":retrieved_ids,
                  "emitted_hints":emitted_hints,"correct_hints":correct_hints,
                  "no_skill_false_positives":false_positives},
        "wilson_95":{
            "positive_top1_hit_rate":wilson_95(top1,relevant),
            "no_skill_false_positive_rate":wilson_95(false_positives,no_skill),
        },
        "latency_ms_p50":round(statistics.median(times),4) if times else 0,
        "latency_ms_p95":round(sorted_times[min(len(times)-1, int(len(times)*.95))],4) if times else 0,
        "misses_and_false_positives":errors,
    }



def validate_fixtures(catalogue: object, fixture: object) -> tuple[list[dict], list[dict]]:
    """Reject malformed or ambiguous labels before reporting selection accuracy."""
    if (not isinstance(catalogue, dict) or not isinstance(fixture, dict)
            or type(catalogue.get("schema_version")) is not int
            or type(fixture.get("schema_version")) is not int
            or catalogue["schema_version"] != 1 or fixture["schema_version"] != 1):
        raise ValueError("unsupported fixture schema")
    skills, cases = catalogue.get("skills"), fixture.get("cases")
    if not isinstance(skills, list) or not isinstance(cases, list):
        raise ValueError("fixture skills and cases must be lists")
    provenance = fixture.get("source")
    if not isinstance(provenance, str) or not provenance.strip() or len(provenance) > 500:
        raise ValueError("invalid dataset provenance")
    if len(skills) > 10000 or len(cases) > 10000:
        raise ValueError("fixture exceeds 10000 skill/case limit")

    names, identities = set(), set()
    for skill in skills:
        if not isinstance(skill, dict):
            raise ValueError("invalid skill record")
        name, identity = skill.get("name"), skill.get("id")
        if (not isinstance(name, str) or not name.strip() or len(name) > 200
                or not isinstance(identity, str) or not identity.strip()
                or len(identity) > 1000):
            raise ValueError("invalid skill name or ID")
        if name in names or identity in identities:
            raise ValueError("duplicate skill name or ID; labels must be unambiguous")
        names.add(name)
        identities.add(identity)
        description = skill.get("description", "")
        if not isinstance(description, str) or len(description) > 20000:
            raise ValueError("invalid skill metadata")
        for field in ("tags", "aliases", "intents", "negative_intents"):
            values = skill.get(field, [])
            if (not isinstance(values, list) or len(values) > 100
                    or any(not isinstance(value, str) or len(value) > 1000
                           for value in values)):
                raise ValueError("invalid skill metadata")

    if not cases:
        raise ValueError("no cases or duplicate case IDs")
    seen_cases = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("invalid case prompt or identifier")
        prompt, case_id = case.get("prompt"), case.get("id")
        if (not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000
                or not isinstance(case_id, str) or not case_id.strip()
                or len(case_id) > 120):
            raise ValueError("invalid case prompt or identifier")
        if case_id in seen_cases:
            raise ValueError("no cases or duplicate case IDs")
        seen_cases.add(case_id)
        gold = case.get("gold")
        if (not isinstance(gold, list)
                or any(not isinstance(value, str) or not value for value in gold)
                or len(set(gold)) != len(gold) or not set(gold).issubset(names)):
            raise ValueError("missing or unknown ground truth IDs")
    return skills, cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json",action="store_true",help="Machine-readable output")
    parser.add_argument("--catalogue",type=Path,default=ROOT/"benchmarks/selection-catalogue-v1.json",
                        help="JSON skill catalogue (offline local file)")
    parser.add_argument("--cases",type=Path,default=ROOT/"benchmarks/selection-cases-v1.json",
                        help="JSON labelled prompts (offline local file)")
    args = parser.parse_args()
    cat = json.loads(args.catalogue.read_text(encoding="utf-8"))
    fixture = json.loads(args.cases.read_text(encoding="utf-8"))
    skills, cases = validate_fixtures(cat, fixture)
    reports = [evaluate(skills, cases, variant) for variant in ("names","source","enriched")]
    if args.json:
        print(json.dumps({"dataset":fixture["source"],"results":reports},indent=2))
    else:
        print("Offline retrieval fixture:",fixture.get("source","unreviewed provenance"))
        print("Metrics are NOT independent model quality evidence without held-out labels.")
        for r in reports:
            def fmt(value):
                return "n/a" if value is None else f"{value:.3f}"
            print(f"{r['variant']:<10} top1-hit={fmt(r['top1_positive_hit_rate'])} "
                  f"(95% CI {r['wilson_95']['positive_top1_hit_rate']}) "
                  f"micro-recall@3={fmt(r['micro_recall_at_3'])} "
                  f"hint-precision={fmt(r['precision_of_emitted_hints'])} "
                  f"no-skill-FPR={fmt(r['no_skill_false_positive_rate'])} "
                  f"(95% CI {r['wilson_95']['no_skill_false_positive_rate']}) "
                  f"p95={r['latency_ms_p95']:.3f}ms, errors={len(r['misses_and_false_positives'])}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
