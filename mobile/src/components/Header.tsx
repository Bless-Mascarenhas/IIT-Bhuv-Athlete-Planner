import { useState } from 'react';
import { Flame, Save, X, Loader2 } from 'lucide-react';
import { useAthlete } from '../context/AthleteContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Header() {
  const { athlete, streak, greeting } = useAthlete();
  const { userId, isGuest, login } = useAuth();
  
  const [showModal, setShowModal] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUpgrade = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !userId) {
      setError('Please fill in all fields.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    const success = await api.upgradeGuest(userId, athlete?.name || 'Athlete', email, password);
    if (success) {
      // Re-login as a normal user to clear isGuest
      await login(userId, false);
      setShowModal(false);
    } else {
      setError('Failed to upgrade account. Try again.');
    }
    setLoading(false);
  };

  return (
    <header
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.85rem 1.25rem',
        backgroundColor: 'var(--bg)',
        boxShadow: '0 4px 12px rgba(163, 177, 198, 0.35)',
        zIndex: 20,
        borderBottom: '1px solid rgba(255, 255, 255, 0.4)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span
          style={{
            fontWeight: '900',
            fontSize: '1.45rem',
            color: '#fc5200', // Strava orange brand tone
            fontStyle: 'italic',
            letterSpacing: '-1px',
            lineHeight: 1.1,
          }}
        >
          Pace
        </span>
        <span style={{ fontSize: '0.72rem', color: '#7f8c8d', fontWeight: '600' }}>
          {greeting}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {isGuest && (
          <button
            onClick={() => setShowModal(true)}
            className="neu-btn"
            style={{
              padding: '0.45rem 0.8rem',
              color: '#0984e3',
              fontSize: '0.75rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Save size={14} />
            Save Account
          </button>
        )}
        <div
          className="neu-box"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0.4rem 0.8rem',
            marginBottom: 0,
            borderRadius: '999px',
            backgroundColor: 'var(--bg)',
            boxShadow: 'inset 2px 2px 4px rgba(163,177,198,0.5), inset -2px -2px 4px rgba(255,255,255,0.7)',
          }}
          title={`Current streak: ${streak} consecutive days`}
        >
          <span
            style={{
              fontWeight: '800',
              fontSize: '1rem',
              color: '#2d3436',
            }}
          >
            {streak}
          </span>
          <Flame size={19} color="#fc5200" fill="#fc5200" />
        </div>
      </div>

      {/* Upgrade Modal */}
      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="neu-box" style={{ width: '100%', maxWidth: '400px', padding: '1.5rem', position: 'relative' }}>
            <button 
              onClick={() => setShowModal(false)}
              className="neu-btn"
              style={{ position: 'absolute', top: '1rem', right: '1rem', padding: '0.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#636e72' }}
            >
              <X size={16} />
            </button>

            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#2d3436', marginBottom: '0.5rem' }}>Secure Your Data</h3>
            <p style={{ fontSize: '0.85rem', color: '#636e72', marginBottom: '1.5rem', lineHeight: 1.4 }}>
              You're currently using a temporary account. Add an email and password to permanently save your data, streaks, and training plans to the cloud.
            </p>

            <form onSubmit={handleUpgrade} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#636e72', marginLeft: '0.5rem' }}>Email</label>
                <input 
                  type="email" 
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="neu-inset"
                  placeholder="athlete@pace.ai"
                  style={{ padding: '0.85rem', borderRadius: '10px', border: 'none', outline: 'none', backgroundColor: 'transparent' }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, color: '#636e72', marginLeft: '0.5rem' }}>Password</label>
                <input 
                  type="password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="neu-inset"
                  placeholder="••••••••"
                  style={{ padding: '0.85rem', borderRadius: '10px', border: 'none', outline: 'none', backgroundColor: 'transparent' }}
                />
              </div>

              {error && <div style={{ color: '#d63031', fontSize: '0.8rem', textAlign: 'center', fontWeight: 600 }}>{error}</div>}

              <button 
                type="submit" 
                className="neu-btn"
                disabled={loading}
                style={{ padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#0984e3', marginTop: '0.5rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
              >
                {loading ? <Loader2 size={18} className="spin" /> : <Save size={18} />}
                {loading ? 'Securing Account...' : 'Secure Account'}
              </button>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}
