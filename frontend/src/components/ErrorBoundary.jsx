import { Component } from 'react';
import { AlertTriangle, RefreshCw, Trash2, ShieldAlert } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('[DeviationIQ ErrorBoundary Caught Exception]:', error, errorInfo);
  }

  handleReset = () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch (e) {
      console.warn('Storage clear failed:', e);
    }
    window.location.href = '/';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '100vh',
            width: '100vw',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--color-bg, #0B0F19)',
            color: 'var(--color-text, #F1F5F9)',
            fontFamily: 'var(--font-sans, system-ui, sans-serif)',
            padding: '24px',
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              maxWidth: '640px',
              width: '100%',
              background: 'var(--color-bg-card, #1E293B)',
              border: '1px solid var(--color-border, #334155)',
              borderRadius: '16px',
              padding: '32px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  color: '#ef4444',
                  padding: '10px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <ShieldAlert size={28} />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>
                  Client Runtime Exception
                </h2>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--color-text-muted, #94a3b8)' }}>
                  DeviationIQ encountered an unexpected interface error.
                </p>
              </div>
            </div>

            <div
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: '8px',
                padding: '14px',
                fontSize: '0.85rem',
                fontFamily: 'monospace',
                color: '#f87171',
                maxHeight: '180px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {this.state.error?.toString() || 'Unknown error occurred'}
            </div>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={this.handleReload}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '8px',
                  background: 'var(--color-primary, #0ea5e9)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={16} />
                <span>Reload Page</span>
              </button>

              <button
                type="button"
                onClick={this.handleReset}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '8px',
                  background: 'transparent',
                  color: 'var(--color-text-muted, #94a3b8)',
                  border: '1px solid var(--color-border, #334155)',
                  fontWeight: 500,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                }}
              >
                <Trash2 size={16} />
                <span>Reset Cache & Storage</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

