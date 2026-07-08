import React, { useState } from 'react';
import { Calendar, Tag, Gift, Edit2 } from 'lucide-react';
import { InteractionForm } from './InteractionForm';

interface SummaryCardProps {
  toolResult: any;
  toolUsed: string;
  onUpdate?: () => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ toolResult, toolUsed, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);

  if (!toolResult || !toolResult.success) {
    return null;
  }

  // Handle different tools
  if (toolUsed === 'lookup_hcp') {
    const matches = toolResult.matches || [];
    return (
      <div className="summary-card" style={{ borderStyle: 'solid', borderColor: 'var(--info)' }}>
        <div className="summary-card-header">
          <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>HCP Lookup Results</span>
          <span className="summary-card-badge" style={{ backgroundColor: 'var(--info)' }}>{matches.length} found</span>
        </div>
        {matches.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: 'var(--color-secondary)' }}>No doctors found matching the query.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {matches.map((hcp: any) => (
              <div key={hcp.id} style={{ fontSize: '0.8rem', padding: '0.5rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontWeight: 600 }}>{hcp.name} ({hcp.specialty})</div>
                <div style={{ color: 'var(--color-secondary)', fontSize: '0.75rem' }}>{hcp.hospital}</div>
                {hcp.recent_interactions && hcp.recent_interactions.length > 0 && (
                  <div style={{ marginTop: '0.25rem', fontSize: '0.7rem', color: 'var(--color-muted)', borderTop: '1px solid #f1f5f9', paddingTop: '0.25rem' }}>
                    Last visit: {hcp.recent_interactions[0].date} - {hcp.recent_interactions[0].sentiment}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (toolUsed === 'summarize_interaction_history') {
    return (
      <div className="summary-card" style={{ borderStyle: 'solid', borderColor: 'var(--brand-primary)' }}>
        <div className="summary-card-header">
          <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>Relationship Summary: {toolResult.hcp_name}</span>
          <span className="summary-card-badge">{toolResult.total_interactions} visits</span>
        </div>
        <div 
          style={{ fontSize: '0.8rem', color: 'var(--color-primary)', whiteSpace: 'pre-line', lineHeight: '1.4' }}
          dangerouslySetInnerHTML={{ __html: toolResult.summary }}
        />
      </div>
    );
  }

  // log_interaction and edit_interaction
  const details = toolResult.details || {};
  const interactionId = toolResult.interaction_id;
  const hcpName = toolResult.hcp?.name || details.hcp_name || 'HCP';

  if (isEditing && interactionId) {
    return (
      <div style={{ marginTop: '1rem', border: '1px solid var(--brand-primary)', borderRadius: 'var(--border-radius-md)', padding: '0.25rem', backgroundColor: 'var(--bg-secondary)' }}>
        <InteractionForm
          editingInteractionId={interactionId}
          onSuccess={() => {
            setIsEditing(false);
            if (onUpdate) onUpdate();
          }}
        />
        <div style={{ padding: '0 1.25rem 1.25rem 1.25rem' }}>
          <button onClick={() => setIsEditing(false)} className="btn btn-secondary" style={{ width: '100%', padding: '0.5rem' }}>
            Cancel Editing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="summary-card">
      <div className="summary-card-header">
        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
          {toolUsed === 'edit_interaction' ? 'Updated Log Details' : 'New Log Details'}
        </span>
        <span className="summary-card-badge" style={{ backgroundColor: details.sentiment === 'positive' ? 'var(--success)' : details.sentiment === 'negative' ? 'var(--danger)' : 'var(--color-secondary)' }}>
          {details.sentiment || 'neutral'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.8rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', fontWeight: 600 }}>
          <span>HCP: {hcpName}</span>
          <span style={{ color: 'var(--color-secondary)' }}>Type: {details.type}</span>
        </div>

        {details.summary && (
          <div style={{ color: 'var(--color-secondary)', fontStyle: 'italic', backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px', borderLeft: '3px solid var(--brand-primary)' }}>
            "{details.summary}"
          </div>
        )}

        {details.topics && details.topics.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--color-muted)' }}><Tag size={12} /> Topics:</span>
            {details.topics.map((t: string, i: number) => (
              <span key={i} style={{ padding: '0.1rem 0.4rem', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '10px', fontSize: '0.75rem' }}>{t}</span>
            ))}
          </div>
        )}

        {details.follow_up_required && details.follow_up_date && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--warning)', fontWeight: 500 }}>
            <Calendar size={12} /> Follow-up scheduled: {details.follow_up_date}
          </div>
        )}

        {details.samples && Object.keys(details.samples).length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--color-muted)' }}><Gift size={12} /> Samples:</span>
            {Object.entries(details.samples).map(([k, v]: any) => (
              <span key={k} style={{ padding: '0.1rem 0.4rem', backgroundColor: 'var(--success-light)', color: 'var(--success)', borderRadius: '4px', fontWeight: 600, fontSize: '0.75rem' }}>{k} (x{v})</span>
            ))}
          </div>
        )}

        {interactionId && (
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem', marginTop: '0.25rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setIsEditing(true)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', border: 'none', background: 'none', color: 'var(--brand-primary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.75rem' }}
            >
              <Edit2 size={12} /> Edit Details
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
