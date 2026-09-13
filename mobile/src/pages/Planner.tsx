import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { CheckCircle2, Circle, Flame, Sparkles, Clock, Target, RefreshCw } from 'lucide-react';

export default function Planner() {
  const { quests, streak, loading, completeQuest, refreshQuests } = useAthlete();
  const [filter, setFilter] = useState<'all' | 'workout' | 'recovery'>('all');
  const [activeQuestId, setActiveQuestId] = useState<number | null>(null);

  const filteredQuests = quests.filter((q) => {
    if (filter === 'all') return true;
    if (filter === 'workout') return q.task_type.toLowerCase() === 'workout' || q.task_type.toLowerCase() === 'cardio';
    if (filter === 'recovery') return q.task_type.toLowerCase() === 'recovery' || q.task_type.toLowerCase() === 'mobility' || q.task_type.toLowerCase() === 'wellness';
    return true;
  });

  const completedCount = quests.filter((q) => q.is_completed).length;
  const totalCount = quests.length;

  const handleToggle = async (questId: number) => {
    setActiveQuestId(questId);
    try {
      await completeQuest(questId);
    } finally {
      setActiveQuestId(null);
    }
  };

  const todayStr = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Banner */}
      <div className="neu-box" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#fc5200', textTransform: 'uppercase' }}>
              1-Day Rolling Quests
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2d3436', marginTop: '2px' }}>
              {todayStr}
            </h2>
          </div>
          <button
            onClick={() => refreshQuests()}
            className="neu-btn"
            style={{
              padding: '0.45rem 0.65rem',
              borderRadius: '999px',
              fontSize: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Refresh Quests"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Sync</span>
          </button>
        </div>

        {/* Dynamic Streak Incentive Card */}
        <div
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '12px',
            backgroundColor: 'rgba(252, 82, 0, 0.08)',
            border: '1px solid rgba(252, 82, 0, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Flame size={22} color="#fc5200" fill="#fc5200" />
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#2d3436' }}>
                {streak}-Day Active Streak
              </div>
              <div style={{ fontSize: '0.72rem', color: '#636e72' }}>
                {completedCount === totalCount && totalCount > 0
                  ? 'All tasks completed for today! Streak secured!'
                  : 'Check off a quest to protect & advance your streak.'}
              </div>
            </div>
          </div>
          <div style={{ fontWeight: 800, fontSize: '1rem', color: '#fc5200' }}>
            {completedCount}/{totalCount}
          </div>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '1rem' }}>
          {(['all', 'workout', 'recovery'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className="neu-btn"
              style={{
                flex: 1,
                padding: '0.45rem',
                fontSize: '0.75rem',
                borderRadius: '8px',
                color: filter === tab ? '#fc5200' : '#636e72',
                boxShadow:
                  filter === tab
                    ? 'inset 2px 2px 5px rgba(163,177,198,0.6), inset -2px -2px 5px rgba(255,255,255,0.7)'
                    : undefined,
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Quests List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {filteredQuests.length === 0 ? (
          <div className="neu-box" style={{ textAlign: 'center', padding: '2rem', color: '#7f8c8d' }}>
            No quests found in this category.
          </div>
        ) : (
          filteredQuests.map((quest) => {
            const isDone = quest.is_completed;
            const isProcessing = activeQuestId === quest.id;

            return (
              <div
                key={quest.id}
                className="neu-box"
                style={{
                  padding: '1.25rem',
                  marginBottom: 0,
                  borderLeft: isDone ? '4px solid #00b894' : '4px solid #fc5200',
                  opacity: isDone ? 0.85 : 1,
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                  <div>
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '6px',
                        backgroundColor:
                          quest.task_type.toLowerCase() === 'workout'
                            ? 'rgba(252, 82, 0, 0.12)'
                            : 'rgba(9, 132, 227, 0.12)',
                        color: quest.task_type.toLowerCase() === 'workout' ? '#fc5200' : '#0984e3',
                      }}
                    >
                      {quest.task_type}
                    </span>
                    <h3
                      style={{
                        fontSize: '1.05rem',
                        fontWeight: 700,
                        color: isDone ? '#7f8c8d' : '#2d3436',
                        textDecoration: isDone ? 'line-through' : 'none',
                        marginTop: '6px',
                      }}
                    >
                      {quest.quest_title}
                    </h3>
                  </div>

                  {/* Toggle Complete Button */}
                  <button
                    onClick={() => handleToggle(quest.id)}
                    disabled={isProcessing}
                    className="neu-btn"
                    style={{
                      padding: '0.45rem 0.75rem',
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      color: isDone ? '#00b894' : '#fc5200',
                      gap: '4px',
                      flexShrink: 0,
                    }}
                    title={isDone ? 'Mark as incomplete' : 'Complete Quest & Advance Streak'}
                  >
                    {isDone ? (
                      <>
                        <CheckCircle2 size={16} color="#00b894" />
                        <span>Completed</span>
                      </>
                    ) : (
                      <>
                        <Circle size={16} color="#fc5200" />
                        <span>Done</span>
                      </>
                    )}
                  </button>
                </div>

                {quest.session_description && (
                  <p style={{ fontSize: '0.82rem', color: '#636e72', marginTop: '8px', lineHeight: 1.4 }}>
                    {quest.session_description}
                  </p>
                )}

                {/* Badges: Duration & Target RPE */}
                <div style={{ display: 'flex', gap: '12px', marginTop: '10px', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#7f8c8d' }}>
                    <Clock size={13} />
                    <span>{quest.duration_minutes} mins</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#7f8c8d' }}>
                    <Target size={13} />
                    <span>Target RPE: {quest.target_rpe}/10</span>
                  </div>
                </div>

                {/* AI Sports Science Rationale */}
                {quest.agent_reasoning && (
                  <div
                    style={{
                      marginTop: '10px',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.6)',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '6px',
                    }}
                  >
                    <Sparkles size={14} color="#fc5200" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '0.72rem', color: '#636e72', fontStyle: 'italic', lineHeight: 1.3 }}>
                      {quest.agent_reasoning}
                    </span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
