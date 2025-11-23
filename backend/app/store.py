# store.py
import json
import os
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(__file__)
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(QUESTIONS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_questions(domain: str, level: str) -> List[Dict[str, Any]]:
    """
    Load questions for domain and level. Expects files like questions/<domain>.json
    File schema: { "domain": "...", "levels": { "entry": [...], "medium": [...], "senior": [...] } }
    """
    path = os.path.join(QUESTIONS_DIR, f"{domain}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Questions file not found for domain: {domain}")
    data = json.load(open(path, "r", encoding="utf-8"))
    levels = data.get("levels", {})

    # Normal case: level exists
    if level in levels:
        return levels[level]

    # Prefer 'entry' as the default fallback for compatibility with main.py
    if "entry" in levels:
        return levels["entry"]

    # Fallback: flatten all levels into one list (preserving order)
    return [q for lvl in levels.values() for q in lvl]


def save_session(session_id: str, data: Dict[str, Any]) -> None:
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> Dict[str, Any]:
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError("Session not found")
    return json.load(open(path, "r", encoding="utf-8"))
