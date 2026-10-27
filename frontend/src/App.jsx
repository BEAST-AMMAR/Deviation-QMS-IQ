import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useCreateDraftMutation } from './store/apiSlice';
import { setDraftId, setFieldsFromResponse } from './store/draftSlice';
import { addMessage, clearMessages } from './store/chatSlice';
import Navbar from './components/Navbar';
import DeviationFormPanel from './components/DeviationFormPanel';
import AICopilotPanel from './components/AICopilotPanel';
import AuditTrailDrawer from './components/AuditTrailDrawer';
import PipelineHistoryModal from './components/PipelineHistoryModal';

function App() {
  const dispatch = useDispatch();
  const draftId = useSelector((state) => state.draft.draftId);
  const [createDraft] = useCreateDraftMutation();
  const [showAudit, setShowAudit] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);

  // Auto-create or resume in-progress draft on mount (survives page refresh - NFR-02)
  useEffect(() => {
    if (!draftId) {
      const savedId = sessionStorage.getItem('deviationiq_active_draft_id');
      if (savedId) {
        fetch(`/api/drafts/${savedId}`)
          .then((res) => {
            if (res.ok) return res.json();
            throw new Error('Draft not found');
          })
          .then((data) => {
            if (data.status === 'committed') {
              sessionStorage.removeItem('deviationiq_active_draft_id');
              throw new Error('Already committed');
            }
            dispatch(setDraftId(savedId));
            dispatch(setFieldsFromResponse({
              fields: data.fields,
              pendingAssessment: data.pending_assessment,
              status: data.status,
            }));
            if (data.messages && data.messages.length > 0) {
              dispatch(clearMessages());
              data.messages.forEach((m) => {
                dispatch(addMessage(m));
              });
            }
          })
          .catch(() => {
            createDraft()
              .unwrap()
              .then((res) => {
                sessionStorage.setItem('deviationiq_active_draft_id', res.draft_id);
                dispatch(setDraftId(res.draft_id));
              })
              .catch((err) => {
                console.error('Failed to create draft:', err);
              });
          });
      } else {
        createDraft()
          .unwrap()
          .then((res) => {
            sessionStorage.setItem('deviationiq_active_draft_id', res.draft_id);
            dispatch(setDraftId(res.draft_id));
          })
          .catch((err) => {
            console.error('Failed to create draft:', err);
          });
      }
    }
  }, [draftId, createDraft, dispatch]);

  const handleOpenHistory = (id) => {
    setSelectedHistoryId(id || null);
    setShowHistory(true);
  };

  return (
    <div className="app-container">
      <Navbar onOpenHistory={() => handleOpenHistory(null)} />
      <div className="main-content">
        <DeviationFormPanel
          onShowAudit={() => setShowAudit(true)}
          onOpenHistory={handleOpenHistory}
        />
        <AICopilotPanel onOpenHistory={handleOpenHistory} />
      </div>
      {showAudit && (
        <AuditTrailDrawer
          deviationId={draftId}
          onClose={() => setShowAudit(false)}
        />
      )}
      <PipelineHistoryModal
        isOpen={showHistory}
        initialSelectedId={selectedHistoryId}
        onClose={() => setShowHistory(false)}
      />
    </div>
  );
}

export default App;
