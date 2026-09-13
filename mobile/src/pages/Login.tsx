import React, { useState } from 'react';
import { LogIn, UserPlus, Play } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isRegistering) {
        if (!name || !email || !password) {
          setError('Please fill out all fields.');
          setLoading(false);
          return;
        }
        const userId = await api.register(name, email, password);
        if (userId) {
          await login(userId);
        } else {
          setError('Registration failed. Try again.');
        }
      } else {
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
      }
    } catch {
      setError('An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const userId = await api.loginGuest();
      if (userId) {
        await login(userId);
      } else {
        setError('Guest login failed.');
      }
    } catch {
      setError('An error occurred.');
    } finally {
      setLoading(false);
    }
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
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isRegistering && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Full Name</label>
              <input 
                type="text" 
                value={name}
                onChange={e => setName(e.target.value)}
                className="neu-inset"
                placeholder="Alex Rivera"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent' }}
              />
            </div>
          )}
          
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
            {isRegistering ? <UserPlus size={20} /> : <LogIn size={20} />}
            {isRegistering ? 'Create Account' : 'Log In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', marginBottom: '1.5rem' }}>
          <span 
            onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
            style={{ color: '#fc5200', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}
          >
            {isRegistering ? 'Already have an account? Log In' : 'Need an account? Sign Up'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'rgba(0,0,0,0.1)' }} />
          <span style={{ fontSize: '0.85rem', color: '#b2bec3', fontWeight: 600 }}>OR</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'rgba(0,0,0,0.1)' }} />
        </div>

        <button 
          onClick={handleGuestLogin}
          className="neu-btn"
          disabled={loading}
          style={{ width: '100%', padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#2d3436' }}
        >
          {loading ? 'Logging in...' : 'Login as Guest'}
        </button>
      </div>
    </div>
  );
}
