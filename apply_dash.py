import re

with open('mobile/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    d_code = f.read()

d_code = d_code.replace("const { athlete, quests, healthMetrics: metrics, updateGoal, loading } = useAthlete();", "const { athlete, quests, healthMetrics: metrics, updateGoal, completeGoal, loading } = useAthlete();")

ui_block = """<div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Target size={20} color="#fc5200" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>Active Goal</h3>
        </div>
        
        {athlete?.active_goal && athlete?.goal_end_date && new Date(athlete.goal_end_date) >= new Date(new Date().toISOString().split('T')[0]) ? (
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0984e3', marginBottom: '0.5rem' }}>
              {athlete.active_goal}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#7f8c8d', marginBottom: '1rem' }}>
              Locked until {new Date(athlete.goal_end_date).toLocaleDateString()}
            </div>
            <button 
              onClick={() => completeGoal()} 
              disabled={loading}
              className="neu-btn"
              style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', fontWeight: 800, color: '#00b894' }}
            >
              Mark Goal as Completed
            </button>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '0.85rem', color: '#7f8c8d', marginBottom: '1rem' }}>
              Set a new 7-day goal. You cannot change this until it expires or is completed.
            </div>
            <form onSubmit={handleSetGoal} style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                placeholder="e.g. Lose 10kg in 10 days" 
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
                className="neu-inset"
                style={{ 
                  flex: 1, 
                  padding: '0.65rem 1rem', 
                  border: 'none', 
                  borderRadius: '999px',
                  backgroundColor: 'transparent',
                  outline: 'none',
                  fontSize: '0.85rem'
                }}
              />
              <button 
                type="submit" 
                className="neu-btn" 
                disabled={isSettingGoal || loading}
                style={{ padding: '0 1rem', borderRadius: '999px', fontWeight: 700, color: '#fc5200' }}
              >
                {isSettingGoal ? 'Planning...' : 'Set Goal'}
              </button>
            </form>
          </div>
        )}"""

old_ui = r'<div style=\{\{ display: \'flex\', alignItems: \'center\', gap: \'8px\', marginBottom: \'10px\' \}\}>[\s\S]*?</form>'

d_code = re.sub(old_ui, ui_block, d_code)

with open('mobile/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(d_code)

print("Dashboard updated.")
