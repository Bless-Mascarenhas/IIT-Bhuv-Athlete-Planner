import re

with open('mobile/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    d_code = f.read()

# Make sure we have the imports needed for the tasks
if 'CheckCircle2' not in d_code:
    d_code = d_code.replace("Activity, Moon, Heart, Zap, ArrowRight, Target", "Activity, Moon, Heart, Zap, ArrowRight, Target, CheckCircle2, Circle, Flame")

quests_preview = """
      {/* Today's Schedule Preview */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436' }}>Today's Goal / Schedule</h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {quests.filter(q => q.plan_date === new Date().toISOString().split('T')[0]).length === 0 && (
            <div className="neu-box" style={{ padding: '1rem', textAlign: 'center', color: '#7f8c8d' }}>
              No quests scheduled for today.
            </div>
          )}
          {quests.filter(q => q.plan_date === new Date().toISOString().split('T')[0]).slice(0, 3).map((quest) => (
            <div key={quest.id} className="neu-box" style={{ padding: '1rem', display: 'flex', gap: '12px', alignItems: 'center', opacity: quest.is_completed ? 0.6 : 1 }}>
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: quest.is_completed ? '#7f8c8d' : '#2d3436', textDecoration: quest.is_completed ? 'line-through' : 'none', marginBottom: '4px' }}>
                  {quest.quest_title}
                </h4>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#0984e3' }}>
                    {quest.duration_minutes} mins
                  </span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#e84393' }}>
                    RPE {quest.target_rpe}
                  </span>
                </div>
              </div>
              {quest.is_completed ? (
                <CheckCircle2 size={24} color="#00b894" />
              ) : (
                <Circle size={24} color="#b2bec3" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Link to Planner */}
"""

d_code = d_code.replace("{/* Navigation Link to Planner */}", quests_preview)

with open('mobile/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(d_code)

print("Dashboard updated with quests preview.")
