import { useState, useEffect, type FormEvent } from 'react';
import { api, type CalendarEvent } from '../services/api';
import { Trophy, Dumbbell, Plus, X, Clock, Check, Sparkles, CalendarDays } from 'lucide-react';

export default function Calendar() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formType, setFormType] = useState('match');
  const [formDate, setFormDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });
  const [formDuration, setFormDuration] = useState(90);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadEvents() {
      setLoading(true);
      try {
        const data = await api.getEvents(1);
        if (isMounted) {
          setEvents(data);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadEvents();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    if (!formDate) return;

    setSubmitting(true);
    try {
      const newEvent: CalendarEvent = {
        athlete_id: 1,
        event_date: formDate,
        event_type: formType,
        duration_minutes: Number(formDuration) || 60,
      };

      await api.addEvent(newEvent);

      setEvents((prev) => [
        ...prev,
        {
          ...newEvent,
          id: Date.now(),
        },
      ]);

      setShowAddForm(false);
      setStatusMsg(Added  on !);
      setTimeout(() => setStatusMsg(null), 3500);
    } finally {
      setSubmitting(false);
    }
  };

  const sortedEvents = [...events].sort((a, b) => a.event_date.localeCompare(b.event_date));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Banner */}
      <div className=neu-box style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#fc5200', textTransform: 'uppercase' }}>
              Fixture & Schedule
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '2px' }}>
              Upcoming Events
            </h2>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className=neu-btn
            style={{
              padding: '0.45rem 0.8rem',
              borderRadius: '999px',
              fontSize: '0.75rem',
              color: showAddForm ? '#ff7675' : '#fc5200',
              gap: '4px',
            }}
          >
            {showAddForm ? <X size={15} /> : <Plus size={15} />}
            <span>{showAddForm ? 'Cancel' : 'Add Event'}</span>
          </button>
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

      {/* Add Event Form Modal/Drawer */}
      {showAddForm && (
        <div className=neu-box style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#2d3436', marginBottom: '0.75rem' }}>
            Schedule New Fixture
          </h3>
          <form onSubmit={handleAddEvent} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', display: 'block', marginBottom: '4px' }}>
                Event Type
              </label>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value)}
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
              >
                <option value=match>Match / Fixture</option>
                <option value=training>Team Training Session</option>
                <option value=recovery>Active Recovery Session</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#636e72', display: 'block', marginBottom: '4px' }}>
                Event Date
              </label>
              <input
                type=date
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
                required
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
                Duration (Minutes)
              </label>
              <input
                type=number
                value={formDuration}
                onChange={(e) => setFormDuration(Number(e.target.value))}
                min=10
                max=240
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
              type=submit
              disabled={submitting}
              className=neu-btn
              style={{
                marginTop: '0.5rem',
                padding: '0.75rem',
                backgroundColor: '#fc5200',
                color: '#ffffff',
                fontSize: '0.85rem',
              }}
            >
              {submitting ? 'Saving Event...' : 'Save to Schedule'}
            </button>
          </form>
        </div>
      )}

      {/* Events List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {loading ? (
          <div className=neu-box style={{ textAlign: 'center', padding: '1.5rem', color: '#7f8c8d' }}>
            Loading athlete fixtures...
          </div>
        ) : sortedEvents.length === 0 ? (
          <div className=neu-box style={{ textAlign: 'center', padding: '2rem', color: '#7f8c8d' }}>
            No upcoming events scheduled. Tap 'Add Event' or message Pace Coach in the Chat tab!
          </div>
        ) : (
          sortedEvents.map((evt, idx) => {
            const isMatch = evt.event_type.toLowerCase() === 'match';
            const isTraining = evt.event_type.toLowerCase() === 'training';

            return (
              <div
                key={evt.id || idx}
                className=neu-box
                style={{
                  padding: '1.1rem 1.25rem',
                  marginBottom: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderLeft: isMatch
                    ? '4px solid #fc5200'
                    : isTraining
                    ? '4px solid #0984e3'
                    : '4px solid #00b894',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '10px',
                      backgroundColor: isMatch
                        ? 'rgba(252, 82, 0, 0.12)'
                        : isTraining
                        ? 'rgba(9, 132, 227, 0.12)'
                        : 'rgba(0, 184, 148, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: isMatch ? '#fc5200' : isTraining ? '#0984e3' : '#00b894',
                    }}
                  >
                    {isMatch ? (
                      <Trophy size={20} />
                    ) : isTraining ? (
                      <Dumbbell size={20} />
                    ) : (
                      <Sparkles size={20} />
                    )}
                  </div>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#2d3436' }}>
                      {isMatch ? 'Competitive Match' : isTraining ? 'Team Training' : 'Active Recovery'}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px', color: '#7f8c8d', fontSize: '0.75rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <CalendarDays size={13} />
                        {evt.event_date}
                      </span>
                      <span>•</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <Clock size={13} />
                        {evt.duration_minutes || 60}m
                      </span>
                    </div>
                  </div>
                </div>

                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: isMatch ? '#fc5200' : isTraining ? '#0984e3' : '#00b894',
                    backgroundColor: 'rgba(255, 255, 255, 0.6)',
                    padding: '0.25rem 0.6rem',
                    borderRadius: '999px',
                  }}
                >
                  {evt.event_type}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
