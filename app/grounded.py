# app/grounded.py
import json
import re
from app.model import chat
from app.retrieval import search

SYSTEM = (
    "You are a support-ticket assistant. Answer only using the provided "
    "runbook excerpts. If the excerpts do not contain the answer, reply "
    "exactly: ABSTAIN. When you answer, cite source IDs in square brackets, "
    "e.g. [rb-access-v1]. Do not invent source IDs."
)

_SOURCE_RE = re.compile(r"\[(rb-[a-z0-9\-]+)\]")


def build_prompt(question: str, hits: list[dict]) -> str:
    context = "\n\n".join(f"[{h['source_id']}]\n{h['body']}" for h in hits)
    return (
        f"Runbook excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer with citations, or ABSTAIN if not covered."
    )


def answer(question: str, tenant_id: int) -> dict:
    hits = search(question, tenant_id=tenant_id, k=2)
    if not hits:
        return {"answer": "ABSTAIN", "sources": [], "seconds": 0.0}

    prompt = build_prompt(question, hits)
    result = chat(prompt, system=SYSTEM, num_predict=256)

    allowed = {h["source_id"] for h in hits}
    text = result["content"]

    # Extract all bracketed source IDs from the model's text
    found = set(_SOURCE_RE.findall(text))

    cited = found & allowed
    invented = found - allowed

    if invented:
        return {
            "answer": "ABSTAIN",
            "sources": [],
            "reason": f"invented sources: {sorted(invented)}",
            "seconds": result["seconds"],
        }

    return {
        "answer": text.strip(),
        "sources": sorted(cited),
        "seconds": result["seconds"],
    }


if __name__ == "__main__":
    tests = [
        ("A customer says they can't log in after resetting their password.", 1),
        ("How do we verify line items on an invoice?", 1),
        ("What's the best restaurant near the office?", 1),
    ]
    for q, tid in tests:
        print(f"\n=== {q} ===")
        r = answer(q, tenant_id=tid)
        print(json.dumps(r, indent=2))