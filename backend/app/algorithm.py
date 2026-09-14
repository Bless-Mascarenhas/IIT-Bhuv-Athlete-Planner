import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta

from .database import get_db_connection

def calculate_acwr(athlete_id: int, current_date_str: str) -> float:
    """Calculates Acute (7-day sum) to Chronic (28-day weekly average) Workload Ratio."""
    conn = get_db_connection()
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    
    acute_start = current_date - timedelta(days=7)
    chronic_start = current_date - timedelta(days=28)
    
    cursor = conn.cursor()
    # Get Acute Load (Sum of last 7 days)
    cursor.execute('''
        SELECT SUM(acute_workload) as acute_load 
        FROM daily_logs 
        WHERE athlete_id = %s AND log_date > %s AND log_date <= %s
    ''', (athlete_id, acute_start.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")))
    acute_res = cursor.fetchone()
    acute_load = acute_res['acute_load'] if acute_res['acute_load'] else 0

    # Get Chronic Load (Sum of last 28 days)
    cursor.execute('''
        SELECT SUM(acute_workload) as chronic_load 
        FROM daily_logs 
        WHERE athlete_id = %s AND log_date > %s AND log_date <= %s
    ''', (athlete_id, chronic_start.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")))
    chronic_res = cursor.fetchone()
    chronic_total = chronic_res['chronic_load'] if chronic_res['chronic_load'] else 0
    
    conn.close()

    if chronic_total == 0:
        return 0.0 # Prevent division by zero
        
    # Chronic workload is typically evaluated as the average weekly load over the 4 weeks
    chronic_weekly_avg = chronic_total / 4.0
    
    if chronic_weekly_avg == 0:
         return 0.0
         
    return round(acute_load / chronic_weekly_avg, 2)


def get_consecutive_high_intensity_days(athlete_id: int, current_date_str: str) -> int:
    """Counts consecutive 'High' intensity days immediately prior to current_date."""
    conn = get_db_connection()
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    cursor = conn.cursor()
    
    start_date = current_date - timedelta(days=4)
    cursor.execute('''
        SELECT plan_date, intensity_category 
        FROM training_plans 
        WHERE athlete_id = %s AND plan_date >= %s AND plan_date < %s
        ORDER BY plan_date DESC
    ''', (athlete_id, start_date.strftime("%Y-%m-%d"), current_date_str))
    
    plans = cursor.fetchall()
    conn.close()
    
    consecutive = 0
    expected_date = current_date - timedelta(days=1)
    
    for plan in plans:
        if plan['plan_date'] == expected_date.strftime("%Y-%m-%d"):
            if plan['intensity_category'] == 'High':
                consecutive += 1
                expected_date -= timedelta(days=1)
            else:
                break
        else:
            break
            
    return consecutive

def evaluate_daily_constraints(athlete_id: int, current_date_str: str, fatigue: int = None, sleep: int = None) -> dict:
    """
    Evaluates all 5 hard rules and returns constraint directives.
    Returns a dict with 'allowed_intensity', 'max_load_percentage', and 'reasons'.
    """
    conn = get_db_connection()
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    cursor = conn.cursor()
    
    constraints = {
        'allowed_intensity': ['Rest', 'Recovery', 'Moderate', 'High'], # Sorted lowest to highest
        'max_load_percentage': 100, 
        'reasons': [],
        'force_revision': False # Used by the Agent to trigger a recalculation
    }
    
    def restrict_intensity(max_allowed_tier, reason, max_load):
        tiers = ['Rest', 'Recovery', 'Moderate', 'High']
        idx = tiers.index(max_allowed_tier)
        constraints['allowed_intensity'] = tiers[:idx+1] # Slice to keep only allowed tiers
        
        if max_load < constraints['max_load_percentage']:
            constraints['max_load_percentage'] = max_load
            
        constraints['reasons'].append(reason)
        constraints['force_revision'] = True

    # RULE 3: Fatigue / Wellness Threshold (Fatigue > 7 OR Sleep < 5)
    if fatigue is not None and fatigue > 7:
        restrict_intensity('Recovery', f"High fatigue reported ({fatigue}/10). Forced Recovery.", 40)
    
    if sleep is not None and sleep < 5:
        restrict_intensity('Recovery', f"Poor sleep reported ({sleep}/10). Forced Recovery.", 40)

    # RULE 1: Pre-Match Tapering (24h = <30%, 48h = <50%)
    tomorrow = current_date + timedelta(days=1)
    day_after = current_date + timedelta(days=2)
    
    cursor.execute('''SELECT id FROM events WHERE athlete_id=%s AND event_type='match' AND event_date=%s''', 
                   (athlete_id, tomorrow.strftime("%Y-%m-%d")))
    if cursor.fetchone():
        restrict_intensity('Moderate', "Pre-Match Tapering (24h). Max load 30%.", 30)
        
    cursor.execute('''SELECT id FROM events WHERE athlete_id=%s AND event_type='match' AND event_date=%s''', 
                   (athlete_id, day_after.strftime("%Y-%m-%d")))
    if cursor.fetchone():
        if constraints['max_load_percentage'] > 50:
            restrict_intensity('Moderate', "Pre-Match Tapering (48h). Max load 50%.", 50)

    # RULE 2: Post-Match Recovery (Day after -> Active Recovery 25%. Rest if >90 mins)
    yesterday = current_date - timedelta(days=1)
    cursor.execute('''SELECT duration_minutes FROM events WHERE athlete_id=%s AND event_type='match' AND event_date=%s''', 
                   (athlete_id, yesterday.strftime("%Y-%m-%d")))
    match_yesterday = cursor.fetchone()
    if match_yesterday:
        duration = match_yesterday['duration_minutes']
        if duration and duration > 90:
            restrict_intensity('Rest', "Extreme Match Load yesterday (>90 mins). Passive Rest Required.", 0)
        else:
            restrict_intensity('Recovery', "Post-Match Day. Active Recovery Required (Max 25%).", 25)

    # RULE 5: Consecutive High-Intensity Days (Max 2)
    consecutive_high = get_consecutive_high_intensity_days(athlete_id, current_date_str)
    if consecutive_high >= 2:
        if 'High' in constraints['allowed_intensity']:
            constraints['allowed_intensity'].remove('High')
            constraints['reasons'].append("2 Consecutive High-Intensity days reached. Capping at Moderate.")
            constraints['force_revision'] = True

    # RULE 4: Acute:Chronic Workload Ratio (ACWR) (> 1.5)
    acwr = calculate_acwr(athlete_id, current_date_str)
    if acwr > 1.5:
        if 'High' in constraints['allowed_intensity']:
            constraints['allowed_intensity'].remove('High')
        if constraints['max_load_percentage'] > 70: # Standardizing a ~30% drop
            constraints['max_load_percentage'] = 70
        constraints['reasons'].append(f"ACWR Danger Zone ({acwr}). Intensity reduced by 30%.")
        constraints['force_revision'] = True

    conn.close()
    return constraints
