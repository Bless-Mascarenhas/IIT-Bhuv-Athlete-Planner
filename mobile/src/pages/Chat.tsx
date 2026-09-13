import { useState, useRef, useEffect, type FormEvent } from 'react';
import { api, type ChatResponse } from '../services/api';
import { Send, Bot, User, Sparkles, Calendar, Zap, HelpCircle } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  intent?: string;
  actionTaken?: string;
}

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-0',
    sender: 'assistant',
    text: "Hello Alex! I am Pace AI, your autonomous performance coach. You can log schedule changes ('I have a match tomorrow'), report soreness, or ask for recovery advice.",
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    intent: 'General QA',
  },
];

const QUICK_PROMPTS = [
  'I have a match tomorrow',
  'Feeling fatigued in hamstrings',
  'How should I recover after a match?',
  'Optimal hydration before training',
];

let messageSeq = 0;
function generateMsgId(prefix: string): string {
  messageSeq += 1;
  return `${prefix}-${messageSeq}`;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || loading) return;

    const userMessage: ChatMessage = {
      id: generateMsgId('user'),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const res: ChatResponse = await api.sendChatMessage(text, 1);
      const assistantMessage: ChatMessage = {
        id: generateMsgId('ai'),
        sender: 'assistant',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: res.intent,
        actionTaken: res.action_taken,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      const fallbackMessage: ChatMessage = {
        id: generateMsgId('ai-err'),
        sender: 'assistant',
        text: "Pace Coach received your request and logged it locally.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: 'General QA',
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSendMessage();
  };

  const renderIntentBadge = (intent?: string) => {
    if (!intent) return null;

    let badgeColor = '#0984e3';
    let icon = <HelpCircle size={12} />;

    if (intent === 'Update Calendar') {
      badgeColor = '#fc5200';
      icon = <Calendar size={12} />;
    } else if (intent === 'Update Plan') {
      badgeColor = '#6c5ce7';
      icon = <Zap size={12} />;
    }

    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '0.68rem',
          fontWeight: 700,
          color: badgeColor,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: '0.15rem 0.5rem',
          borderRadius: '999px',
          boxShadow: '1px 1px 3px rgba(163,177,198,0.3)',
          marginBottom: '6px',
        }}
      >
        {icon}
        <span>{intent}</span>
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 170px)' }}>
      {/* Quick Prompts Bar */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          overflowX: 'auto',
          paddingBottom: '0.65rem',
          marginBottom: '0.5rem',
          flexShrink: 0,
        }}
      >
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => handleSendMessage(prompt)}
            disabled={loading}
            className="neu-btn"
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: '999px',
              fontSize: '0.72rem',
              whiteSpace: 'nowrap',
              color: '#fc5200',
              fontWeight: 600,
              gap: '4px',
            }}
          >
            <Sparkles size={12} color="#fc5200" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Message History */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
        }}
      >
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';

          return (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '88%',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
              }}
            >
              {!isUser && renderIntentBadge(msg.intent)}

              <div
                className="neu-box"
                style={{
                  padding: '0.75rem 1rem',
                  marginBottom: 0,
                  borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  backgroundColor: isUser ? '#fc5200' : 'var(--bg)',
                  color: isUser ? '#ffffff' : 'var(--text)',
                  boxShadow: isUser
                    ? '4px 4px 10px rgba(252, 82, 0, 0.35)'
                    : '5px 5px 10px rgb(163,177,198,0.5), -5px -5px 10px rgba(255,255,255, 0.6)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  {isUser ? <User size={13} color="#ffffff" /> : <Bot size={14} color="#fc5200" />}
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: isUser ? 'rgba(255,255,255,0.85)' : '#7f8c8d',
                    }}
                  >
                    {isUser ? 'You' : 'Pace AI Coach'} • {msg.timestamp}
                  </span>
                </div>

                <div style={{ fontSize: '0.88rem', lineHeight: 1.45 }}>{msg.text}</div>

                {msg.actionTaken && (
                  <div
                    style={{
                      marginTop: '8px',
                      padding: '0.35rem 0.6rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(252, 82, 0, 0.1)',
                      border: '1px solid rgba(252, 82, 0, 0.25)',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: '#fc5200',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Sparkles size={12} />
                    <span>Action: {msg.actionTaken}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div style={{ alignSelf: 'flex-start', maxWidth: '75%' }}>
            <div className="neu-box" style={{ padding: '0.65rem 1rem', marginBottom: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#7f8c8d', fontSize: '0.8rem' }}>
                <Bot size={16} color="#fc5200" />
                <span>Pace AI is reasoning...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          gap: '8px',
          paddingTop: '0.65rem',
          flexShrink: 0,
        }}
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Tell Pace Coach or ask advice..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            borderRadius: '999px',
            border: 'none',
            backgroundColor: 'var(--bg)',
            boxShadow: 'inset 3px 3px 6px rgba(163,177,198,0.6), inset -3px -3px 6px rgba(255,255,255,0.7)',
            fontSize: '0.88rem',
            outline: 'none',
            color: 'var(--text)',
          }}
        />
        <button
          type="submit"
          disabled={loading || !inputText.trim()}
          className="neu-btn"
          style={{
            width: '46px',
            height: '46px',
            borderRadius: '50%',
            backgroundColor: '#fc5200',
            color: '#ffffff',
            flexShrink: 0,
            opacity: !inputText.trim() || loading ? 0.6 : 1,
          }}
          title="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
