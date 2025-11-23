# main.py (adaptive answer flow integrated)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import uuid, asyncio, re, random

from .store import load_questions, save_session, load_session
from .llm_client import call_llm
from .policy import choose_next_question  # policy must be present

app = FastAPI(title="Interview Agent MVP - Adaptive")
from fastapi.middleware.cors import CORSMiddleware

# allow local frontend
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SHORT_WORDS_THRESHOLD = 25

# --- Request models ---
class StartRequest(BaseModel):
    role: str
    level: str = "entry"   # default level name (entry/medium/senior)

class AnswerRequest(BaseModel):
    session_id: str
    answer: str = ""
    hint: bool = False
    skip: bool = False

# --- Utilities ---
def contains_number(text: str) -> bool:
    return bool(re.search(r"\d", text))

def contains_any(text: str, words):
    t = text.lower()
    return any(w.lower() in t for w in words)

def heuristic_followup(answer: str, qmeta: Dict[str, Any]) -> str:
    competency = qmeta.get("competency","").lower()
    if len(answer.split()) < SHORT_WORDS_THRESHOLD:
        return "Can you provide more details and any concrete metrics or results?"
    if competency == "behavioral" and not contains_number(answer):
        return "Could you share the measurable outcome or result (numbers, improvement, time)?"
    if competency == "technical" and not contains_any(answer, ["tradeoff","trade-offs","complexity","latency","space","time","scalab"]):
        return "What tradeoffs or complexity considerations did you evaluate for this approach?"
    return "Can you clarify any assumptions you made?"

# --- Endpoints ---
@app.post("/start_interview")
async def start_interview(req: StartRequest):
    try:
        questions = load_questions(req.role, req.level)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Role not found")
    if not questions:
        raise HTTPException(status_code=500, detail="No questions found for this role/level")

    # shuffle pool to avoid fixed order
    random.shuffle(questions)

    session_id = str(uuid.uuid4())[:8]
    session = {
        "id": session_id,
        "role": req.role,
        "level": req.level,
        "questions": questions,
        "index": 0,
        "history": [],            # list of {id, question, answer, tags, parent_id, score}
        "scores": [],             # list of {index, score}
        "max_questions": 10,      # safety cap, changeable
        "followups_count": {}     # optionally track followup counts per question id
    }
    save_session(session_id, session)
    first = questions[0]
    return {"session_id": session_id, "question": first["question"], "meta": first}

@app.post("/answer")
async def answer(req: AnswerRequest):
    # load session
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    idx = session.get("index", 0)
    questions = session.get("questions", [])
    # if interview already exhausted
    if len(session.get("history", [])) >= session.get("max_questions", 10):
        return {"done": True, "message": "Max questions reached. Please request feedback."}

    if idx >= len(questions):
        return {"done": True, "message": "No more questions"}

    qmeta = questions[idx]

    # HINT: return example answer, do not advance
    if req.hint:
        example = qmeta.get("example_answer", "Try to structure with Situation, Action, Result and include numbers if possible.")
        return {"follow_up": f"(Hint) Example: {example}", "auto_score": None, "next_question": qmeta["question"], "next_meta": qmeta, "done": False}

    # SKIP: record skip and advance sequentially
    if req.skip:
        session["history"].append({
            "id": qmeta.get("id"),
            "question": qmeta.get("question"),
            "answer": "(skipped)",
            "tags": qmeta.get("tags", []),
            "parent_id": None,
            "score": 0
        })
        session["scores"].append({"index": idx, "score": 0})
        # advance index safely to next unseen
        next_idx = idx + 1
        # find next unseen index
        while next_idx < len(questions) and any(h.get("id")==questions[next_idx].get("id") for h in session["history"]):
            next_idx += 1
        session["index"] = next_idx if next_idx < len(questions) else len(questions)
        save_session(session["id"], session)
        if session["index"] < len(questions):
            nxt = questions[session["index"]]
            return {"follow_up": "Skipped. Moving to next question.", "auto_score": 0, "next_question": nxt["question"], "next_meta": nxt, "done": False}
        else:
            return {"follow_up": "Skipped. Interview complete.", "auto_score": 0, "next_question": None, "next_meta": None, "done": True}

    # NORMAL ANSWER FLOW
    # record answer in history (tentative)
    hist_entry = {
        "id": qmeta.get("id"),
        "question": qmeta.get("question"),
        "answer": req.answer,
        "tags": qmeta.get("tags", []),
        "parent_id": None,
        "score": None
    }
    session["history"].append(hist_entry)

    # heuristic follow-up
    follow = heuristic_followup(req.answer, qmeta)

    # try to refine follow-up with LLM (best-effort)
    try:
        llm_prompt = (
            f"You are an interviewer. Role: {session['role']} Level: {session['level']}\n"
            f"Question: {qmeta['question']}\nCandidate answer: {req.answer}\n"
            "Produce one concise probing follow-up question to dig deeper."
        )
        llm_text = await call_llm(llm_prompt)
        # prefer heuristic + LLM supplement
        follow = follow + " | LM: " + llm_text
    except Exception:
        pass

    # simple auto-scoring (keywords + length)
    keywords = qmeta.get("keywords", [])
    keyword_hits = sum(1 for k in keywords if k.lower() in req.answer.lower())
    score = 1 + min(3, keyword_hits)
    if len(req.answer.split()) > 40:
        score += 1
    score = min(5, score)

    # update history score
    session["history"][-1]["score"] = score
    session["scores"].append({"index": idx, "score": score})

    # optionally mark parent_id if this is a follow-up (detect last parent)
    # we consider the previous question as parent if it has the same id (rare) or simply set parent for probing
    parent_id = qmeta.get("id")
    session["history"][-1]["parent_id"] = parent_id

    # Adaptive selection: use policy to choose next question
    next_qmeta = None
    try:
        chosen = choose_next_question(session, req.answer, qmeta)
        if chosen:
            # find chosen index in session.questions
            for i, q in enumerate(session["questions"]):
                if q.get("id") == chosen.get("id"):
                    session["index"] = i
                    next_qmeta = q
                    break
        else:
            # fallback sequential next unseen
            next_idx = idx + 1
            while next_idx < len(questions) and any(h.get("id")==questions[next_idx].get("id") for h in session["history"]):
                next_idx += 1
            session["index"] = next_idx
            if session["index"] < len(questions):
                next_qmeta = session["questions"][session["index"]]
    except Exception:
        # safe fallback: sequential
        next_idx = idx + 1
        while next_idx < len(questions) and any(h.get("id")==questions[next_idx].get("id") for h in session["history"]):
            next_idx += 1
        session["index"] = next_idx
        if session["index"] < len(questions):
            next_qmeta = session["questions"][session["index"]]

    # persist session
    save_session(session["id"], session)

    done_flag = len(session.get("history", [])) >= session.get("max_questions", 10) or session["index"] >= len(session["questions"])
    # prepare response
    if next_qmeta and not done_flag:
        return {"follow_up": follow, "auto_score": score, "next_question": next_qmeta["question"], "next_meta": next_qmeta, "done": False}
    else:
        return {"follow_up": follow, "auto_score": score, "next_question": None, "next_meta": None, "done": True}

@app.get("/feedback/{session_id}")
async def feedback(session_id: str):
    try:
        session = load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    scores = [s["score"] for s in session.get("scores", [])] or [0]
    avg = sum(scores) / len(scores)
    strengths = []
    improvements = []
    for i, h in enumerate(session.get("history", [])):
        s = h.get("score", 0)
        if s >= 4:
            strengths.append({"q": h["question"], "example": h["answer"][:240]})
        else:
            improvements.append({"q": h["question"], "advice": "Be more specific; include metrics and structure."})

    # LLM summary (best-effort)
    try:
        prompt = (
            f"Provide a concise feedback report for a candidate who did an interview for role {session['role']} "
            f"at level {session['level']}. Average score {avg:.2f}. Provide 3 strengths and 3 improvements."
        )
        llm_report = await call_llm(prompt)
    except Exception:
        llm_report = "(LLM unavailable)"

    return {"avg_score": avg, "strengths": strengths[:3], "improvements": improvements[:3], "llm_report": llm_report}
