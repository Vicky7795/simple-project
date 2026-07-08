import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Send, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import { AppDispatch, RootState } from '../app/store';
import { sendMessage, addLocalUserMessage, resetSession } from '../features/chat/chatSlice';
import { fetchInteractions, fetchFollowUps } from '../features/interactions/interactionsSlice';
import { SummaryCard } from './SummaryCard';

export const InteractionChat: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { messages, status, threadId, lastAgentResponse, error } = useSelector((state: RootState) => state.chat);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, status]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status === 'loading') return;

    const messageText = input.trim();
    setInput('');
    
    // Add user message locally first
    dispatch(addLocalUserMessage(messageText));
    
    // Send to agent
    await dispatch(sendMessage({ thread_id: threadId, message: messageText }));
    
    // Refresh global list and follow-ups in background
    dispatch(fetchInteractions());
    dispatch(fetchFollowUps());
  };

  const handleResetSession = () => {
    dispatch(resetSession());
  };

  return (
    <div className="chat-window">
      {/* Chat Header */}
      <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--bg-accent)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={16} style={{ color: 'var(--brand-primary)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Conversational Logger Agent</span>
        </div>
        <button
          onClick={handleResetSession}
          className="btn btn-secondary"
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', borderRadius: '20px' }}
        >
          <RefreshCw size={12} /> New Thread
        </button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div style={{ margin: 'auto', textAlign: 'center', padding: '2rem', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Sparkles size={32} style={{ color: 'var(--brand-primary)', margin: '0 auto' }} />
            <h4 style={{ fontWeight: 600 }}>Logging with AI</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-secondary)' }}>
              Type naturally to log visits, edit existing records, lookup info, or schedule followups.
            </p>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-muted)', backgroundColor: 'var(--bg-accent)', padding: '0.5rem', borderRadius: 'var(--border-radius-sm)', textAlign: 'left', marginTop: '1rem' }}>
              <strong>Try saying:</strong>
              <div style={{ marginTop: '0.25rem', fontStyle: 'italic' }}>
                "Met Dr. Sharma today, positive visit, we discussed CardioShield drug launch, he wants 10 samples"
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            const isLastMessage = index === messages.length - 1;
            
            return (
              <div key={index} style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <div className={`chat-bubble ${isUser ? 'user' : 'agent'}`}>
                  {msg.content}
                </div>
                
                {/* Render Summary Card inline for successful tool usage next to the response bubble */}
                {!isUser && isLastMessage && lastAgentResponse && lastAgentResponse.tool_used && (
                  <div style={{ alignSelf: 'flex-start', width: '90%' }}>
                    <SummaryCard
                      toolResult={lastAgentResponse.tool_result}
                      toolUsed={lastAgentResponse.tool_used}
                      onUpdate={() => {
                        // Refresh the messages
                        dispatch(fetchInteractions());
                        dispatch(fetchFollowUps());
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })
        )}

        {status === 'loading' && (
          <div className="chat-bubble agent" style={{ display: 'inline-flex', alignItems: 'center' }}>
            <div className="typing-indicator">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </div>
          </div>
        )}

        {error && (
          <div style={{ backgroundColor: 'var(--danger-light)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--border-radius-sm)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', margin: '0.5rem 0' }}>
            <AlertCircle size={14} />
            Agent Connection Error: {error}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input form */}
      <form onSubmit={handleSend} className="chat-input-area">
        <input
          type="text"
          placeholder="Describe your HCP interaction here..."
          className="form-control"
          style={{ flex: 1, borderRadius: '24px' }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={status === 'loading'}
        />
        <button
          type="submit"
          className="btn btn-primary"
          style={{ borderRadius: '50%', width: '40px', height: '40px', padding: 0, flexShrink: 0 }}
          disabled={!input.trim() || status === 'loading'}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
};
