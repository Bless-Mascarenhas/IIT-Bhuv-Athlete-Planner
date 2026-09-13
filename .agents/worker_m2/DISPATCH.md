## 2026-09-13T10:06:00Z
You are the Worker for Milestone 2: AI Intent Router (R2).
Your working directory is `d:\IIT-Bhuv\.agents\worker_m2`.
You MUST read the authoritative user request at `d:\IIT-Bhuv\.agents\ORIGINAL_REQUEST.md`.
Read the master project scope at `d:\IIT-Bhuv\.agents\orchestrator_1\PROJECT.md`.
Read the survey blueprint at `d:\IIT-Bhuv\.agents\explorer_survey_3\handoff.md`.
Read the acceptance test contract at `d:\IIT-Bhuv\tests\test_r2_intent.py`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership:
You exclusively create/modify:
- `backend/intent_router.py`
- `backend/main.py` (integrate `/api/chat` route or include router)

Your Tasks:
1. Build `backend/intent_router.py`:
   - Classifies user messages into three distinct intents:
     1. `Update Calendar`: For upcoming matches, games, trainings, schedule changes (e.g. "I have a match tomorrow", "game on Saturday").
        - Autonomously extracts event details (`event_type`: 'match' or 'training', `event_date`: resolves date relative to today like tomorrow, in YYYY-MM-DD, `duration_minutes`: 90 or 60).
        - Autonomously modifies the SQLite database by inserting the record into `events` table (`INSERT INTO events (athlete_id, event_date, event_type, duration_minutes) VALUES (?, ?, ?, ?)`).
        - Returns `{ "intent": "Update Calendar", "response": "...", "action_taken": "calendar_updated", "event": { ... } }`.
     2. `Update Plan`: For fatigue, soreness, injury, requesting lighter/heavier sessions (e.g. "My hamstrings are tight and I am feeling fatigued, please make today's workout lighter").
        - Updates today's plan/rpe in `training_plans` or registers recovery constraint. Does NOT modify `events` table.
        - Returns `{ "intent": "Update Plan", "response": "...", "action_taken": "plan_adjusted" }`.
     3. `General QA`: For training advice, nutrition, sleep questions (e.g. "What should I eat before my match?").
        - Generates sports science coaching guidance. Does NOT modify database.
        - Returns `{ "intent": "General QA", "response": "..." }`.
   - Dual-engine architecture:
     - Groq LLM primary if `GROQ_API_KEY` is present and valid.
     - Deterministic rule/regex-based intent router fallback that executes flawlessly in offline/CI environments without API keys or network calls.
   - Robust input handling: handles empty strings, whitespace, safe parameterized SQL queries preventing SQL injection.
2. Integrate with `backend/main.py`:
   - Implement `POST /api/chat` accepting `{ "athlete_id": Optional[int] = 1, "message": str, "history": Optional[list] = [] }`.
   - Delegates to `intent_router.process_chat(athlete_id, message, history)`.
   - Returns `{ "status": "success", "intent": ..., "response": ..., ... }`.
3. Verification:
   - Run `python -m unittest tests/test_r2_intent.py` to confirm 100% test pass.
   - Ensure `test_r1_quests.py` also continues to pass (`python -m unittest tests/test_r1_quests.py tests/test_r2_intent.py`).
4. Deliverable:
   - Write `d:\IIT-Bhuv\.agents\worker_m2\handoff.md` with implementation details, exact intent classification logic, autonomous DB action details, and test outputs.
   - Maintain `progress.md` in your directory. When finished, send message to parent.

## 2026-09-13T10:11:05Z
**Context**: Server restart 5 recovery - Finalize Milestone 2 (AI Intent Router)
**Content**: `backend/intent_router.py` is completed!
Now wire `POST /api/chat` in `backend/main.py`:

```python
from intent_router import process_chat

class ChatMessageRequest(BaseModel):
    athlete_id: Optional[int] = 1
    message: str
    history: Optional[List[dict]] = []

@app.post("/api/chat")
def chat_endpoint(payload: ChatMessageRequest):
    """AI Intent Router endpoint: classifies chat and executes autonomous DB updates."""
    try:
        result = process_chat(
            athlete_id=payload.athlete_id or 1,
            message=payload.message,
            history=payload.history or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Then run:
`python -m unittest tests/test_r2_intent.py`
Verify that all tests pass, write your handoff report to `d:\IIT-Bhuv\.agents\worker_m2\handoff.md`, and report completion.
**Action**: Add the route, run the tests, and write handoff.md now.
