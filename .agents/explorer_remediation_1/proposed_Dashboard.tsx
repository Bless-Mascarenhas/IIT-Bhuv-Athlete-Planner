import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAthlete } from '../context/AthleteContext';
import { getHealthProvider, type HealthMetrics } from '../services/health';
import { Flame, Heart, Moon, Zap, Activity, CheckCircle2, Circle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function Dashboard() {
  const { athlete, streak, greeting, quests, healthMetrics: contextMetrics, healthProviderName } = useAthlete();
  const [metrics, setMetrics] = useState<HealthMetrics | null>(contextMetrics);

  useEffect(() => {
    let isMounted = true;
    async function fetchBiometrics() {
      try {
        const provider = getHealthProvider();
        const data = await provider.getTodayMetrics();
        if (isMounted) {
          setMetrics(data);
        }
      } catch {
        // Retain context metrics if provider call encounters error
      }
    }
    fetchBiometrics();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (contextMetrics) {
      setMetrics(contextMetrics);
    }
  }, [contextMetrics]);

  const totalQuests = quests.length;
  const completedQuests = quests.filter((q) => q.is_completed).length;
  const completionPercentage = totalQuests > 0 ? Math.round((completedQuests / totalQuests) * 100) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Athlete Profile & Readiness Card */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436' }}>{greeting}</h2>
            <p style={{ fontSize: '0.85rem', color: '#7f8c8d', marginTop: '2px' }}>
              {athlete?.name || 'Alex Rivera'} ? {athlete?.sport_type || 'Football (Forward)'}
            </p>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(252, 82, 0, 0.1)',
              padding: '0.35rem 0.75rem',
              borderRadius: '999px',
              border: '1px solid rgba(252, 82, 0, 0.25)',
            }}
          >
            <Flame size={18} color="#fc5200" fill="#fc5200" />
            <span style={{ fontWeight: 800, color: '#fc5200', fontSize: '0.85rem' }}>
              {streak} Days
            </span>
          </div>
        </div>

        {/* Readiness and Workload Ratio */}
        <div
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '12px',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.3)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span style={{ fontSize: '0.75rem', color: '#636e72', fontWeight: 600, textTransform: 'uppercase' }}>
              Readiness / ACWR
            </span>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#00b894' }}>
              Optimal (1.15)
            </div>
          </div>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              backgroundColor: '#00b894',
              color: '#ffffff',
              padding: '0.2rem 0.6rem',
              borderRadius: '999px',
            }}
          >
            Prime Conditioning
          </span>
        </div>
      </div>

      {/* Biometric Health Telemetry Grid (from getHealthProvider()) */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436' }}>Today's Biometrics</h3>
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.7rem',
              color: '#00b894',
              fontWeight: 600,
            }}
          >
            <ShieldCheck size={14} />
            {healthProviderName}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem' }}>
          {/* Steps Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0984e3' }}>
              <Activity size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Steps</span>
            </div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {(metrics?.steps ?? 8420).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#7f8c8d', marginTop: '2px' }}>
              Goal: 10,000 ({Math.min(100, Math.round(((metrics?.steps ?? 8420) / 10000) * 100))}%)
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
              {metrics?.sleepMinutes ?? 468} mins (Restorative)
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

          {/* Calories Burned Card */}
          <div className="neu-box" style={{ padding: '1rem', marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fc5200' }}>
              <Zap size={20} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Calories</span>
            </div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '6px' }}>
              {(metrics?.caloriesBurned ?? 2150).toLocaleString()} <span style={{ fontSize: '0.85rem' }}>kcal</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#7f8c8d', marginTop: '2px' }}>
              Active: {(metrics?.activeCalories ?? 580).toLocaleString()} kcal
            </div>
          </div>
        </div>
      </div>

      {/* Today's 1-Day Rolling Quests Summary */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>Today's Quests</h3>
            <span style={{ fontSize: '0.75rem', color: '#7f8c8d' }}>
              {completedQuests} of {totalQuests} tasks completed
            </span>
          </div>
          <span
            style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              color: completionPercentage === 100 ? '#00b894' : '#fc5200',
            }}
          >
            {completionPercentage}%
          </span>
        </div>

        {/* Progress Bar */}
        <div
          style={{
            height: '8px',
            borderRadius: '999px',
            backgroundColor: 'rgba(163,177,198,0.35)',
            boxShadow: 'inset 1px 1px 3px rgba(163,177,198,0.5)',
            overflow: 'hidden',
            marginBottom: '1rem',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${completionPercentage}%`,
              backgroundColor: '#fc5200',
              borderRadius: '999px',
              transition: 'width 0.4s ease',
            }}
          />
        </div>

        {/* Quest Items Preview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {quests.slice(0, 3).map((q) => (
            <div
              key={q.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.65rem 0.85rem',
                borderRadius: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.45)',
                border: '1px solid rgba(255, 255, 255, 0.6)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {q.is_completed ? (
                  <CheckCircle2 size={18} color="#00b894" />
                ) : (
                  <Circle size={18} color="#b2bec3" />
                )}
                <div>
                  <div
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: q.is_completed ? '#7f8c8d' : '#2d3436',
                      textDecoration: q.is_completed ? 'line-through' : 'none',
                    }}
                  >
                    {q.quest_title}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#636e72' }}>
                    {q.duration_minutes}m ? RPE {q.target_rpe} ? {q.task_type}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Navigation Link to Planner */}
        <Link
          to="/planner"
          className="neu-btn"
          style={{
            marginTop: '1rem',
            padding: '0.65rem',
            gap: '6px',
            fontSize: '0.85rem',
            color: '#fc5200',
            textDecoration: 'none',
          }}
        >
          <span>Open Full Planner & Check Off Quests</span>
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
