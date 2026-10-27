import { useState, useRef, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useDropzone } from 'react-dropzone';
import {
  BrainCircuit,
  Upload,
  Send,
  FileText,
  AlertCircle,
  CheckCircle2,
  PlusCircle,
  ShieldCheck,
  History,
  Download,
} from 'lucide-react';
import {
  useSendMessageMutation,
  useUploadFileMutation,
  useConfirmAssessmentMutation,
  useCreateDraftMutation,
} from '../store/apiSlice';
import { setFieldsFromResponse, setLoading, setCommitted, resetDraft, setDraftId } from '../store/draftSlice';
import { addMessage, setProcessing, clearMessages } from '../store/chatSlice';
import ConfirmationCard from './ConfirmationCard';


export default function AICopilotPanel({ onOpenHistory }) {
  const dispatch = useDispatch();
  const draftId = useSelector((s) => s.draft.draftId);
  const status = useSelector((s) => s.draft.status);
  const pendingAssessment = useSelector((s) => s.draft.pendingAssessment);
  const messages = useSelector((s) => s.chat.messages);
  const isProcessing = useSelector((s) => s.chat.isProcessing);

  const [inputText, setInputText] = useState('');
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const [sendMessage] = useSendMessageMutation();
  const [uploadFile] = useUploadFileMutation();
  const [confirmAssessment] = useConfirmAssessmentMutation();
  const [createDraft] = useCreateDraftMutation();

  const handleStartNextDeviation = async () => {
    dispatch(resetDraft());
    dispatch(clearMessages());
    try {
      const res = await createDraft().unwrap();
      dispatch(setDraftId(res.draft_id));
      dispatch(addMessage({
        role: 'assistant',
        content: 'Welcome to DeviationIQ. Upload a document or paste report text to begin extraction for your next deviation.',
      }));
    } catch (e) {
      console.error('Failed to create new draft:', e);
    }
  };

  // Auto-scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, status]);


  // Handle text message submission
  const handleSendMessage = async () => {
    const text = inputText.trim();
    if (!text || !draftId || isProcessing) return;

    setInputText('');
    dispatch(addMessage({ role: 'user', content: text }));
    dispatch(setProcessing(true));
    dispatch(setLoading(true));

    try {
      const result = await sendMessage({ draftId, text }).unwrap();
      dispatch(setFieldsFromResponse({
        fields: result.fields,
        changedFields: result.changed_fields,
        pendingAssessment: result.pending_assessment,
        status: result.status,
      }));
      dispatch(addMessage({ role: 'assistant', content: result.chat_reply }));
    } catch (err) {
      console.error('Send message failed:', err);
      dispatch(addMessage({
        role: 'assistant',
        content: 'An error occurred while processing your request. Please try again.',
      }));
    } finally {
      dispatch(setProcessing(false));
      dispatch(setLoading(false));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle file upload via dropzone
  const onDrop = useCallback(async (acceptedFiles) => {
    if (!draftId || acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    dispatch(addMessage({ role: 'user', content: `Uploading: ${file.name}` }));
    dispatch(setProcessing(true));
    dispatch(setLoading(true));

    try {
      const result = await uploadFile({ draftId, file }).unwrap();
      dispatch(setFieldsFromResponse({
        fields: result.fields,
        changedFields: result.changed_fields,
        pendingAssessment: result.pending_assessment,
        status: result.status,
      }));
      dispatch(addMessage({ role: 'assistant', content: result.chat_reply }));
    } catch (err) {
      console.error('Upload failed:', err);
      const detail = err?.data?.detail || 'Failed to process the uploaded file. Please ensure it contains extractable text.';
      dispatch(addMessage({
        role: 'assistant',
        content: detail,
      }));
    } finally {
      dispatch(setProcessing(false));
      dispatch(setLoading(false));
    }
  }, [draftId, uploadFile, dispatch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: isProcessing || status === 'committed',
  });

  // Handle confirmation
  const handleConfirm = async (assessment) => {
    if (!draftId) return;
    dispatch(setProcessing(true));

    try {
      await confirmAssessment({ draftId, assessment }).unwrap();
      dispatch(setCommitted());
      dispatch(addMessage({
        role: 'assistant',
        content: `Deviation committed successfully.\n\nSeverity: ${assessment.suggested_severity}\nThe record is now locked and read-only.`,
      }));
    } catch (err) {
      console.error('Confirm failed:', err);
      dispatch(addMessage({
        role: 'assistant',
        content: 'Confirmation failed. Please try again.',
      }));
    } finally {
      dispatch(setProcessing(false));
    }
  };

  const isCommitted = status === 'committed';

  return (
    <div className="ai-panel">
      {/* Header */}
      <div className="ai-panel-header">
        <div className="ai-panel-title">
          <BrainCircuit size={20} />
          AI Deviation Assistant
          <span className="beta-tag">BETA</span>
        </div>
      </div>

      {/* Upload Dropzone */}
      {!isCommitted && (
        <div
          {...getRootProps()}
          className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="upload-zone-icon">
            <Upload size={28} strokeWidth={1.5} />
          </div>
          <div className="upload-zone-text">
            Drag & drop a file or <strong>browse</strong>
          </div>
          <div className="upload-zone-hint">
            Supports PDF, DOCX, TXT (max 10 MB)
          </div>
        </div>
      )}

      {/* Chat Thread */}
      <div className="chat-thread">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {msg.timestamp && (
              <div className="msg-time">
                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
        ))}

        {/* Processing indicator */}
        {isProcessing && (
          <div className="chat-message assistant" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            Analyzing...
          </div>
        )}

        {/* Confirmation Card (interrupt UI) */}
        {pendingAssessment && status === 'awaiting_confirmation' && (
          <ConfirmationCard
            assessment={pendingAssessment}
            onConfirm={handleConfirm}
            isProcessing={isProcessing}
          />
        )}

        {/* Post-Commit Compliance & Workflow Transition Card (BUG-01 Fix) */}
        {isCommitted && (
          <div className="post-commit-card">
            <div className="post-commit-header">
              <ShieldCheck size={28} className="post-commit-icon" />
              <div>
                <div className="post-commit-title">Record Committed & Cryptographically Locked</div>
                <div className="post-commit-sub">21 CFR Part 11 Electronic Record Protection Active</div>
              </div>
            </div>
            <div className="post-commit-meta">
              <span>Sealed Record:</span>
              <code>DEV-{draftId ? draftId.slice(0, 8).toUpperCase() : 'COMMITTED'}</code>
            </div>
            <p className="post-commit-text">
              All data attributes, timestamps, and operator actions have been immutably sealed in the audit trail. You can now log the next deviation or upload a new file.
            </p>
            <div className="post-commit-actions">
              <button className="btn btn-primary" onClick={handleStartNextDeviation}>
                <PlusCircle size={16} /> + Log Next Deviation
              </button>
              <button className="btn btn-secondary" onClick={() => onOpenHistory?.(draftId)}>
                <History size={16} /> View in History
              </button>
            </div>

            <div className="post-commit-downloads" style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
              <a
                href={`/api/deviations/${draftId}/export/pdf`}
                download
                className="btn btn-outline-success btn-sm"
                style={{ flex: 1, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                title="Download official publication-grade PDF report"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Download size={14} /> Download PDF
              </a>
              <a
                href={`/api/deviations/${draftId}/export/docx`}
                download
                className="btn btn-ghost btn-sm"
                style={{ flex: 1, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px', border: '1px solid var(--color-border)' }}
                title="Download editable GxP Word dossier (.docx)"
              >
                <FileText size={14} /> Download Word
              </a>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Chat Input or Post-Commit Bar */}
      {isCommitted ? (
        <div className="post-commit-bottom-bar" style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleStartNextDeviation}>
            <PlusCircle size={16} /> + Start New Deviation
          </button>
          <button className="btn btn-secondary" onClick={() => onOpenHistory?.(draftId)} title="Inspect archived session">
            <History size={16} /> History
          </button>
        </div>
      ) : (
        <div className="chat-input-area">
          <div className="chat-input-wrapper">
            <input
              ref={inputRef}
              type="text"
              placeholder={isProcessing ? 'Analyzing...' : 'Paste report text or describe a correction...'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isProcessing}
            />
            <button
              className="btn btn-primary btn-sm"
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isProcessing}
              style={{ borderRadius: 'var(--radius-sm)' }}
            >
              {isProcessing ? <div className="spinner"></div> : <Send size={16} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

