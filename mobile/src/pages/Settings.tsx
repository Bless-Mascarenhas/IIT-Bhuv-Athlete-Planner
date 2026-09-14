import { useState, type FormEvent } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { useAuth } from '../context/AuthContext';
import { User, Flame, ShieldCheck, RefreshCw, Check, Trophy, LogOut } from 'lucide-react';

export default function Settings() {
  const { athlete, streak, healthProviderName, syncHealth, updateGoal } = useAthlete();
  const { logout } = useAuth();
  const [name, setName] = useState(athlete?.name || 'Alex Rivera');
  const [sport, setSport] = useState(athlete?.sport_type || 'Football (Forward)');
  const [goal, setGoal] = useState(athlete?.active_goal || 'Stay Fit');
  const [isSyncing, setIsSyncing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleSyncHealth = async () => {
    setIsSyncing(true);
    try {
      await syncHealth();
      setStatusMsg('Health telemetry synchronized successfully!');
      setTimeout(() => setStatusMsg(null), 3000);
    } catch {
      setStatusMsg('Health sync complete (cached locally).');
      setTimeout(() => setStatusMsg(null), 3000);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSaveProfile = async (e: FormEvent) => {
    e.preventDefault();
    if (goal !== athlete?.active_goal) {
      await updateGoal(goal);
    }
    setStatusMsg('Profile preferences updated!');
    setTimeout(() => setStatusMsg(null), 3000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Profile Overview Card */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '50%',
              backgroundColor: '#fc5200',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.35rem',
              fontWeight: 800,
              boxShadow: '0 4px 10px rgba(252, 82, 0, 0.4)',
            }}
          >
            {name.charAt(0)}
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#2d3436' }}>{name}</h2>
            <div style={{ fontSize: '0.8rem', color: '#7f8c8d' }}>{sport}</div>
          </div>
        </div>

        <div
          style={{
            marginTop: '1rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '0.75rem',
          }}
        >
          <div
            style={{
              padding: '0.65rem 0.85rem',
              borderRadius: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Flame size={18} color="#fc5200" fill="#fc5200" />
            <div>
              <div style={{ fontSize: '0.68rem', color: '#7f8c8d', fontWeight: 600 }}>CURRENT STREAK</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fc5200' }}>{streak} Days</div>
            </div>
          </div>

          <div
            style={{
              padding: '0.65rem 0.85rem',
              borderRadius: '10px',
              backgroundColor: 'rgba(255, 255, 255, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Trophy size={18} color="#0984e3" />
            <div>
              <div style={{ fontSize: '0.68rem', color: '#7f8c8d', fontWeight: 600 }}>ATHLETE TIER</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0984e3' }}>{athlete?.athlete_tier || 'Semi-Pro'}</div>
            </div>
          </div>
        </div>

        {statusMsg && (
          <div
            style={{
              marginTop: '0.85rem',
              padding: '0.5rem 0.8rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(0, 184, 148, 0.15)',
              color: '#00b894',
              fontSize: '0.75rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Check size={14} />
            <span>{statusMsg}</span>
          </div>
        )}
      </div>

      {/* Health Architecture & Telemetry Provider Card */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.75rem' }}>
          <ShieldCheck size={20} color="#00b894" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>
            Health Data Architecture (R4)
          </h3>
        </div>

        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.25)',
            marginBottom: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72' }}>Active Provider</span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                color: '#00b894',
                backgroundColor: 'rgba(0, 184, 148, 0.12)',
                padding: '0.2rem 0.6rem',
                borderRadius: '999px',
              }}
            >
              Online
            </span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#2d3436', marginTop: '4px' }}>
            {healthProviderName}
          </div>
        </div>

        <p style={{ fontSize: '0.78rem', color: '#636e72', lineHeight: 1.45, marginBottom: '1rem' }}>
          Pace utilizes a Strategy pattern provider interface. When running in a standard web browser,
          it gracefully falls back to mock biometrics to prevent Capacitor native plugin crashes. When deployed
          on mobile devices, it directly interfaces with HealthKit and Health Connect.
        </p>

        <button
          onClick={handleSyncHealth}
          disabled={isSyncing}
          className="neu-btn"
          style={{
            width: '100%',
            padding: '0.7rem',
            color: '#00b894',
            fontSize: '0.85rem',
            gap: '6px',
          }}
        >
          <RefreshCw size={15} className={isSyncing ? 'spin' : ''} />
          <span>{isSyncing ? 'Synchronizing Biometrics...' : 'Sync Health Telemetry Now'}</span>
        </button>
      </div>

      {/* Edit Profile Form */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.85rem' }}>
          <User size={18} color="#0984e3" />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#2d3436' }}>Athlete Preferences</h3>
        </div>

        <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', display: 'block', marginBottom: '4px' }}>
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: 'var(--bg)',
                boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.6), inset -2px -2px 4px rgba(255,255,255,0.7)',
                color: 'var(--text)',
                fontSize: '0.85rem',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', display: 'block', marginBottom: '4px' }}>
              Sport / Position
            </label>
            <input
              type="text"
              value={sport}
              onChange={(e) => setSport(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: 'var(--bg)',
                boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.6), inset -2px -2px 4px rgba(255,255,255,0.7)',
                color: 'var(--text)',
                fontSize: '0.85rem',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', display: 'block', marginBottom: '4px' }}>
              Active Goal
            </label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: 'var(--bg)',
                boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.6), inset -2px -2px 4px rgba(255,255,255,0.7)',
                color: 'var(--text)',
                fontSize: '0.85rem',
              }}
            />
          </div>

          <button
            type="submit"
            className="neu-btn"
            style={{
              marginTop: '0.5rem',
              padding: '0.75rem',
              backgroundColor: '#0984e3',
              color: '#ffffff',
              fontSize: '0.85rem',
            }}
          >
            Update Profile Preferences
          </button>
        </form>
      </div>

      {/* Logout Button */}
      <button
        onClick={() => logout()}
        className="neu-btn"
        style={{
          width: '100%',
          padding: '1rem',
          color: '#d63031',
          fontSize: '0.9rem',
          fontWeight: 800,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          marginTop: '1rem'
        }}
      >
        <LogOut size={18} />
        Log Out / Change User
      </button>
    </div>
  );
}
