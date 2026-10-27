import { useState, useEffect } from 'react';
import { Cookie, ShieldCheck, X } from 'lucide-react';
import { useRecordConsentMutation } from '../store/apiSlice';

export default function CookieBanner({ onOpenPolicy }) {
  const [visible, setVisible] = useState(false);
  const [recordConsent] = useRecordConsentMutation();

  useEffect(() => {
    const hasConsented = localStorage.getItem('deviationiq_cookie_consent');
    if (!hasConsented) {
      // Small delay for smooth appearance
      const timer = setTimeout(() => setVisible(true), 1200);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = async () => {
    localStorage.setItem('deviationiq_cookie_consent', 'true');
    setVisible(false);
    try {
      await recordConsent({
        consent_type: 'essential_cookies',
        policy_version: 'v1.0-2026',
        granted: true,
      }).unwrap();
    } catch (e) {
      // Silent catch; local preference is already persisted
      console.debug('Cookie consent recorded locally:', e);
    }
  };

  if (!visible) return null;

  return (
    <div
      className="cookie-banner-wrap"
      style={{
        position: 'fixed',
        bottom: '1.25rem',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '92%',
        maxWidth: '780px',
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.94)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.55), 0 0 15px rgba(56, 189, 248, 0.15)',
        borderRadius: '12px',
        padding: '1rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        animation: 'fadeInUp 0.35s ease-out',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
        <div
          style={{
            background: 'rgba(56, 189, 248, 0.12)',
            color: 'var(--color-primary)',
            padding: '0.5rem',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Cookie size={20} />
        </div>
        <div style={{ fontSize: '0.82rem', lineHeight: 1.45, color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
            Essential Security Cookies & DPDP Compliance
          </span>
          <p style={{ margin: '2px 0 0 0' }}>
            DeviationIQ uses strictly essential JWT session tokens and local state for 21 CFR Part 11 audit trails
            and DPDP Act 2023 compliance. We never use advertising or commercial tracking cookies.{' '}
            <button
              type="button"
              onClick={() => onOpenPolicy && onOpenPolicy('cookies')}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                textDecoration: 'underline',
                cursor: 'pointer',
                padding: 0,
                fontSize: 'inherit',
                fontFamily: 'inherit',
              }}
            >
              Read Cookie Policy
            </button>
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
        <button
          type="button"
          onClick={handleAccept}
          className="btn btn-primary"
          style={{
            padding: '0.45rem 1rem',
            fontSize: '0.82rem',
            fontWeight: 600,
            whiteSpace: 'nowrap',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <ShieldCheck size={14} />
          <span>Accept Essential</span>
        </button>
        <button
          type="button"
          onClick={() => setVisible(false)}
          className="icon-btn"
          title="Dismiss"
          style={{ padding: '0.35rem' }}
        >
          <X size={15} />
        </button>
      </div>
    </div>
  );
}
