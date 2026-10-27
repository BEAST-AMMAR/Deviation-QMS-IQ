import { useState, useEffect } from 'react';
import {
  History,
  X,
  Search,
  FileText,
  MessageSquare,
  ScrollText,
  FileCheck,
  ShieldCheck,
  Building2,
  Calendar,
  Clock,
  Copy,
  Check,
  AlertTriangle,
  AlertCircle,
  Tag,
  ArrowRight,
  BrainCircuit,
  UserCircle2,
  Download,
  Filter,
} from 'lucide-react';
import { useListDeviationsQuery, useGetSessionDetailQuery } from '../store/apiSlice';

const SEVERITY_COLORS = {
  Critical: { bg: '#FFF1F2', text: '#BE123C', border: '#FECDD3' },
  Major: { bg: '#FFFBEB', text: '#B45309', border: '#FDE68A' },
  Minor: { bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
  default: { bg: '#F3F4F6', text: '#4B5563', border: '#E5E7EB' },
};

export default function PipelineHistoryModal({ isOpen, initialSelectedId, onClose }) {
  const { data: deviations = [], isLoading: isListLoading } = useListDeviationsQuery(undefined, {
    skip: !isOpen,
    pollingInterval: isOpen ? 6000 : 0,
  });

  const [selectedId, setSelectedId] = useState(initialSelectedId || null);
  const [activeTab, setActiveTab] = useState('outcomes'); // 'outcomes' | 'chat' | 'audit'
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [copied, setCopied] = useState(false);

  // Sync selectedId when modal opens or deviations list loads
  useEffect(() => {
    if (initialSelectedId) {
      setSelectedId(initialSelectedId);
    } else if (deviations.length > 0 && !selectedId) {
      setSelectedId(deviations[0].id);
    }
  }, [initialSelectedId, deviations]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const { data: sessionDetail, isLoading: isDetailLoading } = useGetSessionDetailQuery(selectedId, {
    skip: !isOpen || !selectedId,
  });

  if (!isOpen) return null;

  // Filter list
  const filteredDeviations = deviations.filter((dev) => {
    const matchesSearch =
      (dev.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (dev.id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (dev.site_plant || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (dev.filename || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity =
      severityFilter === 'ALL' || dev.initial_severity === severityFilter;

    return matchesSearch && matchesSeverity;
  });

  const activeDeviation = sessionDetail?.deviation || deviations.find((d) => d.id === selectedId);
  const messages = sessionDetail?.messages || [];
  const events = sessionDetail?.events || [];

  const formatDateTime = (ts) => {
    if (!ts) return 'N/A';
    try {
      return new Date(ts).toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return String(ts);
    }
  };

  const handleCopySummary = () => {
    if (!activeDeviation) return;
    const summaryText = `=====================================================
DEVIATIONIQ PIPELINE ARCHIVE & SESSION SUMMARY
Reference ID: DEV-${activeDeviation.id.slice(0, 8).toUpperCase()}
Committed At: ${formatDateTime(activeDeviation.committed_at)}
Reviewed By:  ${activeDeviation.reviewed_by || 'Quality Officer QO-01'}
Source File:  ${activeDeviation.filename || 'Direct Form Input'}
=====================================================

[EXECUTIVE SUMMARY]
${sessionDetail?.session_summary || activeDeviation.session_summary || 'No automated summary recorded.'}

[CORE REPORT OUTCOMES]
Title:                ${activeDeviation.title || 'N/A'}
Date of Occurrence:   ${activeDeviation.date_of_occurrence || 'N/A'}
Site / Facility:      ${activeDeviation.site_plant || 'N/A'}
Initial Severity:     ${activeDeviation.initial_severity || 'N/A'}
AI Suggested Severity:${activeDeviation.ai_suggested_severity || 'N/A'}
Classification:       ${activeDeviation.source || 'N/A'}
Related Product:      ${activeDeviation.related_product || 'N/A'}
Batch / Lot:          ${activeDeviation.batch_lot || 'N/A'}

[DETAILED DESCRIPTION]
${activeDeviation.detailed_description || 'N/A'}

[IMMEDIATE ACTION TAKEN]
${activeDeviation.initial_impact || 'N/A'}

[AI RISK REASONING & JUSTIFICATION]
${activeDeviation.ai_reasoning || 'N/A'}

[CHAT TRANSCRIPT STATS]
Recorded Messages: ${messages.length} messages in AI Copilot session
Audit Events:      ${events.length} CFR Part 11 events
=====================================================`;

    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <div className="history-modal-overlay" onClick={onClose}>
      <div className="history-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="history-modal-header">
          <div className="history-modal-title-group">
            <div className="history-header-icon-box">
              <History size={20} />
            </div>
            <div>
              <div className="history-modal-title">Pipeline Execution History & Archived Sessions</div>
              <div className="history-modal-subtitle">
                Complete AI Copilot chat transcripts, outcomes, risk assessments, and 21 CFR Part 11 audit records
              </div>
            </div>
          </div>
          <button className="history-close-btn" onClick={onClose} title="Close History (Esc)">
            <X size={18} />
          </button>
        </div>

        {/* Modal Content: Master-Detail Grid */}
        <div className="history-modal-body">
          {/* Left Master List */}
          <div className="history-sidebar">
            <div className="history-search-bar">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                placeholder="Search past sessions, IDs, files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-search-btn" onClick={() => setSearchQuery('')}>
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Severity Filter Pills */}
            <div className="history-filter-pills">
              {['ALL', 'Critical', 'Major', 'Minor'].map((sev) => (
                <button
                  key={sev}
                  className={`filter-pill ${severityFilter === sev ? 'active' : ''}`}
                  onClick={() => setSeverityFilter(sev)}
                >
                  {sev}
                </button>
              ))}
            </div>

            <div className="history-list-header">
              <span>Past Sessions ({filteredDeviations.length})</span>
              <span className="history-auto-refresh">Live Sync</span>
            </div>

            <div className="history-session-list">
              {isListLoading && deviations.length === 0 && (
                <div className="history-empty-state">
                  <div className="spinner"></div>
                  <span>Loading history...</span>
                </div>
              )}

              {!isListLoading && filteredDeviations.length === 0 && (
                <div className="history-empty-state">
                  <FileText size={32} opacity={0.35} />
                  <span>No completed pipeline sessions match your search.</span>
                </div>
              )}

              {filteredDeviations.map((dev) => {
                const isSelected = dev.id === selectedId;
                const sevStyle = SEVERITY_COLORS[dev.initial_severity] || SEVERITY_COLORS.default;
                return (
                  <div
                    key={dev.id}
                    className={`history-item-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedId(dev.id)}
                  >
                    <div className="history-item-top">
                      <span className="history-ref-tag">
                        DEV-{dev.id.slice(0, 8).toUpperCase()}
                      </span>
                      {dev.initial_severity && (
                        <span
                          className="history-severity-tag"
                          style={{
                            backgroundColor: sevStyle.bg,
                            color: sevStyle.text,
                            borderColor: sevStyle.border,
                          }}
                        >
                          {dev.initial_severity}
                        </span>
                      )}
                    </div>
                    <div className="history-item-title" title={dev.title}>
                      {dev.title || 'Untitled Deviation Record'}
                    </div>
                    <div className="history-item-meta">
                      <span className="history-item-site">
                        <Building2 size={11} /> {dev.site_plant || 'Site 01'}
                      </span>
                      <span className="history-item-date">
                        <Clock size={11} /> {formatDateTime(dev.committed_at || dev.created_at)}
                      </span>
                    </div>
                    {dev.filename && (
                      <div className="history-item-file">
                        <FileText size={11} />
                        <span>{dev.filename}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Detail Pane */}
          <div className="history-detail-pane">
            {!activeDeviation ? (
              <div className="history-detail-empty">
                <AlertCircle size={40} opacity={0.3} />
                <h3>No Session Selected</h3>
                <p>Select a completed pipeline session from the left to inspect its complete records.</p>
              </div>
            ) : (
              <div className="history-detail-content">
                {/* Header Banner */}
                <div className="history-detail-header-card">
                  <div className="history-detail-top-row">
                    <div className="history-detail-id-box">
                      <span className="history-detail-id">
                        DEV-{activeDeviation.id.slice(0, 8).toUpperCase()}
                      </span>
                      <span className="history-status-badge">
                        <ShieldCheck size={12} /> 21 CFR Part 11 Sealed
                      </span>
                    </div>
                    <div className="history-actions-group">
                      <a
                        href={`/api/deviations/${activeDeviation.id}/export/pdf`}
                        download
                        className="btn btn-primary btn-sm"
                        title="Download publication-grade GxP PDF Investigation Report"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                      >
                        <Download size={13} />
                        <span>PDF Report</span>
                      </a>
                      <a
                        href={`/api/deviations/${activeDeviation.id}/export/docx`}
                        download
                        className="btn btn-secondary btn-sm"
                        title="Download editable GxP Word Investigation Dossier (.docx)"
                        style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                      >
                        <FileText size={13} />
                        <span>Word (.docx)</span>
                      </a>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={handleCopySummary}
                        title="Copy complete text summary to clipboard"
                      >
                        {copied ? <Check size={13} color="#059669" /> : <Copy size={13} />}
                        {copied ? 'Copied' : 'Copy Text'}
                      </button>
                    </div>
                  </div>

                  <h2 className="history-detail-heading">{activeDeviation.title || 'Untitled Deviation'}</h2>

                  <div className="history-detail-chips">
                    <div className="detail-chip">
                      <Building2 size={13} />
                      <span>Facility:</span>
                      <strong>{activeDeviation.site_plant || 'API Manufacturing Unit 01'}</strong>
                    </div>
                    <div className="detail-chip">
                      <Calendar size={13} />
                      <span>Occurrence:</span>
                      <strong>{activeDeviation.date_of_occurrence || 'Not specified'}</strong>
                    </div>
                    <div className="detail-chip">
                      <Clock size={13} />
                      <span>Committed:</span>
                      <strong>{formatDateTime(activeDeviation.committed_at)}</strong>
                    </div>
                    <div className="detail-chip">
                      <ShieldCheck size={13} />
                      <span>Reviewer:</span>
                      <strong>{activeDeviation.reviewed_by || 'Quality Officer QO-01'}</strong>
                    </div>
                    {activeDeviation.filename && (
                      <div className="detail-chip highlight">
                        <FileText size={13} />
                        <span>Source Doc:</span>
                        <strong>{activeDeviation.filename}</strong>
                      </div>
                    )}
                  </div>

                  {/* Automated Executive Session Summary */}
                  {(sessionDetail?.session_summary || activeDeviation.session_summary) && (
                    <div className="history-session-summary-box">
                      <div className="summary-box-title">
                        <BrainCircuit size={14} /> Pipeline Executive Summary & Outcomes
                      </div>
                      <p className="summary-box-text">
                        {sessionDetail?.session_summary || activeDeviation.session_summary}
                      </p>
                    </div>
                  )}
                </div>

                {/* Tabs */}
                <div className="history-tabs-bar">
                  <button
                    className={`history-tab-btn ${activeTab === 'outcomes' ? 'active' : ''}`}
                    onClick={() => setActiveTab('outcomes')}
                  >
                    <FileCheck size={15} />
                    Report & Outcomes
                  </button>
                  <button
                    className={`history-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                    onClick={() => setActiveTab('chat')}
                  >
                    <MessageSquare size={15} />
                    AI Copilot Chat Transcript
                    <span className="tab-counter-badge">{messages.length}</span>
                  </button>
                  <button
                    className={`history-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
                    onClick={() => setActiveTab('audit')}
                  >
                    <ScrollText size={15} />
                    CFR Part 11 Audit Trail
                    <span className="tab-counter-badge">{events.length}</span>
                  </button>
                </div>

                {/* Tab 1: Report & Outcomes */}
                {activeTab === 'outcomes' && (
                  <div className="history-tab-pane">
                    {/* Severity & Triage Assessment Banner */}
                    <div className="history-risk-card">
                      <div className="risk-card-header">
                        <div className="risk-badge-box">
                          <span className="risk-label">Final Initial Severity:</span>
                          <span
                            className="risk-value-pill"
                            style={{
                              backgroundColor:
                                (SEVERITY_COLORS[activeDeviation.initial_severity] || SEVERITY_COLORS.default).bg,
                              color:
                                (SEVERITY_COLORS[activeDeviation.initial_severity] || SEVERITY_COLORS.default).text,
                            }}
                          >
                            {activeDeviation.initial_severity || 'Unspecified'}
                          </span>
                        </div>
                        {activeDeviation.ai_suggested_severity && (
                          <div className="risk-ai-suggested">
                            <span>AI Initial Recommendation:</span>
                            <strong>{activeDeviation.ai_suggested_severity}</strong>
                          </div>
                        )}
                      </div>
                      {activeDeviation.ai_reasoning && (
                        <div className="risk-reasoning-section">
                          <div className="risk-reasoning-title">AI Triage Justification & Risk Analysis</div>
                          <div className="risk-reasoning-content">{activeDeviation.ai_reasoning}</div>
                        </div>
                      )}
                    </div>

                    {/* 9 Core Fields Grid */}
                    <div className="history-fields-grid">
                      <div className="history-field-cell">
                        <div className="field-cell-label">1. Deviation Title</div>
                        <div className="field-cell-value">{activeDeviation.title || '—'}</div>
                      </div>

                      <div className="history-field-cell">
                        <div className="field-cell-label">2. Date of Occurrence</div>
                        <div className="field-cell-value">{activeDeviation.date_of_occurrence || '—'}</div>
                      </div>

                      <div className="history-field-cell">
                        <div className="field-cell-label">3. Facility / Site Plant</div>
                        <div className="field-cell-value">{activeDeviation.site_plant || '—'}</div>
                      </div>

                      <div className="history-field-cell">
                        <div className="field-cell-label">4. Deviation Classification / Source</div>
                        <div className="field-cell-value">{activeDeviation.source || '—'}</div>
                      </div>

                      <div className="history-field-cell">
                        <div className="field-cell-label">5. Related Product</div>
                        <div className="field-cell-value">{activeDeviation.related_product || '—'}</div>
                      </div>

                      <div className="history-field-cell">
                        <div className="field-cell-label">6. Batch / Lot Number</div>
                        <div className="field-cell-value">{activeDeviation.batch_lot || '—'}</div>
                      </div>

                      <div className="history-field-cell full-width">
                        <div className="field-cell-label">7. Detailed Description of Deviation</div>
                        <div className="field-cell-value text-block">
                          {activeDeviation.detailed_description || '—'}
                        </div>
                      </div>

                      <div className="history-field-cell full-width">
                        <div className="field-cell-label">8. Immediate Action Taken / Containment</div>
                        <div className="field-cell-value text-block">
                          {activeDeviation.initial_impact || '—'}
                        </div>
                      </div>

                      <div className="history-field-cell full-width">
                        <div className="field-cell-label">9. Initial Impact Assessment / AI Suggested Action</div>
                        <div className="field-cell-value text-block">
                          {activeDeviation.ai_suggested_action || 'No secondary containment action required.'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 2: AI Copilot Chat Transcript */}
                {activeTab === 'chat' && (
                  <div className="history-tab-pane">
                    {messages.length === 0 ? (
                      <div className="history-chat-empty">
                        <MessageSquare size={36} opacity={0.3} />
                        <h4>No Live Chat Transcript Logged</h4>
                        <p>This deviation was committed directly through the form without an interactive copilot dialogue.</p>
                      </div>
                    ) : (
                      <div className="history-chat-thread">
                        <div className="chat-thread-notice">
                          <ShieldCheck size={14} />
                          <span>Archived copilot session for reference DEV-{activeDeviation.id.slice(0, 8).toUpperCase()}. Fully preserved and unalterable.</span>
                        </div>
                        {messages.map((msg, idx) => {
                          const isUser = msg.role === 'user';
                          return (
                            <div key={idx} className={`history-chat-bubble-row ${isUser ? 'user-row' : 'assistant-row'}`}>
                              <div className="history-chat-avatar">
                                {isUser ? <UserCircle2 size={16} /> : <BrainCircuit size={16} />}
                              </div>
                              <div className={`history-chat-bubble ${isUser ? 'user' : 'assistant'}`}>
                                <div className="history-chat-bubble-header">
                                  <span className="bubble-author">{isUser ? 'Human Operator' : 'AI Copilot Assistant'}</span>
                                  {msg.timestamp && (
                                    <span className="bubble-timestamp">{formatDateTime(msg.timestamp)}</span>
                                  )}
                                </div>
                                <div className="history-chat-bubble-text">{msg.content}</div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: CFR Part 11 Audit Trail */}
                {activeTab === 'audit' && (
                  <div className="history-tab-pane">
                    {events.length === 0 ? (
                      <div className="history-chat-empty">
                        <ScrollText size={36} opacity={0.3} />
                        <h4>No Audit Events Recorded</h4>
                        <p>No incremental field modifications or extractions recorded for this deviation.</p>
                      </div>
                    ) : (
                      <div className="history-audit-timeline">
                        <div className="audit-timeline-intro">
                          <ShieldCheck size={14} />
                          <span>21 CFR Part 11 Append-Only Audit Trail: {events.length} cryptographic events logged.</span>
                        </div>
                        {events.map((evt) => (
                          <div key={evt.id} className="history-audit-row">
                            <div className="audit-row-indicator">
                              <span className={`actor-tag ${evt.actor}`}>
                                {evt.actor === 'ai' ? <BrainCircuit size={12} /> : <UserCircle2 size={12} />}
                                {evt.actor.toUpperCase()}
                              </span>
                            </div>
                            <div className="audit-row-body">
                              <div className="audit-row-meta">
                                <span className="audit-field-name">{evt.field}</span>
                                <span className="audit-time">{formatDateTime(evt.created_at)}</span>
                              </div>
                              <div className="audit-row-diff">
                                {evt.old_value && (
                                  <span className="audit-old-val">
                                    <span className="diff-label">Old:</span> {evt.old_value}
                                  </span>
                                )}
                                {evt.old_value && <ArrowRight size={12} className="diff-arrow" />}
                                <span className="audit-new-val">
                                  <span className="diff-label">New:</span> {evt.new_value || '(cleared)'}
                                </span>
                              </div>
                              {evt.source_snippet && (
                                <div className="audit-source-snippet">
                                  <span>Source text extracted:</span> "{evt.source_snippet}"
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
