import React, { useState } from 'react';
import { LogIn, UserPlus, Play } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isExistingUser, setIsExistingUser] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (!email || !password) {
        setError('Please enter email and password.');
        setLoading(false);
        return;
      }
      const userId = await api.login(email, password);
      if (userId) {
        await login(userId);
      } else {
        setError('Invalid credentials.');
      }
    } catch {
      setError('An error occurred. Server might be waking up.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewUser = () => {
    // Navigate straight to the local onboarding form
    navigate('/onboarding');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <div style={{ 
          display: 'inline-flex', 
          padding: '1rem', 
          borderRadius: '50%', 
          backgroundColor: '#fc5200',
          boxShadow: '8px 8px 16px rgba(0,0,0,0.1), -8px -8px 16px rgba(255,255,255,0.8)',
          marginBottom: '1rem'
        }}>
          <Play size={40} color="white" fill="white" />
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, color: '#2d3436', margin: 0, letterSpacing: '-1px' }}>PACE</h1>
        <p style={{ color: '#7f8c8d', fontSize: '1rem', fontWeight: 600, marginTop: '0.5rem' }}>Autonomous Athlete Planner</p>
      </div>

      <div className="neu-box" style={{ padding: '1.5rem' }}>
        
        {!isExistingUser ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button 
              onClick={handleNewUser}
              className="neu-btn"
              style={{ width: '100%', padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#0984e3', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              <UserPlus size={20} /> New User
            </button>
            <div style={{ textAlign: 'center', margin: '0.5rem 0' }}>
              <span style={{ fontSize: '0.85rem', color: '#b2bec3', fontWeight: 600 }}>OR</span>
            </div>
            <button 
              onClick={() => setIsExistingUser(true)}
              className="neu-btn"
              style={{ width: '100%', padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#2d3436', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              <LogIn size={20} /> Existing User
            </button>
          </div>
        ) : (
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Email</label>
              <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="neu-inset"
                placeholder="athlete@pace.ai"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Password</label>
              <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="neu-inset"
                placeholder="••••••••"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent' }}
              />
            </div>

            {error && <div style={{ color: '#d63031', fontSize: '0.85rem', textAlign: 'center', fontWeight: 600 }}>{error}</div>}

            <button 
              type="submit" 
              className="neu-btn"
              disabled={loading}
              style={{ padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#0984e3', marginTop: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              {loading ? 'Logging in...' : 'Log In'}
            </button>

            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <span 
                onClick={() => { setIsExistingUser(false); setError(''); }}
                style={{ color: '#fc5200', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}
              >
                Go back
              </span>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
