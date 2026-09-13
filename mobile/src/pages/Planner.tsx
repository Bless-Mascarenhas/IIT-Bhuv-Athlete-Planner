import { useState, useMemo } from 'react';
import { Calendar, CheckCircle2, Circle, Flame, Target, ChevronDown } from 'lucide-react';
import { useAthlete } from '../context/AthleteContext';

export default function Planner() {
  const { quests, completeQuest, loading } = useAthlete();
  
  // Extract unique dates from the 7-day plan
  const availableDates = useMemo(() => {
    const dates = quests.map(q => q.plan_date);
    return Array.from(new Set(dates)).sort();
  }, [quests]);

  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  // Default to the first day available if none selected
  const activeDate = selectedDate || (availableDates.length > 0 ? availableDates[0] : null);

  const activeDayQuests = useMemo(() => {
    if (!activeDate) return [];
    return quests.filter(q => q.plan_date === activeDate);
  }, [quests, activeDate]);

  const activeDayTargetSteps = activeDayQuests[0]?.target_steps ?? 10000;
  const activeDayTargetCals = activeDayQuests[0]?.target_calories ?? 2500;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem', color: '#7f8c8d' }}>
        Loading 7-Day Plan...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', paddingBottom: '5rem' }}>
      
      {/* 7-Day Dropdown Selector */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={20} color="#fc5200" />
            {availableDates.length >= 7 ? '7-Day Forecast' : 'Upcoming Plan'}
          </h3>
        </div>
        
        <div style={{ position: 'relative' }}>
          <select 
            value={activeDate || ''} 
            onChange={(e) => setSelectedDate(e.target.value)}
            className="neu-inset"
            style={{
              width: '100%',
              padding: '0.85rem',
              borderRadius: '12px',
              border: 'none',
              backgroundColor: 'transparent',
              outline: 'none',
              appearance: 'none',
              fontSize: '1rem',
              fontWeight: 700,
              color: '#2d3436'
            }}
          >
            {availableDates.length === 0 && <option value="">No plan generated</option>}
            {availableDates.map(date => (
              <option key={date} value={date}>
                {new Date(date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
              </option>
            ))}
          </select>
          <div style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#7f8c8d' }}>
            <ChevronDown size={20} />
          </div>
        </div>
      </div>

      {/* Daily Targets Overview */}
      {activeDate && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0, textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', marginBottom: '4px' }}>Target Steps</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0984e3' }}>{activeDayTargetSteps.toLocaleString()}</div>
          </div>
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0, textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', marginBottom: '4px' }}>Target Calories</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fc5200' }}>{activeDayTargetCals.toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Task List */}
      <div>
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436', marginBottom: '1rem' }}>
          Schedule for {activeDate ? new Date(activeDate).toLocaleDateString(undefined, { weekday: 'long' }) : 'Today'}
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {activeDayQuests.map((quest) => (
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

          {activeDayQuests.length === 0 && (
            <div style={{ textAlign: 'center', color: '#7f8c8d', padding: '2rem' }}>
              No quests scheduled for this day.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
