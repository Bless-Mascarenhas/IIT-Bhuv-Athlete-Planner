import re

with open('mobile/src/context/AthleteContext.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Add to interface
code = code.replace("updateGoal: (goal: string) => Promise<void>;", "updateGoal: (goal: string) => Promise<void>;\n  completeGoal: () => Promise<void>;")

# Add function body
complete_fn = """
  const completeGoal = useCallback(async () => {
    setLoading(true);
    await api.completeGoal(1);
    await refreshProfile();
    setLoading(false);
  }, [refreshProfile]);
"""
code = code.replace("const healthProvider = useMemo", complete_fn + "\n  const healthProvider = useMemo")

# Expose to provider
code = code.replace("updateGoal,", "updateGoal,\n        completeGoal,")

with open('mobile/src/context/AthleteContext.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("AthleteContext updated.")
