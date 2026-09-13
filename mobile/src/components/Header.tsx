import { Flame } from 'lucide-react';
import { useAthlete } from '../context/AthleteContext';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const { streak, greeting } = useAthlete();
  const { userId, logout } = useAuth();

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
        {userId === 1 && (
          <button
            onClick={() => logout()}
            className="neu-btn"
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '999px',
              fontSize: '0.75rem',
              fontWeight: 800,
              color: '#0984e3'
            }}
          >
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
    </header>
  );
}
