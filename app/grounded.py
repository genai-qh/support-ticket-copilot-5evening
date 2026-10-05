# app/grounded.py
import json
import re
from app.model import chat
from app.retrieval import search

SYSTEM = (
    "You are a support-ticket assistant. You will receive numbered runbook "
    "excerpts and a question. Answer using ONLY the excerpts provided.\n\n"
    "Rules:\n"
    "1. If an excerpt DIRECTLY answers the question, answer using it and cite "
    "the source ID in square brackets, e.g. [rb-access-v1].\n"
    "2. Cite ONLY source IDs that appear in the excerpts. Never invent a "
    "source ID, never cite a source that was not provided.\n"
    "3. If none of the excerpts are relevant, respond with exactly: ABSTAIN\n"
    "4. Keep answers short and factual."
)

_SOURCE_RE = re.compile(r"\[(rb-[a-z0-9\-]+)\]")

# Hard relevance floor: require at least this many distinct CONTENT-word
# tokens from the query to appear in a runbook body. Function words like
# "what", "our", "during" are ignored so they don't inflate the score.
# This is a code-level safety net, not a prompt instruction.
MIN_RELEVANCE = 2

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "into",
    "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "should", "may", "might", "must",
    "i", "you", "he", "she", "it", "we", "they",
    "my", "your", "his", "her", "its", "our", "their",
    "this", "that", "these", "those",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "not", "no", "so", "as", "than",
    "about", "during", "after", "before", "between", "over", "under",
    "up", "down", "out", "off", "again", "any", "some",
    "get", "got", "make", "made", "go", "goes", "went",
}


def _content_tokens(text: str) -> set[str]:
    """Extract lowercase alphanumeric content-word tokens (len > 2,
    not in STOP_WORDS)."""
    tokens = set()
    for t in text.lower().split():
        cleaned = "".join(c for c in t if c.isalnum())
        if len(cleaned) > 2 and cleaned not in STOP_WORDS:
            tokens.add(cleaned)
    return tokens


def _relevance_score(question: str, runbook: dict) -> int:
    """How many distinct content tokens from the query appear in the
    runbook body?"""
    tokens = _content_tokens(question)
    body = runbook["body"].lower()
    return sum(1 for t in tokens if t in body)


def build_prompt(question: str, hits: list[dict]) -> str:
    context = "\n\n".join(
        f"Excerpt {i+1} [{h['source_id']}]\n{h['body']}"
        for i, h in enumerate(hits)
    )
    return (
        f"Runbook excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer with citations. If none of the excerpts directly answer the "
        f"question, respond with exactly: ABSTAIN"
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

    # Enforce a hard relevance floor. Do not rely on the model to abstain.
    hits = [h for h in hits if _relevance_score(question, h) >= MIN_RELEVANCE]

    if not hits:
        return {
            "answer": "ABSTAIN",
            "sources": [],
            "reason": "no runbook above relevance floor",
            "seconds": 0.0,
        }

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
        ("What's our policy for compensating customers during an outage?", 1),
    ]
    for q, tid in tests:
        print(f"\n=== {q} ===")
        r = answer(q, tenant_id=tid)
        print(json.dumps(r, indent=2))