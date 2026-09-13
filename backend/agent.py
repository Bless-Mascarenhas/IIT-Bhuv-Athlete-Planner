import os
import json
from datetime import datetime, timedelta
from groq import Groq
from algorithm import evaluate_daily_constraints, get_db_connection

# Using environment variable for security
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# We use the powerful Llama 3 70B for high-level reasoning and strict JSON adherence
MODEL = "openai/gpt-oss-120b"

def get_onboarding_response(conversation_history: list) -> str:
    """
    Grill Agent: Interviews the user to establish their baseline.
    """
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


def generate_weekly_plan(athlete_id: int, start_date_str: str, fatigue: int = None, sleep: int = None) -> dict:
    """
    Planner Agent: Uses mathematical constraints and a 7-day horizon to generate a rolling weekly schedule.
    """
    # 1. Get the mathematical constraints for TODAY (Day 1)
    constraints = evaluate_daily_constraints(athlete_id, start_date_str, fatigue, sleep)
    
    # 2. Grab upcoming events for the next 7 days to pass to the LLM
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
    
    # 3. Build the prompt for Groq
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
            " - 'agent_reasoning': string (Explain why this was chosen for this specific day)\n"
        )
    }
    
    user_prompt = {
        "role": "user",
        "content": (
            f"Start Date (Day 1): {start_date_str}\n"
            f"Athlete Current State (Crucial for Day 1 mapping):\n"
            f"- Fatigue: {fatigue}/10 (10=Worst)\n"
            f"- Sleep Quality: {sleep}/10 (10=Best)\n"
            f"Current Constraints (MUST BE STRICTLY OBEYED FOR DAY 1):\n"
            f"- Allowed Intensities: {constraints['allowed_intensity']}\n"
            f"- Maximum Load Capacity: {constraints['max_load_percentage']}%\n"
            f"- Triggered Rules: {', '.join(constraints['reasons']) if constraints['reasons'] else 'None. Nominal.'}\n\n"
            f"Upcoming 7-Day Events (Calendar): {events_str}\n\n"
            f"Generate the 7-day schedule in strict JSON. \n"
            f"CRITICAL RULES: \n"
            f"1. Day 1 MUST strictly obey the Current Constraints above.\n"
            f"2. If the athlete is fresh today (low fatigue, great sleep), push them with High/Moderate on Day 1.\n"
            f"3. Smoothly periodize the remaining 6 days around any upcoming matches (taper before, recover after)."
        )
    }
    
    response = client.chat.completions.create(
        messages=[system_prompt, user_prompt],
        model=MODEL,
        temperature=0.2, # Low temperature forces the AI to stick strictly to the rules
        response_format={"type": "json_object"}
    )
    
    plan_data = json.loads(response.choices[0].message.content)
    
    # Merge the mathematical flags so the frontend API knows if Day 1 was a forced revision
    plan_data['was_revised'] = constraints['force_revision']
    plan_data['constraint_reasons'] = constraints['reasons']
    
    return plan_data
