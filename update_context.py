import re

with open('mobile/src/context/AthleteContext.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Add updateGoal to interface
code = code.replace("refreshProfile: () => Promise<void>;", "refreshProfile: () => Promise<void>;\n  updateGoal: (goal: string) => Promise<void>;")

# Add updateGoal function body
update_goal_fn = """
  const updateGoal = useCallback(async (goal: string) => {
    setLoading(true);
    await api.updateGoal(goal, 1);
    await refreshProfile();
    // Setting a new goal also recalculates the plan
    await fetch('/api/plan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ athlete_id: 1, active_goal: goal }),
    });
    await refreshQuests();
    setLoading(false);
  }, [refreshProfile, refreshQuests]);
"""
code = code.replace("const healthProvider = useMemo", update_goal_fn + "\n  const healthProvider = useMemo")

# Pass updateGoal to Provider value
code = code.replace("refreshProfile,\n        syncHealth,", "refreshProfile,\n        syncHealth,\n        updateGoal,")

# rename getTodayPlan to get7DayPlan in the context where it's called
code = code.replace("api.getTodayPlan(1)", "api.get7DayPlan(1)")

with open('mobile/src/context/AthleteContext.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("AthleteContext updated.")
