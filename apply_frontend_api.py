import re

with open('mobile/src/services/api.ts', 'r', encoding='utf-8') as f:
    api_code = f.read()

# Add active_goal to UserProfile
api_code = api_code.replace("sport_type: string;", "sport_type: string;\n  active_goal?: string;")
api_code = api_code.replace("sport_type: 'Soccer',", "sport_type: 'Soccer',\n  active_goal: 'Stay Fit',")

api_code = api_code.replace("current_streak: data.current_streak ?? 12,", "current_streak: data.current_streak ?? 12,\n        active_goal: data.active_goal || 'Stay Fit',")

# Add updateGoal method to ApiService
update_goal_fn = """
  async updateGoal(goal: string, userId: number = 1): Promise<boolean> {
    try {
      const res = await fetch(`/api/user/goal?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },
"""
api_code = api_code.replace("async getProfile", update_goal_fn + "\n  async getProfile")

# Change getTodayPlan to return 7 days
api_code = api_code.replace("getTodayPlan", "get7DayPlan")
api_code = api_code.replace("data.quests", "data.plan") 

with open('mobile/src/services/api.ts', 'w', encoding='utf-8') as f:
    f.write(api_code)

print("Frontend API updated.")
