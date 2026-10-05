# infra/release_gate.py
"""
Release gate: run every test + evaluation the release must pass.

Exit codes:
  0 = all checks passed (release allowed)
  1 = one or more checks failed (release blocked)

Usage:
  uv run python -m infra.release_gate            # full gate
  uv run python -m infra.release_gate --quick    # skip eval (fast PR check)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_BASELINE = REPO_ROOT / "artifacts" / "eval_baseline.json"
MIN_QUALITY_SCORE = 14   # must match or beat the frozen baseline
MAX_AVG_LATENCY = 5.0    # seconds


def run_step(name: str, cmd: list[str]) -> tuple[bool, str]:
    """Run a subprocess. Return (success, combined_output)."""
    print(f"\n{'='*70}")
    print(f"STEP: {name}")
    print(f"CMD:  {' '.join(cmd)}")
    print("=" * 70)
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    print(output)
    return result.returncode == 0, output


def check_eval_score() -> tuple[bool, str]:
    """Run the evaluation and check the score against the baseline."""
    from eval.run_questions import load_questions, score_one  # noqa: E402

    questions = load_questions()
    results = [score_one(q) for q in questions]

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    unanswerable = [r for r in results if r["expected"] is None]
    unans_ok = sum(1 for r in unanswerable if r["correct"])
    avg_time = sum(r["seconds"] for r in results) / total

    # Read baseline for comparison
    baseline_total = None
    if EVAL_BASELINE.exists():
        baseline = json.loads(EVAL_BASELINE.read_text())
        baseline_total = sum(1 for r in baseline if r["correct"])

    lines = [
        f"Eval: {correct}/{total}",
        f"  Unanswerable: {unans_ok}/{len(unanswerable)}",
        f"  Avg latency: {avg_time:.3f}s",
    ]
    if baseline_total is not None:
        lines.append(f"  Baseline was: {baseline_total}/{total}")
        lines.append(f"  Delta: {correct - baseline_total:+d}")

    # Fail conditions
    ok = True
    if correct <= MIN_QUALITY_SCORE:
        lines.append(f"  ✗ FAIL: score {correct} <= minimum {MIN_QUALITY_SCORE}")
        ok = False
    if unans_ok < len(unanswerable):
        lines.append(
            f"  ✗ FAIL: {len(unanswerable) - unans_ok} unanswerable question(s) "
            f"did not abstain"
        )
        ok = False
    if avg_time > MAX_AVG_LATENCY:
        lines.append(f"  ✗ FAIL: avg latency {avg_time:.2f}s > max {MAX_AVG_LATENCY}s")
        ok = False

    if ok:
        lines.append("  ✓ All eval thresholds passed")

    return ok, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Skip the eval step (fast PR check)")
    args = parser.parse_args()

    results = []

    # Step 1: data tests
    ok, _ = run_step(
    "Data, schema, and permission tests",
        ["uv", "run", "pytest", "-v", "tests/"],
    )
    results.append(("Data, schema, and permission tests", ok))

    # Step 2: check_env sanity
    ok, _ = run_step("Environment sanity", ["uv", "run", "python", "-m", "app.check_env"])
    results.append(("Environment sanity", ok))

    # Step 3: tool contract tests (no network) — quick check that tools import
    ok, _ = run_step(
        "Tool imports",
        ["uv", "run", "python", "-c",
         "from app.tools import get_ticket, search_runbooks; print('tools ok')"],
    )
    results.append(("Tool imports", ok))

    # Step 4: evaluation (skip in quick mode)
    if not args.quick:
        print(f"\n{'='*70}")
        print("STEP: Evaluation (quality + safety)")
        print("=" * 70)
        ok, output = check_eval_score()
        print(output)
        results.append(("Evaluation", ok))
    else:
        print("\n(skipping evaluation — quick mode)")

    # Summary
    print(f"\n{'='*70}")
    print("RELEASE GATE SUMMARY")
    print("=" * 70)
    for name, passed in results:
        print(f"  {'✓ PASS' if passed else '✗ FAIL'}  {name}")

    all_ok = all(passed for _, passed in results)
    print()
    if all_ok:
        print("RELEASE ALLOWED")
        sys.exit(0)
    else:
        print("RELEASE BLOCKED")
        sys.exit(1)


if __name__ == "__main__":
    main()