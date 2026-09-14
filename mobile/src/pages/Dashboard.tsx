import React, { useState, useEffect } from 'react';
import { Activity, Moon, Heart, Zap, ArrowRight, Target, CheckCircle2, Circle, RefreshCw, CalendarDays } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAthlete } from '../context/AthleteContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Dashboard() {
  const { userId } = useAuth();
  const { athlete, quests, healthMetrics: metrics, completeGoal, loading, syncHealth, refreshQuests, completeQuest } = useAthlete();
  const [isSyncing, setIsSyncing] = useState(false);
  const [yesterdayReport, setYesterdayReport] = useState<any>(null);

  useEffect(() => {
    if (userId) {
      api.getYesterdayReport(userId).then(setYesterdayReport);
    }
  }, [userId]);

  const handleManualSync = async () => {
    setIsSyncing(true);
    if (syncHealth) await syncHealth();
    if (refreshQuests) await refreshQuests();
    setTimeout(() => setIsSyncing(false), 800);
  };

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



  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', paddingBottom: '5rem' }}>
      
      {/* Active Goal Setting Section */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Target size={20} color="#fc5200" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>Active Goal</h3>
        </div>
        
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0984e3', marginBottom: '0.5rem' }}>
            {athlete?.active_goal || 'Stay Fit'}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#7f8c8d' }}>
            Set from your profile settings.
          </div>
        </div>
      </div>

      {/* Biometric Health Telemetry Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436' }}>Today's Progress vs Targets</h3>
          <button 
            onClick={handleManualSync}
            disabled={isSyncing}
            className="neu-btn"
            style={{
              padding: '0.4rem',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isSyncing ? '#0984e3' : '#636e72',
              transform: isSyncing ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.4s ease, color 0.2s ease'
            }}
          >
            <RefreshCw size={18} />
          </button>
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
              {metrics?.sleepHours || 0} <span style={{ fontSize: '0.85rem' }}>hrs</span>
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
              {metrics?.restingHeartRate || 0} <span style={{ fontSize: '0.85rem' }}>bpm</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#7f8c8d', marginTop: '2px' }}>
              Current: {metrics?.currentHeartRate || 0} bpm
            </div>
          </div>
        </div>
      </div>
      
      {/* Yesterday's Report */}
      {yesterdayReport && (yesterdayReport.quests?.length > 0 || yesterdayReport.biometrics) && (
        <div className="neu-box" style={{ padding: '1.25rem', backgroundColor: 'rgba(9, 132, 227, 0.05)', border: '1px solid rgba(9, 132, 227, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <CalendarDays size={20} color="#0984e3" />
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>Yesterday's Report</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div style={{ backgroundColor: 'var(--bg)', padding: '0.8rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Quests Completed</span>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436' }}>
                {yesterdayReport.quests?.filter((q: any) => q.is_completed).length || 0} <span style={{ fontSize: '0.8rem', color: '#7f8c8d' }}>/ {yesterdayReport.quests?.length || 0}</span>
              </span>
            </div>
            {yesterdayReport.biometrics && (
              <>
                <div style={{ backgroundColor: 'var(--bg)', padding: '0.8rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Steps</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436' }}>
                    {(yesterdayReport.biometrics.steps || 0).toLocaleString()}
                  </span>
                </div>
                <div style={{ backgroundColor: 'var(--bg)', padding: '0.8rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Calories Burned</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436' }}>
                    {(yesterdayReport.biometrics.calories_burned || 0).toLocaleString()}
                  </span>
                </div>
                <div style={{ backgroundColor: 'var(--bg)', padding: '0.8rem', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Sleep</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#2d3436' }}>
                    {Math.round((yesterdayReport.biometrics.sleep_minutes || 0) / 60)} hrs
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      
      {/* Today's Schedule Preview */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436' }}>Today's Goal / Schedule</h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {loading && quests.length === 0 ? (
            <div className="neu-box" style={{ padding: '1rem', textAlign: 'center', color: '#0984e3', fontWeight: 700, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
               <RefreshCw size={16} className="spin" /> Generating your dynamic plan...
            </div>
          ) : quests.filter(q => q.plan_date === new Date().toISOString().split('T')[0]).length === 0 ? (
            <div className="neu-box" style={{ padding: '1rem', textAlign: 'center', color: '#7f8c8d' }}>
              No quests scheduled for today.
            </div>
          ) : quests.filter(q => q.plan_date === new Date().toISOString().split('T')[0]).slice(0, 3).map((quest) => (
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
              <button 
                onClick={() => completeQuest(quest.id)}
                className="neu-btn"
                style={{
                  padding: '8px',
                  borderRadius: '50%',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  color: quest.is_completed ? '#00b894' : '#b2bec3',
                }}
              >
                {quest.is_completed ? (
                  <CheckCircle2 size={24} />
                ) : (
                  <Circle size={24} />
                )}
              </button>
            </div>
          ))}
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
