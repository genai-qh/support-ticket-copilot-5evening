# eval/run_questions.py
import json
import os
import time
from pathlib import Path

from app.grounded import answer

QUESTIONS_PATH = Path("eval/questions.jsonl")


def load_questions() -> list[dict]:
    return [
        json.loads(line)
        for line in QUESTIONS_PATH.read_text().splitlines()
        if line.strip()
    ]


def score_one(q: dict) -> dict:
    question = q["q"]
    expected = q["expected_source"]

    started = time.perf_counter()
    result = answer(question, tenant_id=1)
    elapsed = time.perf_counter() - started

    got_sources = result.get("sources", [])
    abstained = result.get("answer", "").strip().upper().startswith("ABSTAIN")

    if expected is None:
        correct = abstained
        failure_type = None if correct else "should_have_abstained"
    else:
        correct = expected in got_sources
        if correct:
            failure_type = None
        elif abstained:
            failure_type = "over_abstained"
        elif got_sources:
            failure_type = "wrong_source"
        else:
            failure_type = "no_citation"

    return {
        "question": question,
        "expected": expected,
        "got_sources": got_sources,
        "answer_excerpt": result.get("answer", "")[:120],
        "abstained": abstained,
        "correct": correct,
        "failure_type": failure_type,
        "seconds": round(elapsed, 3),
    }


def main():
    questions = load_questions()
    tag = os.environ.get("EVAL_TAG", "baseline")

    print(f"=== Model: {os.environ.get('MODEL', 'unknown')} ===")
    print(f"=== Tag: {tag} ===")
    print(f"=== Questions: {len(questions)} ===\n")

    results = []
    for q in questions:
        r = score_one(q)
        results.append(r)
        marker = "OK " if r["correct"] else "BAD"
        print(
            f"{marker} | {r['question'][:52]:52s} | "
            f"exp={str(r['expected']):20s} got={r['got_sources']} "
            f"({r['seconds']}s)"
        )

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    answerable = [r for r in results if r["expected"] is not None]
    unanswerable = [r for r in results if r["expected"] is None]
    ans_correct = sum(1 for r in answerable if r["correct"])
    unans_correct = sum(1 for r in unanswerable if r["correct"])
    avg_time = sum(r["seconds"] for r in results) / total

    print(f"\n=== Summary ({tag}) ===")
    print(f"Answerable:   {ans_correct}/{len(answerable)}")
    print(f"Unanswerable: {unans_correct}/{len(unanswerable)}")
    print(f"Total:        {correct}/{total} ({100*correct/total:.1f}%)")
    print(f"Avg latency:  {avg_time:.3f}s")

    out = Path(f"artifacts/eval_{tag}.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()