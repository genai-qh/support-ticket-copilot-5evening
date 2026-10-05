# app/compare.py
import json
from app.model import chat
from app.grounded import answer

QUESTIONS = [
    ("A customer can't log in after a password reset.", 1),
    ("Invoice line items don't match the order.", 1),
    ("API calls from one client keep timing out.", 1),
    ("What is the refund policy for annual plans?", 1),  # unanswerable
]


def ungrounded(question: str) -> dict:
    result = chat(question, num_predict=256)
    return {"answer": result["content"], "seconds": result["seconds"]}


if __name__ == "__main__":
    rows = []
    for q, tid in QUESTIONS:
        g = answer(q, tenant_id=tid)
        u = ungrounded(q)
        rows.append({"q": q, "grounded": g, "ungrounded": u})

    print(json.dumps(rows, indent=2))