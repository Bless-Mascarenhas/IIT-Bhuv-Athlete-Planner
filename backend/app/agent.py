import os
import json
from datetime import datetime, timedelta
from groq import Groq
from .algorithm import evaluate_daily_constraints, get_db_connection

# Safely initialize Groq so missing or invalid GROQ_API_KEY never crashes import or runtime
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = None
if GROQ_API_KEY and GROQ_API_KEY.strip():
    try:
        client = Groq(api_key=GROQ_API_KEY.strip())
    except Exception as e:
        print(f"Warning: Failed to initialize Groq client: {e}")
        client = None

# Default to supported fast reasoning model
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_onboarding_response(conversation_history: list) -> str:
    """
    Grill Agent: Interviews the user to establish their baseline.
    Uses Groq LLM if available, with a deterministic sports-science fallback.
    """
    if client is not None:
        try:
            system_prompt = {
                "role": "system",
                "content": (
                    "You are an elite, no-nonsense Sports Performance Scientist. Your goal is to 'grill' "
                    "a new athlete to establish their baseline. Ask them about their specific team sport, "
                    "their typical training volume, their current fatigue levels, and any upcoming major matches. "
                    "Keep questions direct and professional. Ask one or two things at a time, not a massive list. "
                    "Once you have enough info (Sport, typical weekly hours, current fatigue 1-10), "
                    "thank them and end your message with the exact word 'PROFILE_COMPLETE'."
                )
            }
            messages = [system_prompt] + conversation_history
            response = client.chat.completions.create(
                messages=messages,
                model=MODEL,
                temperature=0.6,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API call failed: {e}. Falling back to deterministic onboarding.")

    # Deterministic sports-science interviewer fallback
    user_turns = [m for m in conversation_history if m.get("role") == "user"]
    turn_count = len(user_turns)
    if turn_count <= 1:
        return "Coach here. Let's dial in your baseline. What primary sport do you compete in, and how many hours per week do you typically train?"
    elif turn_count == 2:
        return "Understood. On a 1-10 scale, what is your current fatigue level, and how many hours of restorative sleep did you get last night?"
    else:
        return "Baseline metrics logged. We have configured your training load parameters and daily quest schedule. PROFILE_COMPLETE"


def generate_daily_quests(athlete_id: int, target_date_str: str, fatigue: int = None, sleep: int = None) -> dict:
    """
    1-Day Rolling Quests Generator.
    Evaluates sports-science constraints (ACWR, fatigue, sleep, pre/post-match rules)
    and produces 2-3 structured daily quests (Workout, Recovery/Mobility, Wellness/Nutrition).
    Uses Groq LLM if configured, falling back deterministically to athletic load guidelines.
    """
    # 1. Evaluate mathematical constraints
    constraints = evaluate_daily_constraints(athlete_id, target_date_str, fatigue, sleep)
    primary_tier = constraints['allowed_intensity'][-1] if constraints['allowed_intensity'] else 'Moderate'
    max_load_pct = constraints['max_load_percentage']

    # 2. Check for matches/events on this day
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT event_type, duration_minutes FROM events 
                      WHERE athlete_id=? AND event_date=?''', (athlete_id, target_date_str))
    day_event = cursor.fetchone()
    conn.close()

    event_info = f"{day_event['event_type']} ({day_event['duration_minutes']}m)" if day_event else "No scheduled match"

    # 3. Attempt LLM generation if Groq client is configured
    if client is not None:
        try:
            system_prompt = {
                "role": "system",
                "content": (
                    "You are an Autonomous Athlete Performance Planner for high-performance sports.\n"
                    "Generate exactly 1 day of actionable daily 'Quests' tailored to the athlete's workload constraints.\n"
                    "Provide exactly 2 to 3 quests covering:\n"
                    " 1. Primary Workout/Session (task_type: 'workout' or 'recovery')\n"
                    " 2. Mobility/Tissue Restoration (task_type: 'recovery')\n"
                    " 3. Wellness/Nutrition Protocol (task_type: 'wellness')\n\n"
                    "Return ONLY valid JSON matching this exact structure:\n"
                    "{\n"
                    '  "intensity": "Rest" | "Recovery" | "Moderate" | "High",\n'
                    '  "quests": [\n'
                    '    {\n'
                    '      "quest_title": string,\n'
                    '      "session_description": string,\n'
                    '      "task_type": "workout" | "recovery" | "wellness",\n'
                    '      "intensity_category": "Rest" | "Recovery" | "Moderate" | "High",\n'
                    '      "target_rpe": int (1-10),\n'
                    '      "duration_minutes": int,\n'
                    '      "agent_reasoning": string\n'
                    '    }\n'
                    '  ]\n'
                    "}"
                )
            }
            user_prompt = {
                "role": "user",
                "content": (
                    f"Date: {target_date_str}\n"
                    f"Athlete State: Fatigue {fatigue}/10, Sleep {sleep}/10\n"
                    f"Scheduled Event Today: {event_info}\n"
                    f"Mandatory Constraints:\n"
                    f"- Allowed Intensities: {constraints['allowed_intensity']}\n"
                    f"- Maximum Load Percentage: {max_load_pct}%\n"
                    f"- Active Triggers: {', '.join(constraints['reasons']) if constraints['reasons'] else 'None. Nominal load.'}\n"
                    "Generate the daily quests strictly adhering to these constraints."
                )
            }
            response = client.chat.completions.create(
                messages=[system_prompt, user_prompt],
                model=MODEL,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            llm_data = json.loads(response.choices[0].message.content)
            if "quests" in llm_data and isinstance(llm_data["quests"], list) and len(llm_data["quests"]) >= 2:
                for q in llm_data["quests"]:
                    q["target_load"] = q.get("target_rpe", 5) * q.get("duration_minutes", 30)
                    if "intensity_category" not in q:
                        q["intensity_category"] = primary_tier
                return {
                    "status": "success",
                    "plan_date": target_date_str,
                    "intensity": llm_data.get("intensity", primary_tier),
                    "was_revised": constraints["force_revision"],
                    "constraint_reasons": constraints["reasons"],
                    "quests": llm_data["quests"]
                }
        except Exception as e:
            print(f"Groq API quest generation failed: {e}. Executing deterministic sports-science generator.")

    # 4. Deterministic Sports-Science Quest Generator (Offline / Fallback)
    return _generate_heuristic_quests(athlete_id, target_date_str, constraints, primary_tier, fatigue, sleep, event_info)


def _generate_heuristic_quests(athlete_id: int, target_date_str: str, constraints: dict, 
                               primary_tier: str, fatigue: int, sleep: int, event_info: str) -> dict:
    """
    Algorithmic quest generator strictly respecting sports-science constraints and ACWR.
    """
    max_load_pct = constraints['max_load_percentage']
    reasons_text = " ".join(constraints['reasons'])

    quests = []

    if primary_tier == 'Rest':
        quests.append({
            "quest_title": "Complete Rest & Neuromuscular Decompression",
            "session_description": "Full physiological rest. Central nervous system requires complete recovery after high competitive load.",
            "task_type": "recovery",
            "intensity_category": "Rest",
            "target_rpe": 1,
            "duration_minutes": 15,
            "agent_reasoning": "Forced rest mandated by high acute match duration or extreme fatigue."
        })
        quests.append({
            "quest_title": "Hydrotherapy & Contrast Bath Protocol",
            "session_description": "15 minutes of contrast showering or thermal hydrotherapy to enhance lymphatic drainage.",
            "task_type": "recovery",
            "intensity_category": "Rest",
            "target_rpe": 1,
            "duration_minutes": 20,
            "agent_reasoning": "Passive circulation stimulant without accumulating muscular strain."
        })
        quests.append({
            "quest_title": "Sleep Hygiene & Magnesium Protocol",
            "session_description": "Dark room at 18°C, zero screen exposure 60 mins pre-sleep, target 9+ hours.",
            "task_type": "wellness",
            "intensity_category": "Rest",
            "target_rpe": 1,
            "duration_minutes": 15,
            "agent_reasoning": "Maximize human growth hormone release during deep restorative sleep cycles."
        })

    elif primary_tier == 'Recovery':
        quests.append({
            "quest_title": "Zone 1 Active Flush & Aerobic Spin",
            "session_description": "Low-resistance spin or brisk walk keeping heart rate strictly below 120 bpm (Zone 1).",
            "task_type": "workout",
            "intensity_category": "Recovery",
            "target_rpe": 3,
            "duration_minutes": 25,
            "agent_reasoning": f"Active recovery flush capped at {max_load_pct}% load to accelerate metabolic waste clearance."
        })
        quests.append({
            "quest_title": "Targeted Myofascial Release & Hip Mobility",
            "session_description": "Foam roll hamstrings, adductors, and glutes. Follow with 90/90 hip flow and thoracic rotations.",
            "task_type": "recovery",
            "intensity_category": "Recovery",
            "target_rpe": 2,
            "duration_minutes": 20,
            "agent_reasoning": "Restores joint range of motion and prevents compensatory biomechanical tightness."
        })
        quests.append({
            "quest_title": "Electrolyte Rehydration & Cellular Recovery",
            "session_description": "Consume 750ml water with sodium, magnesium, and potassium electrolytes alongside 30g protein.",
            "task_type": "wellness",
            "intensity_category": "Recovery",
            "target_rpe": 1,
            "duration_minutes": 10,
            "agent_reasoning": "Restores electrolyte equilibrium and initiates tissue protein resynthesis."
        })

    elif primary_tier == 'Moderate':
        if "Pre-Match Tapering" in reasons_text:
            quests.append({
                "quest_title": "Pre-Match Neuromuscular Activation & Speed",
                "session_description": "Short sprint mechanics (10m-20m accelerations), reactive footwork, and light tactical walkthrough.",
                "task_type": "workout",
                "intensity_category": "Moderate",
                "target_rpe": 5,
                "duration_minutes": 35,
                "agent_reasoning": f"Pre-match taper: sharpening reactive speed while capping workload at {max_load_pct}%."
            })
        else:
            quests.append({
                "quest_title": "Aerobic Conditioning & Sport-Specific Circuits",
                "session_description": "Controlled submaximal tempo intervals (Zone 3) combined with sport-specific ball mastery.",
                "task_type": "workout",
                "intensity_category": "Moderate",
                "target_rpe": 6,
                "duration_minutes": 45,
                "agent_reasoning": "Steady-state conditioning building chronic training resilience within safe ACWR limits."
            })

        quests.append({
            "quest_title": "Post-Workout Joint Decompression & Flexibility",
            "session_description": "Static stretching of hip flexors, hamstrings, and calves. Deep diaphragmatic breathing.",
            "task_type": "recovery",
            "intensity_category": "Recovery",
            "target_rpe": 2,
            "duration_minutes": 15,
            "agent_reasoning": "Shifts autonomic nervous system from sympathetic to parasympathetic state post-training."
        })
        quests.append({
            "quest_title": "Post-Session Glycogen & Hydration Routine",
            "session_description": "1.2g/kg carbohydrates and 25g whey protein within 45 mins to optimize glycogen resynthesis window.",
            "task_type": "wellness",
            "intensity_category": "Moderate",
            "target_rpe": 1,
            "duration_minutes": 10,
            "agent_reasoning": "Refuels muscle glycogen ahead of upcoming demands."
        })

    else: # High
        quests.append({
            "quest_title": "High-Intensity Interval Training & Power Circuits",
            "session_description": "Maximal anaerobic capacity intervals (4x4 mins at 90% HR max) paired with explosive plyometric bounds.",
            "task_type": "workout",
            "intensity_category": "High",
            "target_rpe": 8,
            "duration_minutes": 60,
            "agent_reasoning": "Nominal ACWR and fresh readiness allow high-overload conditioning for cardiovascular adaptation."
        })
        quests.append({
            "quest_title": "Extensive Cool-Down & Dynamic Fascial Release",
            "session_description": "10-minute light cycle cool-down followed by band-assisted hamstring and groin stretching.",
            "task_type": "recovery",
            "intensity_category": "Recovery",
            "target_rpe": 2,
            "duration_minutes": 20,
            "agent_reasoning": "Gradual deceleration reduces blood pooling and limits DOMS."
        })
        quests.append({
            "quest_title": "Sleep Prep & Optimal Protein Partitioning",
            "session_description": "Consume 30g slow-digesting casein protein before bed, dim all lights 90 mins prior to sleep.",
            "task_type": "wellness",
            "intensity_category": "High",
            "target_rpe": 1,
            "duration_minutes": 15,
            "agent_reasoning": "Sustained overnight amino acid delivery for myofibrillar protein synthesis."
        })

    for q in quests:
        q["target_load"] = q["target_rpe"] * q["duration_minutes"]

    return {
        "status": "success",
        "plan_date": target_date_str,
        "intensity": primary_tier,
        "was_revised": constraints["force_revision"],
        "constraint_reasons": constraints["reasons"],
        "quests": quests
    }


def generate_weekly_plan(athlete_id: int, start_date_str: str, fatigue: int = None, sleep: int = None, active_goal: str = 'Stay Fit') -> dict:
    """
    Legacy 7-Day horizon plan generator preserved for backward compatibility.
    """
    constraints = evaluate_daily_constraints(athlete_id, start_date_str, fatigue, sleep)
    
    # Fallback to rolling daily plan if Groq is unavailable
    if client is None:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        weekly_plan = []
        for day_offset in range(7):
            cur_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            daily = generate_daily_quests(athlete_id, cur_date, fatigue if day_offset == 0 else None, sleep if day_offset == 0 else None)
            primary_quest = daily["quests"][0]
            weekly_plan.append({
                "date": cur_date,
                "intensity": daily["intensity"],
                "session_description": primary_quest["session_description"],
                "target_rpe": primary_quest["target_rpe"],
                "duration_mins": primary_quest["duration_minutes"],
                "agent_reasoning": primary_quest["agent_reasoning"]
            })
        return {
            "status": "success",
            "was_revised": constraints["force_revision"],
            "constraint_reasons": constraints["reasons"],
            "weekly_plan": weekly_plan
        }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=7)
        cursor.execute('''SELECT event_date, event_type, duration_minutes FROM events 
                          WHERE athlete_id=? AND event_date >= ? AND event_date <= ?''',
                       (athlete_id, start_date_str, end_date.strftime("%Y-%m-%d")))
        events = cursor.fetchall()
        conn.close()
        
        events_str = ", ".join([f"{e['event_date']}: {e['event_type']} ({e['duration_minutes']}m)" for e in events])
        if not events_str:
            events_str = "No matches scheduled in the next 7 days."
        
        system_prompt = {
            "role": "system",
            "content": (
                "You are an Autonomous Athlete Performance Planner for team sports. "
                "Generate a rolling 7-day training plan starting from the provided date. "
                "Return ONLY a valid JSON object with a single key 'weekly_plan' containing an array of 7 daily objects.\n"
                "Each object MUST have these exact keys:\n"
                " - 'date': string (YYYY-MM-DD)\n"
                " - 'intensity': string (MUST be 'Rest', 'Recovery', 'Moderate', or 'High')\n"
                " - 'session_description': string (A 2-3 sentence description of the workout)\n"
                " - 'target_rpe': int (1-10)\n"
                " - 'duration_mins': int\n"
                " - 'target_steps': int\n"
                " - 'target_calories': int\n"
                " - 'agent_reasoning': string (Explain why this was chosen for this specific day)\n"
            )
        }
        
        user_prompt = {
            "role": "user",
            "content": (
                f"Start Date (Day 1): {start_date_str}\n"
                f"Athlete Current State:\n"
                f"- Fatigue: {fatigue}/10\n"
                f"- Sleep Quality: {sleep}/10\n"
                f"Current Goal: {active_goal}\n"
                f"Current Constraints:\n"
                f"- Allowed Intensities: {constraints['allowed_intensity']}\n"
                f"- Maximum Load Capacity: {constraints['max_load_percentage']}%\n"
                f"- Triggered Rules: {', '.join(constraints['reasons']) if constraints['reasons'] else 'None. Nominal.'}\n\n"
                f"Upcoming 7-Day Events: {events_str}\n\n"
                f"Generate the 7-day schedule in strict JSON."
            )
        }
        
        response = client.chat.completions.create(
            messages=[system_prompt, user_prompt],
            model=MODEL,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        plan_data = json.loads(response.choices[0].message.content)
        plan_data['was_revised'] = constraints['force_revision']
        plan_data['constraint_reasons'] = constraints['reasons']
        return plan_data
    except Exception as e:
        print(f"Weekly plan Groq call failed: {e}. Returning heuristic weekly plan.")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        weekly_plan = []
        for day_offset in range(7):
            cur_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            daily = generate_daily_quests(athlete_id, cur_date, fatigue if day_offset == 0 else None, sleep if day_offset == 0 else None)
            primary_quest = daily["quests"][0]
            weekly_plan.append({
                "date": cur_date,
                "intensity": daily["intensity"],
                "session_description": primary_quest["session_description"],
                "target_rpe": primary_quest["target_rpe"],
                "duration_mins": primary_quest["duration_minutes"],
                "agent_reasoning": primary_quest["agent_reasoning"]
            })
        return {
            "status": "success",
            "was_revised": constraints["force_revision"],
            "constraint_reasons": constraints["reasons"],
            "weekly_plan": weekly_plan
        }
