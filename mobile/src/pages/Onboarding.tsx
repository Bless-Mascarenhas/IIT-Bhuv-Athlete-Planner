import React, { useState } from 'react';
import { ArrowRight, Activity, Target } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Onboarding() {
  const { userId, completeOnboarding } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    sport_type: 'General Fitness',
    position: 'Athlete',
    active_goal: 'Stay Fit'
  });

  const handleNext = () => setStep(step + 1);

  const handleSubmit = async () => {
    setLoading(true);
    if (userId) {
      await api.updateProfile(userId, formData);
    }
    await completeOnboarding();
    setLoading(false);
    navigate('/dashboard');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#2d3436', margin: 0 }}>
          {step === 1 ? 'Welcome to Pace.' : step === 2 ? 'Your Sport.' : 'Your Goal.'}
        </h1>
        <p style={{ color: '#7f8c8d', fontSize: '1rem', fontWeight: 600, marginTop: '0.5rem' }}>
          {step === 1 ? 'Let\'s set up your profile.' : step === 2 ? 'Customize your AI planner.' : 'What are we working towards?'}
        </p>
      </div>

      <div className="neu-box" style={{ padding: '2rem' }}>
        
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>What should we call you?</label>
              <input 
                type="text" 
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                className="neu-inset"
                placeholder="First Name"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent', fontSize: '1rem' }}
              />
            </div>
            <button 
              onClick={handleNext}
              className="neu-btn"
              disabled={!formData.name}
              style={{ padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#fc5200', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              Continue <ArrowRight size={20} />
            </button>
          </div>
        )}

        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Primary Sport</label>
              <select 
                value={formData.sport_type}
                onChange={e => setFormData({ ...formData, sport_type: e.target.value })}
                className="neu-inset"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent', fontSize: '1rem', color: '#2d3436' }}
              >
                <option value="General Fitness">General Fitness</option>
                <option value="Football">Football / Soccer</option>
                <option value="Basketball">Basketball</option>
                <option value="Running">Running / Track</option>
                <option value="Swimming">Swimming</option>
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Role / Position</label>
              <input 
                type="text" 
                value={formData.position}
                onChange={e => setFormData({ ...formData, position: e.target.value })}
                className="neu-inset"
                placeholder="e.g. Forward, Sprinter"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent', fontSize: '1rem' }}
              />
            </div>
            <button 
              onClick={handleNext}
              className="neu-btn"
              style={{ padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#fc5200', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              Continue <ArrowRight size={20} />
            </button>
          </div>
        )}

        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 700, color: '#636e72', marginLeft: '1rem' }}>Current 7-Day Goal</label>
              <input 
                type="text" 
                value={formData.active_goal}
                onChange={e => setFormData({ ...formData, active_goal: e.target.value })}
                className="neu-inset"
                placeholder="e.g. Build Endurance"
                style={{ padding: '1rem', borderRadius: '12px', border: 'none', outline: 'none', backgroundColor: 'transparent', fontSize: '1rem' }}
              />
            </div>
            
            <button 
              onClick={handleSubmit}
              disabled={loading || !formData.active_goal}
              className="neu-btn"
              style={{ padding: '1rem', borderRadius: '12px', fontWeight: 800, color: '#00b894', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              {loading ? <Activity size={20} className="spin-anim" /> : <Target size={20} />}
              {loading ? 'Generating AI Plan...' : 'Complete Setup'}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
