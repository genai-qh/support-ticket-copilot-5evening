# app/grounded.py
import json
import re
from app.model import chat
from app.retrieval import search

SYSTEM = (
    "You are a support-ticket assistant. You will receive numbered runbook "
    "excerpts and a question. Answer using ONLY the excerpts provided.\n\n"
    "Rules:\n"
    "1. If any excerpt is relevant to the question, answer using it and cite "
    "the source ID in square brackets, e.g. [rb-access-v1].\n"
    "2. Cite ONLY source IDs that appear in the excerpts. Never invent a "
    "source ID, never cite a source that was not provided.\n"
    "3. If none of the excerpts are relevant, respond with exactly: ABSTAIN\n"
    "4. Keep answers short and factual."
)

_SOURCE_RE = re.compile(r"\[(rb-[a-z0-9\-]+)\]")


def build_prompt(question: str, hits: list[dict]) -> str:
    context = "\n\n".join(
        f"Excerpt {i+1} [{h['source_id']}]\n{h['body']}"
        for i, h in enumerate(hits)
    )
    return (
        f"Runbook excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer with citations, or ABSTAIN if none of the excerpts apply."
    )


def _strip_invalid_citations(text: str, allowed: set[str]) -> tuple[str, set[str]]:
    """Remove any [rb-xxx] not in allowed from the text. Return cleaned text
    and the set of valid sources that remained."""
    valid = set()

    def replacer(match):
        sid = match.group(1)
        if sid in allowed:
            valid.add(sid)
            return match.group(0)
        return ""  # drop invalid citation

    cleaned = _SOURCE_RE.sub(replacer, text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned, valid


def answer(question: str, tenant_id: int) -> dict:
    hits = search(question, tenant_id=tenant_id, k=2)
    if not hits:
        return {"answer": "ABSTAIN", "sources": [], "seconds": 0.0}

    prompt = build_prompt(question, hits)
    result = chat(prompt, system=SYSTEM, num_predict=256)

    allowed = {h["source_id"] for h in hits}
    text = result["content"].strip()

    # Fast path: model said ABSTAIN
    if text.upper().startswith("ABSTAIN"):
        return {
            "answer": "ABSTAIN",
            "sources": [],
            "seconds": result["seconds"],
        }

    # Strip invalid citations instead of rejecting the whole answer
    cleaned, valid_cited = _strip_invalid_citations(text, allowed)

    # If nothing valid remains, the answer is ungrounded
    if not valid_cited:
        return {
            "answer": "ABSTAIN",
            "sources": [],
            "reason": "no valid citations after stripping",
            "seconds": result["seconds"],
        }

    return {
        "answer": cleaned,
        "sources": sorted(valid_cited),
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