import React, { useState } from 'react';
import { Activity, Moon, Heart, Zap, ArrowRight, Target } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAthlete } from '../context/AthleteContext';

export default function Dashboard() {
  const { athlete, quests, healthMetrics: metrics, updateGoal, completeGoal, loading } = useAthlete();
  const [goalInput, setGoalInput] = useState('');
  const [isSettingGoal, setIsSettingGoal] = useState(false);

  // const totalQuests = quests.length;
  // const completedQuests = quests.filter((q) => q.is_completed).length;
  // const completionPercentage = totalQuests > 0 ? Math.round((completedQuests / totalQuests) * 100) : 0;

  const todayPlan = quests[0];
  const targetSteps = todayPlan?.target_steps ?? 10000;
  const targetCalories = todayPlan?.target_calories ?? 2500;
  
  const currentSteps = metrics?.steps ?? 0;
  const currentCals = metrics?.caloriesBurned ?? 0;

  const stepsPct = Math.min(100, Math.round((currentSteps / targetSteps) * 100));
  const calsPct = Math.min(100, Math.round((currentCals / targetCalories) * 100));

  const handleSetGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalInput.trim()) return;
    setIsSettingGoal(true);
    await updateGoal(goalInput);
    setGoalInput('');
    setIsSettingGoal(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', paddingBottom: '5rem' }}>
      
      {/* Active Goal Setting Section */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
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
        )}
      </div>

      {/* Biometric Health Telemetry Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436' }}>Today's Progress vs Targets</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem' }}>
          {/* Steps Progress Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0984e3' }}>
              <Activity size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Steps</span>
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {currentSteps.toLocaleString()} <span style={{ fontSize: '0.7rem', color: '#7f8c8d' }}>/ {targetSteps.toLocaleString()}</span>
            </div>
            {/* Progress Bar */}
            <div style={{ height: '6px', backgroundColor: 'rgba(0,0,0,0.1)', borderRadius: '999px', marginTop: '8px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${stepsPct}%`, backgroundColor: '#0984e3', borderRadius: '999px' }} />
            </div>
          </div>

          {/* Calories Progress Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fc5200' }}>
              <Zap size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Calories Burned</span>
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {currentCals.toLocaleString()} <span style={{ fontSize: '0.7rem', color: '#7f8c8d' }}>/ {targetCalories.toLocaleString()}</span>
            </div>
            {/* Progress Bar */}
            <div style={{ height: '6px', backgroundColor: 'rgba(0,0,0,0.1)', borderRadius: '999px', marginTop: '8px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${calsPct}%`, backgroundColor: '#fc5200', borderRadius: '999px' }} />
            </div>
          </div>
          
          {/* Sleep Hours Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6c5ce7' }}>
              <Moon size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Sleep</span>
            </div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {metrics?.sleepHours ?? 7.8} <span style={{ fontSize: '0.85rem' }}>hrs</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#7f8c8d', marginTop: '2px' }}>
              Restorative Sleep
            </div>
          </div>

          {/* Resting Heart Rate Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#e84393' }}>
              <Heart size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Resting HR</span>
            </div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {metrics?.restingHeartRate ?? 54} <span style={{ fontSize: '0.85rem' }}>bpm</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#7f8c8d', marginTop: '2px' }}>
              Current: {metrics?.currentHeartRate ?? 64} bpm
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Link to Planner */}
      <Link
        to="/planner"
        className="neu-btn"
        style={{
          padding: '1rem',
          gap: '6px',
          fontSize: '1rem',
          fontWeight: 800,
          color: '#fc5200',
          textDecoration: 'none',
        }}
      >
        <span>Open Dynamic 7-Day Planner</span>
        <ArrowRight size={20} />
      </Link>
    </div>
  );
}
