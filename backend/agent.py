import os
import json
from groq import Groq
from algorithm import evaluate_daily_constraints

# Using environment variable for security
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# We use the powerful Llama 3 70B for high-level reasoning and strict JSON adherence
MODEL = "openai/gpt-oss-120b"

def get_onboarding_response(conversation_history: list) -> str:
    """
    Grill Agent: Interviews the user to establish their baseline.
    conversation_history is a list of dicts: [{'role': 'user'/'assistant', 'content': '...'}]
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


def generate_daily_plan(athlete_id: int, current_date_str: str, fatigue: int = None, sleep: int = None) -> dict:
    """
    Planner Agent: Uses the mathematical constraints from algorithm.py to generate a specific training session.
    """
    # 1. Get the mathematical constraints (The Referee)
    constraints = evaluate_daily_constraints(athlete_id, current_date_str, fatigue, sleep)
    
    # 2. Build the prompt for Groq
    system_prompt = {
        "role": "system",
        "content": (
            "You are an Autonomous Athlete Performance Planner for team sports. "
            "Your job is to generate a specific, actionable daily training plan that STRICTLY follows "
            "the provided mathematical constraints. Do NOT prescribe medical treatments or make injury claims.\n"
            "Return ONLY a valid JSON object with the following keys:\n"
            " - 'intensity': string (MUST be one of the exact Allowed Intensities provided)\n"
            " - 'session_description': string (A 2-3 sentence description of the workout, e.g., 'Light mobility spin and foam rolling' for Recovery)\n"
            " - 'target_rpe': int (1-10)\n"
            " - 'duration_mins': int\n"
            " - 'agent_reasoning': string (Explain why you chose this, heavily referencing the constraints and sport science)\n"
        )
    }
    
    user_prompt = {
        "role": "user",
        "content": (
            f"Date: {current_date_str}\n"
            f"Athlete Current State:\n"
            f"- Fatigue: {fatigue}/10 (10=Worst)\n"
            f"- Sleep Quality: {sleep}/10 (10=Best)\n"
            f"Constraints from Load Management Engine:\n"
            f"- Allowed Intensities: {constraints['allowed_intensity']}\n"
            f"- Maximum Load Capacity: {constraints['max_load_percentage']}%\n"
            f"- Triggered Rules / System Reasons: {', '.join(constraints['reasons']) if constraints['reasons'] else 'None. Nominal condition.'}\n\n"
            f"Given the athlete's current state and strictly obeying the constraints, generate the optimal training plan in strict JSON. If the athlete is extremely fresh (low fatigue, great sleep) and constraints allow it, you MUST prescribe a 'High' or 'Moderate' intensity session to build fitness. Do not prescribe Recovery for a fully rested athlete unless forced by constraints."
        )
    }
    
    response = client.chat.completions.create(
        messages=[system_prompt, user_prompt],
        model=MODEL,
        temperature=0.2, # Low temperature forces the AI to stick strictly to the rules
        response_format={"type": "json_object"}
    )
    
    plan_data = json.loads(response.choices[0].message.content)
    
    # Merge the mathematical flags so the frontend API knows if this was a forced revision
    plan_data['was_revised'] = constraints['force_revision']
    plan_data['constraint_reasons'] = constraints['reasons']
    
    return plan_data
