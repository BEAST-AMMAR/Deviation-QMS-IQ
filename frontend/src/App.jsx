import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useCreateDraftMutation } from './store/apiSlice';
import { resetDraft, setDraftId, setFieldsFromResponse } from './store/draftSlice';
import { addMessage, clearMessages } from './store/chatSlice';
import Navbar from './components/Navbar';
import DeviationFormPanel from './components/DeviationFormPanel';
import AICopilotPanel from './components/AICopilotPanel';
import AuditTrailDrawer from './components/AuditTrailDrawer';
import PipelineHistoryModal from './components/PipelineHistoryModal';
import LoginPage from './components/LoginPage';
import LegalModal from './components/LegalModal';
import CookieBanner from './components/CookieBanner';

function App() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector((state) => state.auth.isAuthenticated);
  const token = useSelector((state) => state.auth.token);
  const user = useSelector((state) => state.auth.user);
  const draftId = useSelector((state) => state.draft.draftId);
  const [createDraft] = useCreateDraftMutation();
  const [showAudit, setShowAudit] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);

  // Legal Modal & Cookie State
  const [showLegalModal, setShowLegalModal] = useState(false);
  const [legalTab, setLegalTab] = useState('privacy');

  // Key active draft storage strictly per user to ensure complete multi-tenant data isolation
  const userDraftKey = user?.id ? `deviationiq_active_draft_${user.id}` : 'deviationiq_active_draft_guest';

  // Clear in-memory draft whenever authentication state or user identity changes
  useEffect(() => {
    if (!isAuthenticated) {
      dispatch(resetDraft());
      dispatch(clearMessages());
    }
  }, [isAuthenticated, user?.id, dispatch]);

  // Auto-create or resume in-progress draft on mount (survives page refresh - NFR-02)
  useEffect(() => {
    if (!isAuthenticated) return;

    if (!draftId) {
      const savedId = sessionStorage.getItem(userDraftKey);
      const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

      if (savedId) {
        fetch(`/api/drafts/${savedId}`, { headers: authHeaders })
          .then((res) => {
            if (res.ok) return res.json();
            throw new Error('Draft not found');
          })
          .then((data) => {
            if (data.status === 'committed') {
              sessionStorage.removeItem(userDraftKey);
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
                sessionStorage.setItem(userDraftKey, res.draft_id);
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
            sessionStorage.setItem(userDraftKey, res.draft_id);
            dispatch(setDraftId(res.draft_id));
          })
          .catch((err) => {
            console.error('Failed to create draft:', err);
          });
      }
    }
  }, [isAuthenticated, draftId, createDraft, dispatch, token, userDraftKey]);

  // If not authenticated, present the secure 21 CFR Part 11 Login Screen
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const handleOpenHistory = (id) => {
    setSelectedHistoryId(id || null);
    setShowHistory(true);
  };

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar onOpenHistory={() => handleOpenHistory(null)} />
      <div className="main-content" style={{ flex: 1 }}>
        <DeviationFormPanel
          onShowAudit={() => setShowAudit(true)}
          onOpenHistory={handleOpenHistory}
        />
        <AICopilotPanel onOpenHistory={handleOpenHistory} />
      </div>

      {/* Compliance & Regulatory Footer */}
      <footer
        style={{
          padding: '0.6rem 1.5rem',
          background: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          fontSize: '0.76rem',
          color: 'var(--text-muted)',
          zIndex: 10,
        }}
      >
        <div>
          <span>DeviationIQ Enterprise • Indian DPDP Act 2023 & FDA 21 CFR Part 11 Certified</span>
        </div>
        <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
          <button
            type="button"
            onClick={() => {
              setLegalTab('privacy');
              setShowLegalModal(true);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: 'inherit',
            }}
          >
            DPDP Privacy Charter
          </button>
          <button
            type="button"
            onClick={() => {
              setLegalTab('terms');
              setShowLegalModal(true);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: 'inherit',
            }}
          >
            Terms of Service (IT Act)
          </button>
          <button
            type="button"
            onClick={() => {
              setLegalTab('cookies');
              setShowLegalModal(true);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: 'inherit',
            }}
          >
            Cookie Policy
          </button>
          <button
            type="button"
            onClick={() => {
              setLegalTab('dpo');
              setShowLegalModal(true);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: 'inherit',
            }}
          >
            DPO & Grievance Redressal
          </button>
        </div>
      </footer>

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

      <CookieBanner
        onOpenPolicy={(tab) => {
          setLegalTab(tab);
          setShowLegalModal(true);
        }}
      />

      <LegalModal
        isOpen={showLegalModal}
        initialTab={legalTab}
        onClose={() => setShowLegalModal(false)}
      />
    </div>
  );
}

export default App;
