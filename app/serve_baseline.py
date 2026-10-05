# app/serve_baseline.py
from app.model import chat

if __name__ == "__main__":
    prompt = (
        "Classify this ticket: Cannot sign in. "
        "Return only access, billing, or reliability."
    )
    result = chat(prompt, num_predict=64)
    print("--- answer ---")
    print(result["content"])
    print(f"--- end-to-end latency: {result['seconds']:.3f}s ---")