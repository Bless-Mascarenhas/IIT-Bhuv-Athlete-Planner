import { useMemo } from 'react';
import { Calendar, CheckCircle2, Circle, Flame, Target } from 'lucide-react';
import { useAthlete } from '../context/AthleteContext';

export default function Planner() {
  const { quests, completeQuest, loading } = useAthlete();
  
  // Extract unique dates from the 7-day plan
  const availableDates = useMemo(() => {
    const dates = quests.map(q => q.plan_date);
    return Array.from(new Set(dates)).sort();
  }, [quests]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem', color: '#7f8c8d' }}>
        Loading 7-Day Plan...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', paddingBottom: '5rem' }}>
      
      {/* Header */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Calendar size={20} color="#fc5200" />
          {availableDates.length >= 7 ? '7-Day Forecast' : 'Upcoming Plan'}
        </h3>
      </div>

      {availableDates.length === 0 && (
        <div style={{ textAlign: 'center', color: '#7f8c8d', padding: '2rem' }}>
          No plan generated yet. Set a goal in the Dashboard!
        </div>
      )}

      {/* Stacked Days */}
      {availableDates.map((date) => {
        const dayQuests = quests.filter(q => q.plan_date === date);
        const targetSteps = dayQuests[0]?.target_steps ?? 10000;
        const targetCals = dayQuests[0]?.target_calories ?? 2500;
        
        return (
          <div key={date} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0984e3' }}>
                {new Date(date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
              </h3>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', backgroundColor: 'rgba(0,0,0,0.05)', padding: '4px 8px', borderRadius: '8px' }}>
                  {targetSteps.toLocaleString()} steps
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', backgroundColor: 'rgba(252, 82, 0, 0.05)', padding: '4px 8px', borderRadius: '8px' }}>
                  {targetCals.toLocaleString()} cals
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {dayQuests.map((quest) => (
                <div key={quest.id} className="neu-box" style={{ padding: '1.25rem', opacity: quest.is_completed ? 0.6 : 1, transition: 'opacity 0.3s' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', gap: '12px', flex: 1 }}>
                      <button 
                        onClick={() => completeQuest(quest.id)}
                        style={{ 
                          background: 'none', 
                          border: 'none', 
                          padding: 0, 
                          cursor: 'pointer', 
                          marginTop: '2px' 
                        }}
                      >
                        {quest.is_completed ? (
                          <CheckCircle2 size={24} color="#00b894" />
                        ) : (
                          <Circle size={24} color="#b2bec3" />
                        )}
                      </button>
                      <div style={{ paddingRight: '1rem' }}>
                        <h4 style={{ 
                          fontSize: '1rem', 
                          fontWeight: 800, 
                          color: quest.is_completed ? '#7f8c8d' : '#2d3436',
                          textDecoration: quest.is_completed ? 'line-through' : 'none',
                          marginBottom: '4px'
                        }}>
                          {quest.quest_title}
                        </h4>
                        
                        <div style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0984e3', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Target size={14} /> {quest.duration_minutes} mins
                          </span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e84393', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Flame size={14} /> RPE {quest.target_rpe}
                          </span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>
                            {quest.task_type}
                          </span>
                        </div>

                        <p style={{ fontSize: '0.85rem', color: '#636e72', lineHeight: '1.4' }}>
                          {quest.session_description}
                        </p>
                        
                        {quest.revision_reason && (
                          <div style={{ marginTop: '8px', padding: '6px 10px', backgroundColor: '#ffeaa7', borderRadius: '6px', fontSize: '0.75rem', color: '#d63031', fontWeight: 600 }}>
                            Revised: {quest.revision_reason}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
