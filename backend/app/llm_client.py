# llm_client.py  -- AIMLAPI / OpenAI-compatible REST wrapper
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
from typing import Optional
import requests

# Configuration via env vars
AIMLAPI_KEY = os.getenv("AIMLAPI_KEY")
AIML_MODEL = os.getenv("AIML_MODEL")
AIMLAPI_BASE = os.getenv("AIMLAPI_BASE")
REQUEST_TIMEOUT = int(os.getenv("AIML_REQ_TIMEOUT", "30"))
RETRY_ATTEMPTS = int(os.getenv("AIML_RETRIES", "1"))

HEADERS = {"Authorization": f"Bearer {AIMLAPI_KEY}"} if AIMLAPI_KEY else {}

# endpoint for chat-completions (OpenAI-compatible)
CHAT_URL = f"{AIMLAPI_BASE.rstrip('/')}/chat/completions"

async def call_llm(prompt: str, max_tokens: int = 150, temperature: float = 0.2) -> str:
    """
    Async wrapper to call AIMLAPI's OpenAI-compatible chat completions endpoint.
    Returns the assistant text or a fallback string on error.
    """
    if not AIMLAPI_KEY:
        await asyncio.sleep(0.06)
        return "(LLM fallback - AIMLAPI_KEY missing) " + prompt[:400].replace("\n", " ")

    payload = {
        "model": AIML_MODEL,
        "messages": [
            {"role": "system", "content": "You are an interviewer assistant that asks concise probing follow-up questions."},
            {"role": "user",   "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        # optionally: "stream": True
    }

    loop = asyncio.get_event_loop()

    def sync_call():
        last_exc = None
        for attempt in range(RETRY_ATTEMPTS + 1):
            try:
                resp = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    body = resp.json()
                    # OpenAI shape: body['choices'][0]['message']['content']
                    try:
                        choice = body.get("choices", [])[0]
                        # handle both 'message' and legacy 'text'
                        if isinstance(choice, dict) and "message" in choice:
                            return choice["message"].get("content", "").strip()
                        if "text" in choice:
                            return choice["text"].strip()
                    except Exception:
                        pass
                    # fallback: stringify whole body
                    return str(body)
                else:
                    # transient (429/503) or unrecoverable -> raise to allow retries or final fallback
                    if resp.status_code in (429, 503):
                        import time
                        time.sleep(1 + attempt * 1.5)
                        last_exc = RuntimeError(f"Transient {resp.status_code}: {resp.text}")
                        continue
                    # unrecoverable
                    resp.raise_for_status()
            except Exception as e:
                last_exc = e
                import time
                time.sleep(0.5 + attempt * 0.5)
                continue
        raise last_exc or RuntimeError("Unknown AIMLAPI inference error")

    try:
        text = await loop.run_in_executor(None, sync_call)
        return text if isinstance(text, str) else str(text)
    except Exception as e:
        # log for debugging; don't expose stacktraces to clients
        print("AIMLAPI inference error:", e)
        await asyncio.sleep(0.08)
        return "(LLM fallback) " + prompt[:400].replace("\n", " ")
