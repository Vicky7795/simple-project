import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Search, PlusCircle, CheckCircle, Calendar, Phone, Mail, MapPin } from 'lucide-react';
import { AppDispatch, RootState } from '../app/store';
import { fetchHcps, createHcp, HCP } from '../features/hcps/hcpsSlice';
import { fetchFollowUps } from '../features/interactions/interactionsSlice';

interface HcpSearchProps {
  onSelectHcp?: (hcp: HCP) => void;
  selectedHcpId?: number;
}

export const HcpSearch: React.FC<HcpSearchProps> = ({ onSelectHcp, selectedHcpId }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { list: hcps, status } = useSelector((state: RootState) => state.hcps);
  const { followUps } = useSelector((state: RootState) => state.interactions);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newHcp, setNewHcp] = useState({
    name: '',
    specialty: 'Cardiology',
    hospital_affiliation: '',
    email: '',
    phone: '',
    preferred_channel: 'visit',
    notes: '',
  });

  useEffect(() => {
    dispatch(fetchHcps());
    dispatch(fetchFollowUps());
  }, [dispatch]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    dispatch(fetchHcps(query));
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHcp.name) return;
    
    await dispatch(createHcp(newHcp));
    setShowAddForm(false);
    setNewHcp({
      name: '',
      specialty: 'Cardiology',
      hospital_affiliation: '',
      email: '',
      phone: '',
      preferred_channel: 'visit',
      notes: '',
    });
    dispatch(fetchHcps());
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* HCP Search Card */}
      <div className="card">
        <div className="card-title" style={{ display: 'flex', justifyContent: 'between', width: '100%' }}>
          <span style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={18} /> HCP Directory
          </span>
          <button 
            onClick={() => setShowAddForm(!showAddForm)}
            style={{ border: 'none', background: 'none', color: 'var(--brand-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem', fontWeight: 600 }}
          >
            <PlusCircle size={14} /> Add HCP
          </button>
        </div>

        {showAddForm ? (
          <form onSubmit={handleAddSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
              <label className="form-label">Doctor Name *</label>
              <input
                type="text"
                placeholder="Dr. Vivek Nair"
                required
                className="form-control"
                style={{ padding: '0.5rem 0.75rem' }}
                value={newHcp.name}
                onChange={e => setNewHcp({...newHcp, name: e.target.value})}
              />
            </div>
            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
              <label className="form-label">Specialty</label>
              <select
                className="form-control"
                style={{ padding: '0.5rem 0.75rem' }}
                value={newHcp.specialty}
                onChange={e => setNewHcp({...newHcp, specialty: e.target.value})}
              >
                <option value="Cardiology">Cardiology</option>
                <option value="Endocrinology">Endocrinology</option>
                <option value="Oncology">Oncology</option>
                <option value="Pediatrics">Pediatrics</option>
                <option value="General Medicine">General Medicine</option>
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: '0.5rem' }}>
              <label className="form-label">Hospital</label>
              <input
                type="text"
                placeholder="Apollo Clinic"
                className="form-control"
                style={{ padding: '0.5rem 0.75rem' }}
                value={newHcp.hospital_affiliation}
                onChange={e => setNewHcp({...newHcp, hospital_affiliation: e.target.value})}
              />
            </div>
            <div className="form-control-row" style={{ gap: '0.5rem' }}>
              <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-control"
                  style={{ padding: '0.5rem 0.75rem' }}
                  value={newHcp.email}
                  onChange={e => setNewHcp({...newHcp, email: e.target.value})}
                />
              </div>
              <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                <label className="form-label">Phone</label>
                <input
                  type="text"
                  className="form-control"
                  style={{ padding: '0.5rem 0.75rem' }}
                  value={newHcp.phone}
                  onChange={e => setNewHcp({...newHcp, phone: e.target.value})}
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <button type="submit" className="btn btn-primary" style={{ flex: 1, padding: '0.5rem' }}>Save</button>
              <button type="button" onClick={() => setShowAddForm(false)} className="btn btn-secondary" style={{ flex: 1, padding: '0.5rem' }}>Cancel</button>
            </div>
          </form>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search by name, specialty..."
                className="form-control"
                style={{ paddingLeft: '2.25rem' }}
                value={searchQuery}
                onChange={handleSearchChange}
              />
              <Search size={14} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted)' }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
              {status === 'loading' && <p style={{ fontSize: '0.875rem', color: 'var(--color-secondary)' }}>Loading HCPs...</p>}
              {hcps.length === 0 && status !== 'loading' && <p style={{ fontSize: '0.875rem', color: 'var(--color-muted)' }}>No doctors found.</p>}
              
              {hcps.map((hcp) => {
                const isSelected = selectedHcpId === hcp.id;
                return (
                  <div
                    key={hcp.id}
                    onClick={() => onSelectHcp?.(hcp)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: 'var(--border-radius-sm)',
                      border: `1px solid ${isSelected ? 'var(--brand-primary)' : 'var(--border-color)'}`,
                      backgroundColor: isSelected ? 'var(--brand-primary-light)' : 'var(--bg-accent)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem', color: isSelected ? 'var(--brand-primary)' : 'var(--color-primary)' }}>{hcp.name}</span>
                      <span style={{ fontSize: '0.75rem', padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: 'var(--bg-secondary)', color: 'var(--color-secondary)', fontWeight: 500 }}>
                        {hcp.specialty || 'General'}
                      </span>
                    </div>
                    {hcp.hospital_affiliation && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--color-secondary)', marginTop: '0.25rem' }}>
                        <MapPin size={10} /> {hcp.hospital_affiliation}
                      </div>
                    )}
                    {(hcp.phone || hcp.email) && isSelected && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--color-secondary)', borderTop: '1px solid var(--border-color)', paddingTop: '0.25rem' }}>
                        {hcp.phone && <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Phone size={10} /> {hcp.phone}</span>}
                        {hcp.email && <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Mail size={10} /> {hcp.email}</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Follow-ups Card */}
      <div className="card">
        <div className="card-title">
          <Calendar size={18} /> Outstanding Follow-ups
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '250px', overflowY: 'auto' }}>
          {followUps.length === 0 ? (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-muted)' }}>No pending follow-ups. Good job!</p>
          ) : (
            followUps.map((fu) => (
              <div
                key={fu.id}
                style={{
                  padding: '0.75rem',
                  borderRadius: 'var(--border-radius-sm)',
                  backgroundColor: 'var(--bg-accent)',
                  borderLeft: '4px solid var(--warning)',
                  fontSize: '0.8rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                  <span>{fu.hcp_name}</span>
                  <span style={{ color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    <Calendar size={10} /> {fu.follow_up_date}
                  </span>
                </div>
                <div style={{ color: 'var(--color-secondary)', marginTop: '0.25rem' }}>
                  {fu.topics && fu.topics.length > 0 ? `Topic: ${fu.topics.join(', ')}` : 'Routine update'}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
