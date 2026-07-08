import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Send, FileText, Sparkles, Smile, X, AlertCircle } from 'lucide-react';
import { AppDispatch, RootState } from '../app/store';
import { logInteraction, editInteraction, fetchFollowUps } from '../features/interactions/interactionsSlice';
import { fetchHcps } from '../features/hcps/hcpsSlice';

interface InteractionFormProps {
  preselectedHcpId?: number;
  editingInteractionId?: number;
  onSuccess?: () => void;
}

export const InteractionForm: React.FC<InteractionFormProps> = ({
  preselectedHcpId,
  editingInteractionId,
  onSuccess,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const hcps = useSelector((state: RootState) => state.hcps.list);
  const interactions = useSelector((state: RootState) => state.interactions.list);

  // Form Fields State
  const [hcpId, setHcpId] = useState<number | ''>('');
  const [type, setType] = useState('visit');
  const [sentiment, setSentiment] = useState('neutral');
  const [topicInput, setTopicInput] = useState('');
  const [topics, setTopics] = useState<string[]>([]);
  const [productInput, setProductInput] = useState('');
  const [products, setProducts] = useState<string[]>([]);
  
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [followUpDate, setFollowUpDate] = useState('');
  
  // Samples State
  const [sampleProduct, setSampleProduct] = useState('');
  const [sampleQty, setSampleQty] = useState<number>(5);
  const [samples, setSamples] = useState<Record<string, number>>({});

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // 1. Handle preselected HCP or editing state load
  useEffect(() => {
    if (preselectedHcpId) {
      setHcpId(preselectedHcpId);
    }
  }, [preselectedHcpId]);

  useEffect(() => {
    if (editingInteractionId) {
      const match = interactions.find((i) => i.id === editingInteractionId);
      if (match) {
        setHcpId(match.hcp_id);
        setType(match.interaction_type);
        setSentiment(match.sentiment || 'neutral');
        setTopics(match.topics_discussed || []);
        setProducts(match.products_discussed || []);
        setFollowUpRequired(match.follow_up_required);
        setFollowUpDate(match.follow_up_date ? match.follow_up_date.split('T')[0] : '');
        setSamples(match.samples_distributed || {});
      }
    }
  }, [editingInteractionId, interactions]);

  // 2. Add/Remove tags helpers
  const handleAddTopic = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && topicInput.trim()) {
      e.preventDefault();
      if (!topics.includes(topicInput.trim())) {
        setTopics([...topics, topicInput.trim()]);
      }
      setTopicInput('');
    }
  };

  const handleRemoveTopic = (indexToRemove: number) => {
    setTopics(topics.filter((_, i) => i !== indexToRemove));
  };

  const handleAddProduct = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && productInput.trim()) {
      e.preventDefault();
      if (!products.includes(productInput.trim())) {
        setProducts([...products, productInput.trim()]);
      }
      setProductInput('');
    }
  };

  const handleRemoveProduct = (indexToRemove: number) => {
    setProducts(products.filter((_, i) => i !== indexToRemove));
  };

  // 3. Samples handlers
  const handleAddSample = (e: React.MouseEvent) => {
    e.preventDefault();
    if (sampleProduct.trim() && sampleQty > 0) {
      setSamples({
        ...samples,
        [sampleProduct.trim()]: (samples[sampleProduct.trim()] || 0) + sampleQty,
      });
      setSampleProduct('');
      setSampleQty(5);
    }
  };

  const handleRemoveSample = (productKey: string) => {
    const updated = { ...samples };
    delete updated[productKey];
    setSamples(updated);
  };

  // 4. Form Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hcpId) {
      setErrorMsg('Please select a Healthcare Professional.');
      return;
    }

    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    const payload = {
      hcp_id: Number(hcpId),
      interaction_type: type,
      topics_discussed: topics,
      products_discussed: products,
      sentiment,
      follow_up_required: followUpRequired,
      follow_up_date: followUpRequired && followUpDate ? followUpDate : undefined,
      samples_distributed: Object.keys(samples).length > 0 ? samples : undefined,
      source: 'form',
    };

    try {
      if (editingInteractionId) {
        await dispatch(editInteraction({ id: editingInteractionId, data: payload })).unwrap();
        setSuccessMsg('Interaction updated successfully.');
      } else {
        await dispatch(logInteraction(payload)).unwrap();
        setSuccessMsg('Interaction logged successfully.');
        // Reset Form if new
        setTopics([]);
        setProducts([]);
        setFollowUpRequired(false);
        setFollowUpDate('');
        setSamples({});
      }
      
      dispatch(fetchFollowUps());
      
      if (onSuccess) {
        setTimeout(onSuccess, 1000);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'An error occurred during submission.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-title">
        <FileText size={18} />
        {editingInteractionId ? 'Edit Interaction Log' : 'Log New Interaction'}
      </div>

      {errorMsg && (
        <div style={{ backgroundColor: 'var(--danger-light)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--border-radius-sm)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div style={{ backgroundColor: 'var(--success-light)', color: 'var(--success)', padding: '0.75rem', borderRadius: 'var(--border-radius-sm)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontSize: '0.85rem', fontWeight: 600 }}>
          <Sparkles size={16} />
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* HCP Autocomplete / Dropdown */}
        <div className="form-group">
          <label className="form-label">Healthcare Professional (HCP) *</label>
          <select
            className="form-control"
            value={hcpId}
            onChange={(e) => setHcpId(e.target.value ? Number(e.target.value) : '')}
            required
          >
            <option value="">-- Select HCP --</option>
            {hcps.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.specialty || 'General'}) - {h.hospital_affiliation || 'No Affiliation'}
              </option>
            ))}
          </select>
        </div>

        {/* Type & Sentiment Row */}
        <div className="form-control-row">
          <div className="form-group">
            <label className="form-label">Interaction Type</label>
            <select
              className="form-control"
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              <option value="visit">Physical Visit</option>
              <option value="call">Phone Call</option>
              <option value="email">Email</option>
              <option value="conference">Conference / Meeting</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">HCP Sentiment</label>
            <select
              className="form-control"
              value={sentiment}
              onChange={(e) => setSentiment(e.target.value)}
            >
              <option value="positive">Positive / Highly Receptive</option>
              <option value="neutral">Neutral / Informative</option>
              <option value="negative">Negative / Uninterested</option>
            </select>
          </div>
        </div>

        {/* Topics Tag Input */}
        <div className="form-group">
          <label className="form-label">Topics Discussed (Press Enter to add)</label>
          <input
            type="text"
            className="form-control"
            placeholder="e.g. Clinical trials, efficacy, safety updates"
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            onKeyDown={handleAddTopic}
          />
          <div className="tag-container">
            {topics.map((t, i) => (
              <span key={i} className="tag">
                {t}
                <button type="button" onClick={() => handleRemoveTopic(i)} className="tag-remove"><X size={12} /></button>
              </span>
            ))}
          </div>
        </div>

        {/* Products Tag Input */}
        <div className="form-group">
          <label className="form-label">Products/Drugs Discussed (Press Enter to add)</label>
          <input
            type="text"
            className="form-control"
            placeholder="e.g. CardioShield, Glynase"
            value={productInput}
            onChange={(e) => setProductInput(e.target.value)}
            onKeyDown={handleAddProduct}
          />
          <div className="tag-container">
            {products.map((p, i) => (
              <span key={i} className="tag" style={{ backgroundColor: 'var(--info-light)', color: 'var(--info)' }}>
                {p}
                <button type="button" onClick={() => handleRemoveProduct(i)} className="tag-remove" style={{ color: 'var(--info)' }}><X size={12} /></button>
              </span>
            ))}
          </div>
        </div>

        {/* Follow-up fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-sm)', padding: '1rem', backgroundColor: 'var(--bg-primary)' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={followUpRequired}
              onChange={(e) => setFollowUpRequired(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--brand-primary)' }}
            />
            Schedule a follow-up action?
          </label>
          
          {followUpRequired && (
            <div className="form-group" style={{ marginTop: '0.5rem', marginBottom: 0 }}>
              <label className="form-label">Follow-up Date</label>
              <input
                type="date"
                required
                className="form-control"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
              />
            </div>
          )}
        </div>

        {/* Samples Section */}
        <div style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-sm)', padding: '1rem', backgroundColor: 'var(--bg-primary)' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>Distribute Drug Samples</h4>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Product Sample Name"
              style={{ flex: 2, padding: '0.5rem' }}
              value={sampleProduct}
              onChange={(e) => setSampleProduct(e.target.value)}
            />
            <input
              type="number"
              className="form-control"
              placeholder="Qty"
              min="1"
              style={{ flex: 1, padding: '0.5rem' }}
              value={sampleQty}
              onChange={(e) => setSampleQty(Number(e.target.value))}
            />
            <button type="button" onClick={handleAddSample} className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
              Add
            </button>
          </div>

          {Object.keys(samples).length > 0 && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', marginTop: '0.5rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--color-secondary)' }}>
                  <th style={{ padding: '0.25rem 0' }}>Sample Product</th>
                  <th style={{ padding: '0.25rem 0', textAlign: 'center' }}>Quantity</th>
                  <th style={{ padding: '0.25rem 0', textAlign: 'right' }}>Remove</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(samples).map(([prod, qty]) => (
                  <tr key={prod} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.4rem 0', fontWeight: 500 }}>{prod}</td>
                    <td style={{ padding: '0.4rem 0', textAlign: 'center', fontWeight: 600 }}>{qty}</td>
                    <td style={{ padding: '0.4rem 0', textAlign: 'right' }}>
                      <button type="button" onClick={() => handleRemoveSample(prod)} style={{ border: 'none', background: 'none', color: 'var(--danger)', cursor: 'pointer' }}><X size={14} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', height: '44px', marginTop: '0.5rem' }}
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : editingInteractionId ? 'Update Log' : 'Save Interaction Log'}
        </button>
      </form>
    </div>
  );
};
