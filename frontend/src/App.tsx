import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Sparkles, BarChart2, CheckCircle2, Clock, FileText, UserCheck } from 'lucide-react';
import { AppDispatch, RootState } from './app/store';
import { fetchInteractions, fetchFollowUps } from './features/interactions/interactionsSlice';
import { fetchHcps, HCP } from './features/hcps/hcpsSlice';

import { ModeToggle } from './components/ModeToggle';
import { HcpSearch } from './components/HcpSearch';
import { InteractionForm } from './components/InteractionForm';
import { InteractionChat } from './components/InteractionChat';

function App() {
  const dispatch = useDispatch<AppDispatch>();
  const [mode, setMode] = useState<'form' | 'chat'>('form');
  const [selectedHcp, setSelectedHcp] = useState<HCP | undefined>(undefined);

  // Redux state
  const interactions = useSelector((state: RootState) => state.interactions.list);
  const followUps = useSelector((state: RootState) => state.interactions.followUps);
  const hcps = useSelector((state: RootState) => state.hcps.list);

  useEffect(() => {
    dispatch(fetchInteractions());
    dispatch(fetchFollowUps());
    dispatch(fetchHcps());
  }, [dispatch]);

  const handleSelectHcp = (hcp: HCP) => {
    setSelectedHcp(hcp);
  };

  const handleFormSuccess = () => {
    dispatch(fetchInteractions());
    dispatch(fetchFollowUps());
  };

  // Stats calculation
  const totalInteractions = interactions.length;
  const pendingFollowupsCount = followUps.length;
  const activeHcpsCount = hcps.length;

  return (
    <div className="app-container">
      {/* Premium Header */}
      <header className="app-header">
        <div className="app-title-group">
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={24} style={{ color: 'var(--brand-primary)' }} />
            AI-First CRM
          </h1>
          <p>HCP Interaction Logging Platform & Sales Assistant</p>
        </div>
        
        {/* Toggle Mode */}
        <ModeToggle mode={mode} onChange={(newMode) => setMode(newMode)} />
      </header>

      {/* Stats Dashboard Row */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ backgroundColor: 'var(--brand-primary-light)', color: 'var(--brand-primary)', padding: '0.75rem', borderRadius: '50%' }}>
            <FileText size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{totalInteractions}</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>Total Interactions</p>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ backgroundColor: 'var(--warning-light)', color: 'var(--warning)', padding: '0.75rem', borderRadius: '50%' }}>
            <Clock size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{pendingFollowupsCount}</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>Pending Follow-ups</p>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ backgroundColor: 'var(--info-light)', color: 'var(--info)', padding: '0.75rem', borderRadius: '50%' }}>
            <UserCheck size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{activeHcpsCount}</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>Active HCP Contacts</p>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ backgroundColor: 'var(--success-light)', color: 'var(--success)', padding: '0.75rem', borderRadius: '50%' }}>
            <BarChart2 size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Vivek N.</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>Active Field Rep</p>
          </div>
        </div>
      </section>

      {/* Main Content Layout */}
      <main className="main-grid">
        {/* Sidebar */}
        <aside>
          <HcpSearch onSelectHcp={handleSelectHcp} selectedHcpId={selectedHcp?.id} />
        </aside>

        {/* Content Workspace */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {mode === 'form' ? (
            <InteractionForm
              preselectedHcpId={selectedHcp?.id}
              onSuccess={handleFormSuccess}
            />
          ) : (
            <InteractionChat />
          )}

          {/* Recent Interactions Feed */}
          <div className="card">
            <div className="card-title">
              <CheckCircle2 size={18} /> Recent Interactions Log
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
              {interactions.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--color-muted)', padding: '1rem 0' }}>No interactions recorded yet. Complete the form or chat with the AI to log one.</p>
              ) : (
                interactions.map((inter) => (
                  <div
                    key={inter.id}
                    style={{
                      padding: '1rem',
                      borderRadius: 'var(--border-radius-sm)',
                      border: '1px solid var(--border-color)',
                      backgroundColor: 'var(--bg-accent)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                          {inter.hcp?.name || `HCP (ID: ${inter.hcp_id})`}
                        </span>
                        <span style={{ fontSize: '0.75rem', padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: 'var(--bg-secondary)', color: 'var(--color-secondary)' }}>
                          {inter.interaction_type}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px',
                          fontWeight: 600,
                          backgroundColor: inter.sentiment === 'positive' ? 'var(--success-light)' : inter.sentiment === 'negative' ? 'var(--danger-light)' : 'var(--border-color)',
                          color: inter.sentiment === 'positive' ? 'var(--success)' : inter.sentiment === 'negative' ? 'var(--danger)' : 'var(--color-secondary)'
                        }}
                      >
                        {inter.sentiment || 'neutral'}
                      </span>
                    </div>

                    {inter.summary && (
                      <p style={{ fontSize: '0.825rem', color: 'var(--color-secondary)', lineHeight: 1.4 }}>
                        {inter.summary}
                      </p>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--color-muted)', marginTop: '0.25rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem' }}>
                      <span>Logged via: <strong>{inter.source}</strong></span>
                      <span>Date: {inter.interaction_date ? new Date(inter.interaction_date).toLocaleDateString() : 'N/A'}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
