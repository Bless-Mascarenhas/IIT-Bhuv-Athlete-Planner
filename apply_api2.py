import re

with open('mobile/src/services/api.ts', 'r', encoding='utf-8') as f:
    api_code = f.read()

# Add goal_end_date to UserProfile
api_code = api_code.replace("active_goal?: string;", "active_goal?: string;\n  goal_end_date?: string;")
api_code = api_code.replace("active_goal: 'Stay Fit',", "active_goal: 'Stay Fit',\n  goal_end_date: undefined,")

# Add goal_end_date to API response mapping
api_code = api_code.replace("active_goal: data.active_goal || 'Stay Fit',", "active_goal: data.active_goal || 'Stay Fit',\n        goal_end_date: data.goal_end_date,")

# Add completeGoal API function
complete_goal_fn = """
  async completeGoal(userId: number = 1): Promise<boolean> {
    try {
      const res = await fetch(`/api/user/goal/complete?user_id=${userId}`, {
        method: 'POST',
      });
      return res.ok;
    } catch {
      return false;
    }
  },
"""
api_code = api_code.replace("async updateGoal", complete_goal_fn + "\n  async updateGoal")

with open('mobile/src/services/api.ts', 'w', encoding='utf-8') as f:
    f.write(api_code)

print("api.ts updated.")
