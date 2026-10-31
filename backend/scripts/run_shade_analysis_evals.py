#!/usr/bin/env python3
"""
Run the small live shade-analysis eval set against /api/analyze-shade.

Requires OPENAI_API_KEY (or a running backend with the key configured).
Does not invent pass/fail — prints structured checks for manual RESULTS.md logging.

Usage (from backend/):
  python -m scripts.run_shade_analysis_evals
  python -m scripts.run_shade_analysis_evals --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx

EVALS_PATH = Path(__file__).resolve().parents[1] / "evals" / "shade_mismatch_cases.json"


def _blob(analysis: Dict[str, Any]) -> str:
    parts: List[str] = [
        analysis.get("summary", ""),
        analysis.get("analysis_vs_recommendation_note", ""),
        " ".join(analysis.get("possible_explanations") or []),
        " ".join(analysis.get("undertone_adjustments_to_try") or []),
        " ".join(analysis.get("suggested_next_steps") or []),
        " ".join(analysis.get("uncertainties") or []),
        " ".join(analysis.get("reported_color_issues") or []),
    ]
    return " ".join(parts).lower()


def score_case(case: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
    """Return human-readable check notes (not automated pass/fail for soft cues)."""
    expected = case.get("expected") or {}
    notes: List[str] = []
    text = _blob(analysis)

    reported = analysis.get("reported_depth_match")
    if "reported_depth_match" in expected and reported != expected["reported_depth_match"]:
        notes.append(
            f"FAIL depth: got {reported!r}, expected {expected['reported_depth_match']!r}"
        )
    else:
        notes.append(f"OK depth reported_depth_match={reported!r}")

    if expected.get("reported_wear_change"):
        got = analysis.get("reported_wear_change")
        if got != expected["reported_wear_change"]:
            notes.append(
                f"FAIL wear: got {got!r}, expected {expected['reported_wear_change']!r}"
            )
        else:
            notes.append(f"OK wear={got!r}")

    if expected.get("must_list_uncertainties"):
        if analysis.get("uncertainties"):
            notes.append("OK uncertainties present")
        else:
            notes.append("FAIL must_list_uncertainties")

    if expected.get("must_not_claim_verified_match"):
        if "verified match" in text or "guaranteed match" in text:
            notes.append("FAIL invented verified-match claim")
        else:
            notes.append("OK no verified-match claim")

    if expected.get("must_not_invent_cross_brand_equivalence"):
        # Soft heuristic — flag confident cross-brand SKU language.
        if "equivalent to" in text or ("same as" in text and "brand" in text):
            notes.append("REVIEW possible cross-brand equivalence language")
        else:
            notes.append("OK no obvious cross-brand equivalence")

    if expected.get("must_not_claim_photo_analysis"):
        if "photo" in text and ("analyzed" in text or "from your photo" in text):
            notes.append("FAIL photo-analysis claim")
        else:
            notes.append("OK no photo-analysis claim")

    if expected.get("must_not_force_confident_diagnosis"):
        if "certainly" in text or "definitely your undertone" in text:
            notes.append("FAIL overconfident diagnosis")
        else:
            notes.append("OK not forcing confident diagnosis")

    soft_keys = [
        "should_mention_color_issue",
        "should_suggest_cooler_or_less_warm",
        "should_suggest_warmer_or_neutral",
        "should_prioritize_lighter_depth",
        "should_discuss_oxidation_or_wear_change",
        "should_flag_contradiction_or_uncertainty",
    ]
    for key in soft_keys:
        if key not in expected:
            continue
        value = expected[key]
        if key == "should_mention_color_issue" and isinstance(value, str):
            notes.append(
                "SOFT OK color cue" if value.lower() in text else f"SOFT MISS color cue {value!r}"
            )
        elif value is True:
            cues = {
                "should_suggest_cooler_or_less_warm": ("cool", "less warm", "neutral"),
                "should_suggest_warmer_or_neutral": ("warm", "neutral"),
                "should_prioritize_lighter_depth": ("lighter", "one shade lighter", "lighter depth"),
                "should_discuss_oxidation_or_wear_change": (
                    "oxid",
                    "after wear",
                    "wear",
                    "darken",
                ),
                "should_flag_contradiction_or_uncertainty": (
                    "unclear",
                    "contradict",
                    "uncertain",
                    "lighting",
                ),
            }.get(key, ())
            hit = any(c in text for c in cues)
            notes.append(f"SOFT {'OK' if hit else 'MISS'} {key}")

    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ShadeWise shade analysis evals")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    if not EVALS_PATH.exists():
        print(f"Missing eval file: {EVALS_PATH}", file=sys.stderr)
        return 2

    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    print(f"Prompt version: {data.get('prompt_version')}")
    print(f"Cases: {len(cases)}")
    print(f"Target: {args.base_url.rstrip('/')}/api/analyze-shade\n")

    health = httpx.get(f"{args.base_url.rstrip('/')}/health", timeout=10.0)
    health.raise_for_status()
    health_json = health.json()
    if not health_json.get("openai_configured"):
        print(
            "OPENAI is not configured on the backend (openai_configured=false).\n"
            "Set OPENAI_API_KEY in backend/.env, restart uvicorn, then re-run.\n"
            "Leaving RESULTS.md as not_run.",
            file=sys.stderr,
        )
        return 3

    any_hard_fail = False
    with httpx.Client(timeout=60.0) as client:
        for case in cases:
            case_id = case["id"]
            print(f"=== {case_id} ===")
            response = client.post(
                f"{args.base_url.rstrip('/')}/api/analyze-shade",
                json=case["input"],
            )
            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {response.text}")
                any_hard_fail = True
                continue
            body = response.json()
            analysis = body.get("analysis") or {}
            for note in score_case(case, analysis):
                print(f"  - {note}")
                if note.startswith("FAIL"):
                    any_hard_fail = True
            print()

    print(
        "Update backend/evals/RESULTS.md with pass/fail + date after reviewing notes above."
    )
    return 1 if any_hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
