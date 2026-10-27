import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { updateFieldManually, resetDraft, setDraftId, setCommitted } from '../store/draftSlice';
import { clearMessages, addMessage } from '../store/chatSlice';
import {
  useResetDraftMutation,
  useCreateDraftMutation,
  useUpdateDraftFieldsMutation,
  useCommitDirectMutation,
  useConfirmAssessmentMutation,
} from '../store/apiSlice';
import {
  ClipboardList,
  RotateCcw,
  ScrollText,
  Save,
  CheckCircle2,
  PlusCircle,
  AlertCircle,
  History,
} from 'lucide-react';
import FormField from './FormField';

const STATUS_LABELS = {
  idle: 'New Draft',
  pending_triage: 'Pending Triage',
  extracting: 'Extracting...',
  awaiting_confirmation: 'Awaiting Confirmation',
  ready_to_commit: 'Ready to Commit',
  committed: 'Committed',
};

export default function DeviationFormPanel({ onShowAudit, onOpenHistory }) {
  const dispatch = useDispatch();
  const { fields, status, draftId, isLoading, changedFields, pendingAssessment } = useSelector((s) => s.draft);
  const [resetDraftApi] = useResetDraftMutation();
  const [createDraft] = useCreateDraftMutation();
  const [updateDraftFieldsApi] = useUpdateDraftFieldsMutation();
  const [commitDirectApi, { isLoading: isCommitting }] = useCommitDirectMutation();
  const [confirmAssessmentApi] = useConfirmAssessmentMutation();

  const [validationError, setValidationError] = useState(null);
  const isCommitted = status === 'committed';

  const handleFieldChange = (fieldName, value) => {
    if (isCommitted) return;
    dispatch(updateFieldManually({ fieldName, value }));
    setValidationError(null);

    // Synchronize to backend draft store so AI and database remain aligned (BUG-04)
    if (draftId) {
      updateDraftFieldsApi({ draftId, fieldName, value }).catch((err) => {
        console.warn('Field sync to backend failed:', err);
      });
    }
  };

  const handleStartNextDeviation = async () => {
    setValidationError(null);
    dispatch(resetDraft());
    dispatch(clearMessages());
    sessionStorage.removeItem('deviationiq_active_draft_id');
    try {
      const res = await createDraft().unwrap();
      sessionStorage.setItem('deviationiq_active_draft_id', res.draft_id);
      dispatch(setDraftId(res.draft_id));
    } catch (e) {
      console.error('Failed to create new draft:', e);
    }
  };

  const handleReset = async () => {
    if (draftId && !isCommitted) {
      try {
        await resetDraftApi(draftId).unwrap();
      } catch (e) { /* ok */ }
    }
    await handleStartNextDeviation();
  };

  const getMissingFields = () => {
    const missing = [];
    if (!fields.site_plant?.value?.trim()) missing.push('Site / Plant');
    if (!fields.date_of_occurrence?.value?.trim()) missing.push('Date of Occurrence');
    if (!fields.title?.value?.trim()) missing.push('Title / Short Description');
    if (!fields.source?.value?.trim()) missing.push('Source');
    if (!fields.detailed_description?.value?.trim()) missing.push('Detailed Description');
    if (!fields.initial_impact?.value?.trim()) missing.push('Initial Impact');
    if (!fields.initial_severity?.value?.trim()) missing.push('Initial Severity');
    return missing;
  };

  const handleSaveDeviation = async () => {
    if (isCommitted || isCommitting) return;
    setValidationError(null);

    const missing = getMissingFields();
    if (missing.length > 0) {
      setValidationError(`Missing required fields: ${missing.join(', ')}`);
      return;
    }

    try {
      if (status === 'awaiting_confirmation' && pendingAssessment) {
        await confirmAssessmentApi({
          draftId,
          assessment: {
            suggested_severity: fields.initial_severity?.value || pendingAssessment.suggested_severity || 'Minor',
            suggested_impact: fields.initial_impact?.value || pendingAssessment.suggested_impact || 'No immediate impact',
            reasoning: pendingAssessment.reasoning || 'Confirmed by operator',
            reviewed_by: 'Quality Officer',
          },
        }).unwrap();
      } else {
        await commitDirectApi({
          draftId,
          site_plant: fields.site_plant?.value,
          date_of_occurrence: fields.date_of_occurrence?.value,
          title: fields.title?.value,
          source: fields.source?.value,
          related_product: fields.related_product?.value,
          batch_lot: fields.batch_lot?.value,
          detailed_description: fields.detailed_description?.value,
          initial_impact: fields.initial_impact?.value,
          initial_severity: fields.initial_severity?.value,
          reviewed_by: 'Quality Officer',
          reasoning: 'Human manual verification and direct submission.',
        }).unwrap();
      }

      dispatch(setCommitted());
      dispatch(addMessage({
        role: 'assistant',
        content: `Deviation record committed and locked into regulatory audit trail. All fields saved (21 CFR Part 11).`,
      }));
    } catch (err) {
      console.error('Save deviation failed:', err);
      const msg = err?.data?.detail || 'Failed to save deviation. Please verify all fields and try again.';
      setValidationError(msg);
    }
  };


  return (
    <div className="form-panel">
      {/* Header */}
      <div className="form-panel-header">
        <div>
          <div className="form-panel-title">
            <ClipboardList size={20} />
            Log Deviation
          </div>
          <div className="form-panel-subtitle">
            Record any unexpected event or departure from approved procedures
          </div>
        </div>
        <div className={`status-badge ${status}`}>
          {STATUS_LABELS[status] || status}
        </div>
      </div>

      {/* Body */}
      <div className="form-panel-body">
        {/* Section 1: Deviation Information */}
        <div className="form-section">
          <div className="form-section-title">
            <span className="section-number">1</span>
            Deviation Information
          </div>
          <div className="form-grid">
            <FormField
              label="Site / Plant"
              required
              fieldName="site_plant"
              fieldData={fields.site_plant}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('site_plant')}
              placeholder="Awaiting AI extraction..."
            />
            <FormField
              label="Date of Occurrence"
              required
              fieldName="date_of_occurrence"
              fieldData={fields.date_of_occurrence}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('date_of_occurrence')}
              type="date"
              placeholder="Awaiting AI extraction..."
            />
            <FormField
              label="Title / Short Description"
              required
              fieldName="title"
              fieldData={fields.title}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('title')}
              placeholder="Awaiting AI extraction..."
            />
            <FormField
              label="Source"
              required
              fieldName="source"
              fieldData={fields.source}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('source')}
              type="select"
              options={['', 'Shift Log', 'Lab Report', 'Operator Report', 'Email', 'Audit Finding', 'Other']}
              placeholder="Awaiting AI extraction..."
            />
            <FormField
              label="Related Product / Material"
              fieldName="related_product"
              fieldData={fields.related_product}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('related_product')}
              placeholder="Awaiting AI extraction..."
            />
            <FormField
              label="Batch / Lot Number"
              fieldName="batch_lot"
              fieldData={fields.batch_lot}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('batch_lot')}
              placeholder="Awaiting AI extraction..."
            />
          </div>
        </div>

        {/* Section 2: Deviation Details */}
        <div className="form-section">
          <div className="form-section-title">
            <span className="section-number">2</span>
            Deviation Details
          </div>
          <div className="form-grid">
            <div className="full-width">
              <FormField
                label="Detailed Description"
                required
                fieldName="detailed_description"
                fieldData={fields.detailed_description}
                onChange={handleFieldChange}
                disabled={isCommitted}
                isChanged={changedFields.includes('detailed_description')}
                type="textarea"
                maxLength={2000}
                placeholder="Awaiting AI extraction..."
              />
            </div>
            <FormField
              label="Initial Impact"
              required
              fieldName="initial_impact"
              fieldData={fields.initial_impact}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('initial_impact')}
              type="select"
              options={['', 'No Impact', 'Product Quality', 'Patient Safety', 'Data Integrity', 'Regulatory', 'Other']}
              placeholder="Set via AI assessment..."
            />
            <FormField
              label="Initial Severity"
              required
              fieldName="initial_severity"
              fieldData={fields.initial_severity}
              onChange={handleFieldChange}
              disabled={isCommitted}
              isChanged={changedFields.includes('initial_severity')}
              type="select"
              options={['', 'Minor', 'Major', 'Critical']}
              placeholder="Set via AI assessment..."
            />
          </div>
        </div>
      </div>

      {/* Validation Feedback */}
      {validationError && (
        <div className="form-validation-alert">
          <AlertCircle size={15} />
          <span>{validationError}</span>
        </div>
      )}

      {/* Footer */}
      <div className="form-panel-footer">
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-danger btn-sm" onClick={handleReset}>
            <RotateCcw size={14} />
            {isCommitted ? 'Reset / New Draft' : 'Reset Form'}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={onShowAudit}>
            <ScrollText size={14} />
            Audit Trail
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => onOpenHistory?.(draftId)} title="View past completed pipeline sessions">
            <History size={14} />
            Pipeline History
          </button>
        </div>

        {isCommitted ? (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button className="btn btn-outline-success" disabled>
              <CheckCircle2 size={16} /> Committed
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => onOpenHistory?.(draftId)}>
              <History size={14} /> View in History
            </button>
            <button className="btn btn-primary" onClick={handleStartNextDeviation}>
              <PlusCircle size={16} /> Log Next Deviation
            </button>
          </div>
        ) : (
          <button
            className="btn btn-success"
            onClick={handleSaveDeviation}
            disabled={isCommitting}
            title="Save and commit deviation record"
          >
            {isCommitting ? (
              <><div className="spinner"></div> Saving...</>
            ) : (
              <><Save size={16} /> Save Deviation</>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

