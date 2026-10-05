# app/harness.py
import json
import time
from urllib.request import Request, urlopen

from app.model import MODEL, URL
from app.tools import get_ticket, search_runbooks

# --- The bounded tool surface ---
# Only these tools are exposed to the model. Anything else is rejected.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": (
                "Fetch a support ticket by its integer ID. "
                "Only returns tickets belonging to the caller's tenant."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The numeric ticket ID.",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_runbooks",
            "description": (
                "Search the support runbooks for passages relevant to a query. "
                "Returns source_id, version and excerpt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Short search query, max 500 chars.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

# Hard limits (page 8: "Limit the available tools, total steps,
# elapsed time, output size and spend.")
MAX_STEPS = 4
MAX_SECONDS = 30.0
MAX_OUTPUT_CHARS = 4000


def _raw_chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Low-level Ollama chat call. Does NOT go through app.model.chat,
    because tool calls need access to the raw response structure."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 512},
    }
    if tools:
        payload["tools"] = tools

    req = Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=60) as resp:
        return json.load(resp)


def _execute(tool_name: str, arguments: dict, tenant_id: int) -> dict:
    """Route an authorized tool call to the actual function."""
    if tool_name == "get_ticket":
        return get_ticket(
            ticket_id=arguments.get("ticket_id"),
            tenant_id=tenant_id,
        )
    if tool_name == "search_runbooks":
        return search_runbooks(
            query=arguments.get("query", ""),
            tenant_id=tenant_id,
        )
    return {"error": "unknown_tool", "name": tool_name}


def run(user_message: str, tenant_id: int, verbose: bool = False) -> dict:
    """The harness loop. Returns the final answer plus an execution trace."""
    started = time.perf_counter()
    messages = [{"role": "user", "content": user_message}]
    trace = []

    for step in range(MAX_STEPS):
        if time.perf_counter() - started > MAX_SECONDS:
            return {
                "answer": "BUDGET_EXCEEDED",
                "trace": trace,
                "reason": "time limit",
            }

        response = _raw_chat(messages, tools=TOOLS)
        msg = response["message"]

        # Case 1: model produced tool calls
        if msg.get("tool_calls"):
            # Append the assistant's tool-call message once
            messages.append(msg)

            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = call["function"].get("arguments", {})
                # arguments may arrive as a dict or a JSON string
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                # Execute
                result = _execute(name, args, tenant_id)
                result_str = json.dumps(result)

                # Bound the output size
                if len(result_str) > MAX_OUTPUT_CHARS:
                    result_str = result_str[:MAX_OUTPUT_CHARS] + "...[truncated]"

                # Feed the result back
                messages.append({"role": "tool", "content": result_str})
                trace.append(
                    {
                        "step": step,
                        "tool": name,
                        "args": args,
                        "result_keys": list(result.keys()),
                    }
                )

            if verbose:
                called = [t["tool"] for t in trace if t["step"] == step]
                print(f"[step {step}] tool calls executed: {called}")
            continue

        # Case 2: model produced a final answer
        answer = (msg.get("content") or "").strip()
        return {
            "answer": answer,
            "trace": trace,
            "seconds": round(time.perf_counter() - started, 3),
        }

    # Ran out of steps
    return {
        "answer": "MAX_STEPS_REACHED",
        "trace": trace,
        "reason": f"exceeded {MAX_STEPS} steps",
    }


if __name__ == "__main__":
    queries = [
        ("What is in ticket 42?", 1),
        ("Find the runbook for someone who cannot sign in.", 1),
        ("What's the best restaurant near the office?", 1),
    ]
    for q, tid in queries:
        print(f"\n=== {q} (tenant {tid}) ===")
        r = run(q, tenant_id=tid, verbose=True)
        print(json.dumps(r, indent=2))