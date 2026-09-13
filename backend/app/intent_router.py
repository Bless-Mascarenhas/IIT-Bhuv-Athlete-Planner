"""
Pace AI Intent Router (R2)

Classifies natural language athlete messages into three distinct intents:
1. 'Update Calendar': Autonomous match / training scheduling directly to SQLite 'events' table.
2. 'Update Plan': Autonomous fatigue / soreness / injury workload adaptation in SQLite 'training_plans'.
3. 'General QA': Evidence-based sports science coaching advice without database mutations.

Dual-Engine Architecture:
- Primary: Groq LLM with structured JSON output when GROQ_API_KEY is present and valid.
- Deterministic Fallback: High-precision regex / NLP pattern matching and date resolution
  for offline, CI, and test environments.
"""

import os
import re
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from .database import get_db_connection

logger = logging.getLogger("intent_router")

# --- Intent Constants ---
INTENT_UPDATE_CALENDAR = "Update Calendar"
INTENT_UPDATE_PLAN = "Update Plan"
INTENT_GENERAL_QA = "General QA"

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# --- Sports Science Knowledge Base for Deterministic General QA ---
SPORTS_SCIENCE_KNOWLEDGE: List[Tuple[List[str], str]] = [
    (
        ["glycogen", "carb", "carbs", "carbohydrate", "eat", "meal", "food", "pre-match", "pre match", "fuel"],
        "For optimal glycogen storage before a high-intensity match, consume a high-carbohydrate meal "
        "(1-4g carbohydrates per kg body weight) 3 to 4 hours prior to kickoff. Focus on low-glycemic, "
        "easily digestible complex carbohydrates like oatmeal, brown rice, sweet potatoes, or pasta accompanied "
        "by moderate lean protein. In the final 60 minutes, ingest a fast-acting carb source (such as a banana "
        "or sports gel) and 300-500ml of water with electrolytes to prime blood glucose and cellular hydration."
    ),
    (
        ["recovery", "post-match", "post match", "after match", "window", "protein", "soreness recovery"],
        "Post-match recovery centers on the 45-minute metabolic window: ingest a 3:1 or 4:1 ratio of carbohydrates "
        "to high-biological-value protein (e.g., 20-30g whey protein with 60-80g maltodextrin or fruit) to rapidly "
        "stimulate muscle protein synthesis and replenish glycogen. Rehydrate by drinking 150% of fluid lost through sweat "
        "along with sodium, and utilize contrast hydrotherapy or low-intensity active recovery to accelerate lactate clearance."
    ),
    (
        ["acwr", "workload", "acute", "chronic", "injury risk", "ratio", "spike"],
        "The Acute:Chronic Workload Ratio (ACWR) evaluates short-term fatigue (7-day acute workload) against long-term "
        "fitness preparation (28-day chronic workload). The optimal 'sweet spot' is 0.8 to 1.3, where injury risk is lowest. "
        "When ACWR exceeds 1.5 ('danger zone'), the relative injury risk rises significantly due to unaccustomed physiological "
        "strain. Pace automatically adjusts your daily quest targets when an upcoming match threatens to spike your ACWR."
    ),
    (
        ["sleep", "rest", "circadian", "hgh", "rem", "deep sleep", "fatigue recovery"],
        "Sleep is the foundational pillar of physiological restoration. Elite athletes require 8-10 hours of sleep per night. "
        "Slow-wave deep sleep triggers Human Growth Hormone (HGH) release necessary for cellular repair and myofibrillar rebuilding, "
        "while REM sleep consolidates tactical memory and neuromuscular coordination. Maintain a dark, cool room (18°C/65°F), "
        "avoid blue spectrum light 90 minutes before bed, and cease caffeine intake 8 hours prior to sleep."
    ),
    (
        ["hydration", "water", "fluid", "cramp", "cramping", "electrolytes", "sodium"],
        "Dehydration of just 2% body mass impairs aerobic capacity, cognitive decision-making, and sprint velocity. "
        "Consume 5-7ml fluid per kg body weight 4 hours before training. During sessions exceeding 60 minutes in heat, consume "
        "150-250ml of a 6-8% carbohydrate-electrolyte solution every 15-20 minutes, targeting 300-600mg sodium per hour to "
        "prevent hyponatremia and neuromuscular cramping."
    ),
    (
        ["hamstring", "knee", "quad", "calf", "groin", "achilles", "tendon", "injury prevention"],
        "Soft-tissue resilience requires progressive eccentric loading. For hamstrings, Nordic curls and Romanian deadlifts "
        "lengthen the muscle fascicle, protecting against high-speed sprint strain. If experiencing acute tightness without sharp "
        "pain, prioritize dynamic active mobility and low-load isometric holds over aggressive static stretching, which can "
        "destabilize an already fatigued motor unit."
    ),
    (
        ["taper", "tapering", "pre-game", "pre match day"],
        "Effective tapering involves reducing training volume by 40-60% over 3-5 days while maintaining training intensity. "
        "This maintains neuromuscular neuromuscular sharpness while allowing physiological glycogen supercompensation and "
        "systemic fatigue dissipation before competition."
    ),
]

DEFAULT_COACHING_RESPONSE = (
    "As your Pace sports science performance coach, I recommend structuring your training around periodization: "
    "balance high-intensity stimulus with dedicated active recovery, prioritize balanced macro-nutrient timing and sleep hygiene, "
    "and monitor your daily ACWR to stay safely within the optimal performance envelope."
)


# --- Deterministic Entity Extraction & Date Resolution ---

def resolve_relative_date(text: str, base_date: Optional[date] = None) -> date:
    """
    Parses relative or absolute date mentions from text safely.
    Handles 'tomorrow', 'today', 'in X days', weekdays, and ISO formats.
    """
    base = base_date or date.today()
    text_lower = text.lower()

    # 1. tomorrow
    if "tomorrow" in text_lower:
        return base + timedelta(days=1)

    # 2. day after tomorrow
    if "day after tomorrow" in text_lower:
        return base + timedelta(days=2)

    # 3. today / tonight
    if re.search(r"\b(?:today|tonight)\b", text_lower):
        return base

    # 4. in X days
    match_in_days = re.search(r"\bin\s+(\d+)\s+days?\b", text_lower)
    if match_in_days:
        return base + timedelta(days=int(match_in_days.group(1)))

    # 5. Weekday names
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for day_name, day_num in weekdays.items():
        if re.search(rf"\b{day_name}\b", text_lower):
            current_day = base.weekday()
            days_ahead = (day_num - current_day) % 7
            if days_ahead == 0:
                days_ahead = 7  # If same day, assume next week's occurrence
            return base + timedelta(days=days_ahead)

    # 6. Explicit ISO YYYY-MM-DD
    iso_match = re.search(r"\b(20\d\d[-/]\d{1,2}[-/]\d{1,2})\b", text)
    if iso_match:
        try:
            clean_str = iso_match.group(1).replace("/", "-")
            parts = clean_str.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            pass

    # Default fallback for calendar event without specified date: tomorrow
    return base + timedelta(days=1)


def extract_event_type(text: str) -> str:
    """Extracts event type ('match' vs 'training') from text."""
    text_lower = text.lower()
    training_keywords = ["training", "practice", "workout", "drill", "session", "scrimmage", "gym"]
    match_keywords = ["match", "game", "fixture", "tournament", "cup", "friendly", "trial", "trials", "competition", "playoff"]

    for kw in match_keywords:
        if re.search(rf"\b{kw}\b", text_lower):
            return "match"

    for kw in training_keywords:
        if re.search(rf"\b{kw}\b", text_lower):
            return "training"

    return "match"


def extract_duration_minutes(text: str, event_type: str) -> int:
    """Extracts duration in minutes or defaults based on event type (90 for match, 60 for training)."""
    text_lower = text.lower()
    min_match = re.search(r"(\d+)\s*(?:mins?|minutes?)", text_lower)
    if min_match:
        val = int(min_match.group(1))
        return max(15, min(240, val))

    hr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr)", text_lower)
    if hr_match:
        val = int(float(hr_match.group(1)) * 60)
        return max(15, min(240, val))

    return 90 if event_type == "match" else 60


def get_sports_science_qa_response(message: str) -> str:
    """Returns accurate coaching advice from knowledge base matching keywords."""
    msg_lower = message.lower()
    for keywords, response in SPORTS_SCIENCE_KNOWLEDGE:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", msg_lower):
                return response
    return DEFAULT_COACHING_RESPONSE


# --- Intent Classification Logic ---

def classify_intent(message: str) -> str:
    """
    Deterministically classifies natural language text into one of three intents:
    - 'Update Calendar'
    - 'Update Plan'
    - 'General QA'
    """
    msg = message.strip()
    if not msg:
        return INTENT_GENERAL_QA

    msg_lower = msg.lower()

    # 1. Question / General QA patterns (e.g. "What should I eat before a match...")
    qa_question_patterns = [
        r"^(?:what|how|why|when|where|can\s+i|should\s+i|could\s+i|is\s+it|tell\s+me|explain)\b",
        r"\b(?:what\s+should\s+i\s+eat|what\s+to\s+eat|nutrition|glycogen|hydration|electrolytes|supplements)\b",
        r"\b(?:how\s+much\s+sleep|sleep\s+quality|sleep\s+needed|rem\s+sleep)\b",
        r"\b(?:what\s+is\s+acwr|explain\s+acwr|workload\s+ratio|acute\s+chronic)\b",
        r"\b(?:advice|tips|recommendations?|best\s+way\s+to)\b",
    ]
    is_explicit_qa = any(re.search(p, msg_lower) for p in qa_question_patterns)

    # 2. Calendar update patterns
    calendar_patterns = [
        r"\b(?:have|got|having|schedule|scheduled|add|book|play|playing)\s+(?:a\s+)?(?:match|game|trial|trials|practice|training|fixture|tournament|cup|friendly)\b",
        r"\b(?:match|game|fixture|tournament|cup|trial|trials|friendly)\s+(?:is\s+)?(?:tomorrow|today|tonight|on\s+\w+|next\s+\w+|in\s+\d+\s+days)\b",
        r"\b(?:practice|training)\s+(?:is\s+)?(?:tomorrow|today|tonight|on\s+\w+|next\s+\w+|in\s+\d+\s+days)\b",
        r"\bi\s+have\s+a\s+match\b",
        r"\bgame\s+on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bmatch\s+on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bhave\s+(?:a\s+)?(?:match|game|training)\b",
    ]
    is_calendar = any(re.search(p, msg_lower) for p in calendar_patterns)

    # 3. Plan update patterns
    plan_patterns = [
        r"\b(?:fatigue|fatigued|tired|exhausted|exhaustion|drained|weary|burnout|burned\s+out)\b",
        r"\b(?:sore|soreness|tight|tightness|stiff|stiffness|cramp|cramping|cramps)\b",
        r"\b(?:hurt|hurts|pain|painful|ache|aching|strained|strain|sprain|sprained|pulled|tweak|tweaked|injury|injured)\b",
        r"\b(?:sick|fever|ill|illness|nausea|nauseous|headache|flu|cold)\b",
        r"\b(?:lighter|easier|easy|scale\s+back|dial\s+back|reduce\s+load|lower\s+intensity|take\s+it\s+easy|rest\s+day|skip\s+today|skip\s+workout)\b",
        r"\b(?:make\s+today(?:'s)?\s+workout|adjust\s+today|change\s+today|modify\s+today|update\s+today|adapt\s+today)\b",
        r"\b(?:feeling\s+great|fresh|ramp\s+up|harder|push\s+harder|increase\s+intensity)\b",
        r"\b(?:hamstrings?|quads?|cal(?:f|ves)|knees?|ankles?|groin|glutes?|lower\s+back|hip|hips)\b.*(?:tight|sore|hurt|pain|tweak)",
        r"(?:tight|sore|hurt|pain|tweak).*\b(?:hamstrings?|quads?|cal(?:f|ves)|knees?|ankles?|groin|glutes?|lower\s+back|hip|hips)\b"
    ]
    is_plan = any(re.search(p, msg_lower) for p in plan_patterns)

    # Disambiguation:
    # If QA question pattern matched and message is not an explicit declaration like "I have a match tomorrow"
    if is_explicit_qa and not re.search(r"\bi\s+(?:have|got)\s+a\s+match\b", msg_lower):
        return INTENT_GENERAL_QA

    if is_calendar:
        return INTENT_UPDATE_CALENDAR

    if is_plan:
        return INTENT_UPDATE_PLAN

    return INTENT_GENERAL_QA


# --- Autonomous Database Modification Executors ---

def execute_update_calendar(
    athlete_id: int,
    message: str,
    event_date_str: Optional[str] = None,
    event_type: Optional[str] = None,
    duration_minutes: Optional[int] = None
) -> dict:
    """
    Autonomously modifies the SQLite 'events' table by inserting the new match or training event.
    Guarantees SQL injection safety via parameterized queries.
    """
    resolved_date = event_date_str if event_date_str else resolve_relative_date(message).strftime("%Y-%m-%d")
    resolved_type = event_type if event_type else extract_event_type(message)
    resolved_duration = duration_minutes if duration_minutes else extract_duration_minutes(message, resolved_type)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parameterized query protects against SQL injection
    cursor.execute(
        """
        INSERT INTO events (athlete_id, event_date, event_type, duration_minutes)
        VALUES (?, ?, ?, ?)
        """,
        (athlete_id, resolved_date, resolved_type, resolved_duration)
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    response_text = (
        f"Scheduled your {resolved_type} on {resolved_date} ({resolved_duration} mins). "
        f"Your training plan and ACWR forecast will autonomously adapt to taper appropriately."
    )

    return {
        "status": "success",
        "intent": INTENT_UPDATE_CALENDAR,
        "response": response_text,
        "reply": response_text,
        "action_taken": "calendar_updated",
        "event": {
            "id": event_id,
            "athlete_id": athlete_id,
            "event_date": resolved_date,
            "event_type": resolved_type,
            "duration_minutes": resolved_duration
        }
    }


def execute_update_plan(athlete_id: int, message: str) -> dict:
    """
    Autonomously adjusts today's training plan in SQLite 'training_plans' based on athlete feedback.
    Does NOT modify 'events' table.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()

    msg_lower = message.lower()
    is_harder = any(k in msg_lower for k in ["harder", "fresh", "ramp up", "feeling great", "increase intensity"])

    new_intensity = "High" if is_harder else "Recovery"
    new_rpe = 8 if is_harder else 2
    new_title = "High-Intensity Performance Session" if is_harder else "Active Recovery & Mobility Quest"
    new_desc = (
        "Sport-specific drills, threshold intervals, and reactive agility."
        if is_harder else
        "Gentle foam rolling, hamstring and hip mobility, light dynamic stretching, and rehydration."
    )
    revision_reason = f"Athlete feedback: {message[:100]}"

    cursor.execute(
        "SELECT id, duration_minutes FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
        (athlete_id, today_str)
    )
    plans = cursor.fetchall()

    if plans:
        for p in plans:
            dur = p['duration_minutes'] or 30
            target_load = float(new_rpe * dur)
            cursor.execute(
                """
                UPDATE training_plans
                SET intensity_category = ?, target_rpe = ?, target_load = ?,
                    status = 'revised', revision_reason = ?, quest_title = ?, session_description = ?
                WHERE id = ?
                """,
                (new_intensity, new_rpe, target_load, revision_reason, new_title, new_desc, p['id'])
            )
    else:
        cursor.execute(
            """
            INSERT INTO training_plans
            (athlete_id, plan_date, intensity_category, target_load, status, revision_reason,
             quest_title, session_description, task_type, target_rpe, duration_minutes, is_completed)
            VALUES (?, ?, ?, ?, 'revised', ?, ?, ?, 'recovery', ?, 30, 0)
            """,
            (athlete_id, today_str, new_intensity, float(new_rpe * 30), revision_reason, new_title, new_desc, new_rpe)
        )

    conn.commit()
    conn.close()

    adjustment_desc = "intensified" if is_harder else "downgraded to active recovery"
    response_text = (
        f"Understood. I have updated today's workout to an {new_intensity.lower()} session "
        f"({adjustment_desc}) to protect your readiness and prevent overreaching."
    )

    return {
        "status": "success",
        "intent": INTENT_UPDATE_PLAN,
        "response": response_text,
        "reply": response_text,
        "action_taken": "plan_adjusted"
    }


def execute_general_qa(athlete_id: int, message: str, custom_response: Optional[str] = None) -> dict:
    """
    Returns sports science coaching feedback without modifying the database.
    """
    reply_text = custom_response if custom_response else get_sports_science_qa_response(message)
    return {
        "status": "success",
        "intent": INTENT_GENERAL_QA,
        "response": reply_text,
        "reply": reply_text
    }


# --- Groq LLM Primary Engine ---

def call_groq_llm_intent_router(athlete_id: int, message: str, history: Optional[list] = None) -> Optional[dict]:
    """
    Invokes Groq LLM to classify intent and extract parameters using structured JSON output.
    Returns processed response dictionary, or None if LLM call fails.
    """
    try:
        from groq import Groq
    except ImportError:
        logger.warning("Groq SDK not installed, using deterministic fallback.")
        return None

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("gsk_test_fixture"):
        return None

    try:
        client = Groq(api_key=api_key)
        today_str = date.today().strftime("%Y-%m-%d")

        system_prompt = f"""You are the AI Performance Coach & Intent Router for Pace, an autonomous sports performance planner.
Current Date: {today_str}

Analyze the athlete's message and classify it into EXACTLY ONE of three intents:
1. "Update Calendar": Scheduling or reporting upcoming matches, games, practices, competitions, or schedule changes.
2. "Update Plan": Athlete reporting fatigue, soreness, pain, injury, illness, or requesting workout adjustments (lighter or heavier).
3. "General QA": Asking coaching, physiological, nutritional, hydration, or sleep advice.

Return ONLY valid JSON matching this schema:
{{
  "intent": "Update Calendar" | "Update Plan" | "General QA",
  "event_type": "match" | "training" | null,
  "event_date": "YYYY-MM-DD" | null,
  "duration_minutes": int | null,
  "response": "Sports science coaching response to user"
}}"""

        chat_messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                if isinstance(h, dict) and "role" in h and "content" in h:
                    chat_messages.append({"role": h["role"], "content": h["content"]})
        chat_messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=chat_messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        data = json.loads(content)
        intent = data.get("intent", INTENT_GENERAL_QA)

        if intent == INTENT_UPDATE_CALENDAR:
            return execute_update_calendar(
                athlete_id=athlete_id,
                message=message,
                event_date_str=data.get("event_date"),
                event_type=data.get("event_type"),
                duration_minutes=data.get("duration_minutes")
            )
        elif intent == INTENT_UPDATE_PLAN:
            return execute_update_plan(athlete_id=athlete_id, message=message)
        else:
            qa_reply = data.get("response") or get_sports_science_qa_response(message)
            return execute_general_qa(athlete_id=athlete_id, message=message, custom_response=qa_reply)

    except Exception as e:
        logger.warning(f"Groq LLM intent router failed ({type(e).__name__}: {e}). Using deterministic fallback.")
        return None


# --- Master Entry Point ---

def process_chat(athlete_id: int = 1, message: str = "", history: Optional[list] = None) -> dict:
    """
    Main entry point for processing chat messages:
    1. Validates input.
    2. Attempts Groq LLM if API key is present and valid.
    3. Falls back to deterministic rule/regex-based router with autonomous DB execution.
    """
    clean_msg = message.strip() if message else ""
    if not clean_msg:
        return {
            "status": "success",
            "intent": INTENT_GENERAL_QA,
            "response": (
                "Hello! I am Pace, your AI performance coach. Ask me sports science questions, "
                "schedule upcoming matches (e.g. 'I have a match tomorrow'), or let me know if "
                "you need today's workout adjusted."
            ),
            "reply": (
                "Hello! I am Pace, your AI performance coach. Ask me sports science questions, "
                "schedule upcoming matches (e.g. 'I have a match tomorrow'), or let me know if "
                "you need today's workout adjusted."
            )
        }

    # Primary: Groq LLM
    llm_result = call_groq_llm_intent_router(athlete_id, clean_msg, history)
    if llm_result is not None:
        return llm_result

    # Fallback: Deterministic Intent Router
    intent = classify_intent(clean_msg)
    if intent == INTENT_UPDATE_CALENDAR:
        return execute_update_calendar(athlete_id, clean_msg)
    elif intent == INTENT_UPDATE_PLAN:
        return execute_update_plan(athlete_id, clean_msg)
    else:
        return execute_general_qa(athlete_id, clean_msg)
