import { useState } from 'react';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

/**
 * ConfirmationCard — The visual surface of the LangGraph interrupt().
 * Blocks Save Deviation until the user confirms or edits the AI risk assessment.
 */
export default function ConfirmationCard({ assessment, onConfirm, isProcessing }) {
  const [severity, setSeverity] = useState(assessment?.suggested_severity || 'Major');
  const [impact, setImpact] = useState(assessment?.suggested_impact || '');
  const [reasoning] = useState(assessment?.reasoning || '');

  const handleConfirm = () => {
    onConfirm({
      suggested_severity: severity,
      suggested_impact: impact,
      reasoning,
      reviewed_by: 'Quality Officer',
    });
  };

  return (
    <div className="confirmation-card">
      <div className="confirmation-card-header">
        <ShieldAlert size={18} />
        AI Risk Assessment — Confirmation Required
      </div>

      <div className="confirmation-card-body">
        <div className="confirmation-field">
          <label>Suggested Severity:</label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="Minor">Minor</option>
            <option value="Major">Major</option>
            <option value="Critical">Critical</option>
          </select>
        </div>

        <div className="confirmation-field">
          <label>Suggested Impact:</label>
          <input
            type="text"
            value={impact}
            onChange={(e) => setImpact(e.target.value)}
            placeholder="Describe the potential impact..."
          />
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text-secondary)', marginBottom: '7px', display: 'block' }}>
            AI Reasoning:
          </label>
          <div className="confirmation-reasoning">
            {reasoning || 'No reasoning provided.'}
          </div>
        </div>
      </div>

      <div className="confirmation-actions">
        <button
          className="btn btn-success"
          onClick={handleConfirm}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <><div className="spinner"></div> Confirming...</>
          ) : (
            <><CheckCircle2 size={16} /> Confirm & Save</>
          )}
        </button>
      </div>
    </div>
  );
}
