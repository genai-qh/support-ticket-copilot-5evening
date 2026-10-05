import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

# --- Load .env into the process environment (once, at import time) ---
_env_path = Path(".env")
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        # setdefault: don't override a real shell env var if the user set one
        os.environ.setdefault(key.strip(), value.strip())

MODEL = os.environ.get("MODEL", "llama3.2:3b")
URL = "http://127.0.0.1:11434/api/chat"


def chat(prompt: str, system: str | None = None, num_predict: int = 256) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 4096,
            "num_predict": num_predict,
        },
    }
    req = Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urlopen(req, timeout=60) as resp:
        body = json.load(resp)
    elapsed = time.perf_counter() - started
    return {"content": body["message"]["content"], "seconds": elapsed}