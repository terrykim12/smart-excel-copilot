import os, json, requests, subprocess, shutil
from .intent_schema import Intent

MODEL = os.getenv("SEC_LLM_MODEL", "qwen2.5:3b-instruct")  # ← 여기서 교체

SYS = (
  "You are a strict JSON planner for Excel. "
  "Convert the user's Korean request into JSON intent with keys: "
  "rows[], columns[], values[(col,agg)], filters{col:[vals]}, chart('bar|line|pie'). "
  "Only output valid JSON. No extra text."
)

def _ollama_api(prompt: str, *, fmt_json=True, temperature=0, seed=42, timeout=20):
    payload = {
        "model": MODEL,
        "prompt": f"{SYS}\nUSER:{prompt}\nJSON:",
        "options": {"temperature": temperature, "seed": seed, "num_ctx": 4096},
    }
    if fmt_json:
        payload["format"] = "json"  # ← JSON 강제 (Ollama 지원)
    r = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=timeout)
    r.raise_for_status()
    resp = r.json().get("response", "")
    return json.loads(resp)

def _via_ollama_cli(text: str) -> dict:
    if not shutil.which("ollama"): raise RuntimeError("ollama not found")
    prompt = f"{SYS}\nUSER:{text}\nJSON:"
    p = subprocess.run(["ollama","run",MODEL,prompt], capture_output=True, text=True, timeout=30)
    p.check_returncode()
    return json.loads(p.stdout.strip())

def parse_with_llm(text: str, *, allowed_columns=None) -> Intent | None:
    try:
        hint = ""
        if allowed_columns:
            hint = f"\nColumns: {list(allowed_columns)}\n"
        try:
            data = _ollama_api(f"{hint}{text}")
        except Exception:
            data = _via_ollama_cli(f"{hint}{text}")
        return Intent.model_validate(data)
    except Exception:
        # CLI fallback 대비: 실패 시 None
        return None
