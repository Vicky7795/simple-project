import React from 'react';
import { LayoutGrid, MessageSquare } from 'lucide-react';

interface ModeToggleProps {
  mode: 'form' | 'chat';
  onChange: (mode: 'form' | 'chat') => void;
}

export const ModeToggle: React.FC<ModeToggleProps> = ({ mode, onChange }) => {
  return (
    <div className="toggle-container">
      <button
        onClick={() => onChange('form')}
        className={`toggle-btn ${mode === 'form' ? 'active' : ''}`}
      >
        <LayoutGrid size={16} />
        Structured Form
      </button>
      <button
        onClick={() => onChange('chat')}
        className={`toggle-btn ${mode === 'chat' ? 'active' : ''}`}
      >
        <MessageSquare size={16} />
        Chat with AI
      </button>
    </div>
  );
};
