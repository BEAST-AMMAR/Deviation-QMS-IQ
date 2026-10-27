import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useCreateDraftMutation } from './store/apiSlice';
import { setDraftId } from './store/draftSlice';
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

  // Auto-create a draft on mount
  useEffect(() => {
    if (!draftId) {
      createDraft()
        .unwrap()
        .then((res) => {
          dispatch(setDraftId(res.draft_id));
        })
        .catch((err) => {
          console.error('Failed to create draft:', err);
        });
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
