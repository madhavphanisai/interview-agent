# policy.py
import random
from typing import Dict, List, Any

SHORT_WORDS_THRESHOLD = 25
MAX_FOLLOWUPS_PER_Q = 2

def answer_signals(answer: str, qmeta: Dict[str, Any]) -> Dict[str, Any]:
    words = len(answer.split())
    keywords = qmeta.get("keywords", [])
    keyword_hits = sum(1 for k in keywords if k.lower() in answer.lower())
    has_numbers = any(ch.isdigit() for ch in answer)
    shallow = words < SHORT_WORDS_THRESHOLD
    return {
        "words": words,
        "keyword_hits": keyword_hits,
        "has_numbers": has_numbers,
        "shallow": shallow,
    }

def _asked_ids(session: Dict[str,Any]) -> set:
    return set(h.get("id") for h in session.get("history", []) if h.get("id"))

def shortlist_candidates(session: Dict[str, Any], current_qmeta: Dict[str,Any], signals: Dict[str,Any]) -> List[Dict[str,Any]]:
    """
    Build up to N candidate questions from the session pool.
    Priority:
      - explicit followups
      - probes for shallow answers (same tags)
      - remediation when keyword_hits==0 (same tags)
      - escalate difficulty when keyword_hits high
      - fallback unseen questions to improve coverage
    """
    pool_all = session.get("questions", [])
    asked = _asked_ids(session)
    candidates = []

    # 1) explicit followups referenced by current question
    if current_qmeta:
        follow_ids = current_qmeta.get("followup_ids") or current_qmeta.get("followup_for") or []
        for q in pool_all:
            if q.get("id") in follow_ids and q.get("id") not in asked:
                candidates.append(q)

    # 2) shallow -> pick probes with shared tags and small difficulty
    if signals.get("shallow") and current_qmeta:
        tags = set(current_qmeta.get("tags", []))
        for q in pool_all:
            if q.get("id") not in asked and tags & set(q.get("tags", [])):
                candidates.append(q)

    # 3) remediation if keyword_hits == 0 -> pick questions covering same tags
    if signals.get("keyword_hits",0) == 0 and current_qmeta:
        tags = set(current_qmeta.get("tags", []))
        for q in pool_all:
            if q.get("id") not in asked and tags & set(q.get("tags", [])):
                candidates.append(q)

    # 4) escalate difficulty if candidate did well
    if signals.get("keyword_hits",0) >= 2 and current_qmeta:
        tags = set(current_qmeta.get("tags", []))
        harder = [q for q in pool_all if q.get("id") not in asked and q.get("difficulty",0) > current_qmeta.get("difficulty",0) and tags & set(q.get("tags", []))]
        candidates.extend(harder)

    # 5) fallback: unseen questions (prefer those with uncovered tags)
    if not candidates:
        covered = set()
        for h in session.get("history", []):
            covered.update(h.get("tags", []))
        unseen = [q for q in pool_all if q.get("id") not in asked]
        uncov = [q for q in unseen if any(t not in covered for t in q.get("tags", []))]
        candidates = uncov if uncov else unseen

    # dedupe preserving order
    seen = set(); out = []
    for q in candidates:
        if q.get("id") not in seen:
            out.append(q); seen.add(q.get("id"))
    return out[:6]

def choose_next_question(session: Dict[str,Any], answer: str, current_qmeta: Dict[str,Any]) -> Dict[str,Any]:
    """
    Return chosen question meta dict from session['questions'] or None.
    """
    signals = answer_signals(answer, current_qmeta or {})
    candidates = shortlist_candidates(session, current_qmeta, signals)
    if not candidates:
        return None

    # Safety: cap followups for current question
    if current_qmeta:
        qid = current_qmeta.get("id")
        followups_done = sum(1 for h in session.get("history",[]) if h.get("parent_id")==qid)
        if followups_done >= MAX_FOLLOWUPS_PER_Q:
            # avoid choosing another follow-up: filter candidates that are followups of this q
            candidates = [c for c in candidates if c.get("id") not in (current_qmeta.get("followup_ids") or [])]
            if not candidates:
                return None

    # weight selection: prefer same-tag + difficulty proximity
    weights = []
    for c in candidates:
        w = c.get("weight",1)
        # small boost if shares tags with current
        if current_qmeta and set(current_qmeta.get("tags", [])) & set(c.get("tags", [])):
            w += 1
        # prefer similar difficulty or slightly harder if candidate was strong
        diff = (c.get("difficulty",0) - (current_qmeta.get("difficulty",0) if current_qmeta else 0))
        if signals.get("keyword_hits",0) >= 2 and diff > 0:
            w += 1
        weights.append(max(1, w))

    # choose random by weight
    chosen = random.choices(candidates, weights=weights, k=1)[0]
    return chosen
