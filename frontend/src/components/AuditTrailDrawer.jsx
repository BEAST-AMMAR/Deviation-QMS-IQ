import { useEffect, useState } from 'react';
import {
  ScrollText,
  X,
  BrainCircuit,
  UserCircle2,
  ClipboardList,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { useGetDeviationEventsQuery } from '../store/apiSlice';

/**
 * AuditTrailDrawer — Slide-out drawer displaying the append-only
 * audit trail (deviation_events) with attribution and diffs.
 * Implements US-06 and ALCOA+ visibility.
 */
export default function AuditTrailDrawer({ deviationId, onClose }) {
  const { data: events, isLoading, error } = useGetDeviationEventsQuery(deviationId, {
    skip: !deviationId,
    pollingInterval: 5000,
  });

  const formatTime = (ts) => {
    if (!ts) return '';
    return new Date(ts).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatFieldName = (name) => {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <>
      <div className="audit-overlay" onClick={onClose} />
      <div className="audit-drawer">
        <div className="audit-drawer-header">
          <h3>
            <ScrollText size={18} />
            Audit Trail
          </h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            <X size={14} />
            Close
          </button>
        </div>

        <div className="audit-drawer-body">
          {isLoading && (
            <div className="empty-state">
              <div className="spinner" style={{ width: '24px', height: '24px' }}></div>
              <div className="empty-state-text" style={{ marginTop: '14px' }}>Loading audit trail...</div>
            </div>
          )}

          {error && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <AlertTriangle size={40} />
              </div>
              <div className="empty-state-text">Failed to load audit events.</div>
            </div>
          )}

          {!isLoading && (!events || events.length === 0) && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <ClipboardList size={40} />
              </div>
              <div className="empty-state-text">
                No audit events yet. Events will appear here as fields are extracted and modified.
              </div>
            </div>
          )}

          {events && events.map((event) => (
            <div key={event.id} className={`audit-event ${event.actor}`}>
              <div className="audit-event-header">
                <span className={`audit-event-actor ${event.actor}`}>
                  {event.actor === 'ai' ? (
                    <><BrainCircuit size={14} /> AI</>
                  ) : (
                    <><UserCircle2 size={14} /> Human</>
                  )}
                </span>
                <span className="audit-event-time">{formatTime(event.created_at)}</span>
              </div>
              <div className="audit-event-field">{formatFieldName(event.field)}</div>
              <div className="audit-event-diff">
                {event.old_value && (
                  <>
                    <span className="audit-event-old">{event.old_value}</span>
                    <span className="audit-event-arrow"><ArrowRight size={12} /></span>
                  </>
                )}
                <span className="audit-event-new">{event.new_value || '(empty)'}</span>
              </div>
              {event.confidence && (
                <div style={{ marginTop: '6px' }}>
                  <span className={`field-confidence-tag ${event.confidence}`}>
                    {event.confidence}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
