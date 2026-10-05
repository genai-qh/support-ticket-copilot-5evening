# app/retrieval.py
from pathlib import Path
import yaml

RUNBOOK_DIR = Path("data")


def _parse(path: Path) -> dict:
    text = path.read_text()
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        meta = yaml.safe_load(front) or {}
    else:
        meta, body = {}, text
    return {
        "source_id": meta.get("source_id"),
        "tenant_id": meta.get("tenant_id"),
        "version": meta.get("version"),
        "body": body.strip(),
        "path": str(path),
    }


def load_runbooks() -> list[dict]:
    return [_parse(p) for p in sorted(RUNBOOK_DIR.glob("runbook_*.md"))]


def search(query: str, tenant_id: int, k: int = 2) -> list[dict]:
    """Naive keyword overlap over runbooks. Tenant-filtered."""
    tokens = {t.lower().strip(".,?!") for t in query.split() if len(t) > 2}
    scored = []
    for rb in load_runbooks():
        if rb["tenant_id"] != tenant_id:
            continue
        body_lower = rb["body"].lower()
        score = sum(1 for t in tokens if t in body_lower)
        if score > 0:
            scored.append((score, rb))
    scored.sort(key=lambda x: -x[0])
    return [rb for _, rb in scored[:k]]


if __name__ == "__main__":
    for rb in load_runbooks():
        print(rb["source_id"], "| tenant", rb["tenant_id"])
    print()
    hits = search("cannot sign in to my account", tenant_id=1)
    for h in hits:
        print("HIT:", h["source_id"])