import { useState, useEffect } from 'react';
import {
  Cookie,
  FileCheck2,
  FileText,
  Mail,
  MapPin,
  Phone,
  Scale,
  Shield,
  ShieldCheck,
  X,
} from 'lucide-react';
import {
  useGetCookiePolicyQuery,
  useGetDpoContactQuery,
  useGetPrivacyPolicyQuery,
  useGetTermsAndConditionsQuery,
} from '../store/apiSlice';

export default function LegalModal({ isOpen, onClose, initialTab = 'privacy' }) {
  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  const { data: privacyData, isLoading: isPrivacyLoading } = useGetPrivacyPolicyQuery();
  const { data: termsData, isLoading: isTermsLoading } = useGetTermsAndConditionsQuery();
  const { data: cookieData, isLoading: isCookieLoading } = useGetCookiePolicyQuery();
  const { data: dpoData, isLoading: isDpoLoading } = useGetDpoContactQuery();

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-container legal-modal-container"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '820px', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}
      >
        {/* Modal Header */}
        <div className="modal-header" style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'rgba(56, 189, 248, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
              }}
            >
              <Scale size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                Statutory Compliance & Legal Governance
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                Compliant with Indian DPDP Act 2023, IT Act 2000, and FDA 21 CFR Part 11
              </p>
            </div>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            background: 'var(--bg-secondary)',
            borderBottom: '1px solid var(--border-color)',
            overflowX: 'auto',
          }}
        >
          <button
            type="button"
            className={`auth-tab-btn ${activeTab === 'privacy' ? 'active' : ''}`}
            onClick={() => setActiveTab('privacy')}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            <ShieldCheck size={15} />
            <span>DPDP Privacy Notice</span>
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${activeTab === 'terms' ? 'active' : ''}`}
            onClick={() => setActiveTab('terms')}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            <FileText size={15} />
            <span>Terms of Service (IT Act)</span>
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${activeTab === 'cookies' ? 'active' : ''}`}
            onClick={() => setActiveTab('cookies')}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            <Cookie size={15} />
            <span>Cookie Disclosure</span>
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${activeTab === 'dpo' ? 'active' : ''}`}
            onClick={() => setActiveTab('dpo')}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            <Mail size={15} />
            <span>DPO & Grievances</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            flex: 1,
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            lineHeight: 1.6,
          }}
        >
          {/* TAB 1: PRIVACY POLICY */}
          {activeTab === 'privacy' && (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1.25rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  background: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                }}
              >
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-primary)', margin: 0 }}>
                    {privacyData?.title || 'DPDP Privacy Notice'}
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Governing Law: {privacyData?.governing_law || 'Digital Personal Data Protection Act, 2023 (India)'}
                  </div>
                </div>
                <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.2)', color: 'var(--color-primary)' }}>
                  {privacyData?.version || 'v1.0-2026'}
                </span>
              </div>

              {isPrivacyLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>Loading statutory notice...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {privacyData?.sections?.map((sec, idx) => (
                    <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <h4 style={{ color: 'var(--text-primary)', fontSize: '0.92rem', margin: '0 0 0.5rem 0', fontWeight: 600 }}>
                        {sec.heading}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.85rem' }}>{sec.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: TERMS AND CONDITIONS */}
          {activeTab === 'terms' && (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1.25rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}
              >
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#10b981', margin: 0 }}>
                    {termsData?.title || 'Terms of Service'}
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Governing Law: {termsData?.governing_law || 'Information Technology Act, 2000 (India)'}
                  </div>
                </div>
                <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
                  {termsData?.version || 'v1.0-2026'}
                </span>
              </div>

              {isTermsLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>Loading terms...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {termsData?.sections?.map((sec, idx) => (
                    <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <h4 style={{ color: 'var(--text-primary)', fontSize: '0.92rem', margin: '0 0 0.5rem 0', fontWeight: 600 }}>
                        {sec.heading}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.85rem' }}>{sec.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: COOKIE POLICY */}
          {activeTab === 'cookies' && (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1.25rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  background: 'rgba(245, 158, 11, 0.08)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                }}
              >
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f59e0b', margin: 0 }}>
                    {cookieData?.title || 'Cookie & Local Storage Disclosure'}
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Mandatory Essential Storage Only • Zero Advertising Trackers
                  </div>
                </div>
                <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' }}>
                  {cookieData?.version || 'v1.0-2026'}
                </span>
              </div>

              {isCookieLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>Loading cookie policy...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {cookieData?.sections?.map((sec, idx) => (
                    <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <h4 style={{ color: 'var(--text-primary)', fontSize: '0.92rem', margin: '0 0 0.5rem 0', fontWeight: 600 }}>
                        {sec.heading}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.85rem' }}>{sec.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: DATA PROTECTION OFFICER & GRIEVANCE REDRESSAL */}
          {activeTab === 'dpo' && (
            <div>
              <div
                style={{
                  marginBottom: '1.25rem',
                  padding: '1rem',
                  borderRadius: '8px',
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <Shield size={20} style={{ color: '#818cf8' }} />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#818cf8', margin: 0 }}>
                    Section 13 Grievance Redressal & Data Protection Officer
                  </h3>
                </div>
                <p style={{ fontSize: '0.85rem', margin: 0, color: 'var(--text-secondary)' }}>
                  Under the Digital Personal Data Protection Act, 2023, Data Principals may submit inquiries,
                  consent withdrawal notices, or data handling grievances directly to our statutory officer in India.
                </p>
              </div>

              {isDpoLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>Loading officer details...</div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                  <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <h4 style={{ color: 'var(--text-primary)', fontSize: '1rem', margin: '0 0 0.75rem 0' }}>
                      {dpoData?.name || 'Dr. Rajesh Sharma'}
                    </h4>
                    <p style={{ color: 'var(--color-primary)', fontWeight: 500, margin: '0 0 1rem 0', fontSize: '0.85rem' }}>
                      {dpoData?.designation || 'Data Protection Officer & Quality Compliance Lead'}
                    </p>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Mail size={16} style={{ color: 'var(--text-muted)' }} />
                        <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                          {dpoData?.email || 'dpo-compliance@deviationiq.internal'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Phone size={16} style={{ color: 'var(--text-muted)' }} />
                        <span>{dpoData?.phone || '+91 (0124) 492-7000'}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                        <MapPin size={16} style={{ color: 'var(--text-muted)', marginTop: '2px' }} />
                        <span>
                          {dpoData?.address || 'Quality Governance Complex, Sector 18, Gurugram, Haryana 122015, India'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <h4 style={{ color: 'var(--text-primary)', fontSize: '0.92rem', margin: '0 0 0.5rem 0' }}>
                      Statutory Resolution Timeline & CERT-In Protocol
                    </h4>
                    <p style={{ fontSize: '0.85rem', margin: '0 0 0.75rem 0' }}>
                      All data protection grievances are acknowledged within 48 hours and resolved within{' '}
                      <strong>{dpoData?.statutory_response_days || 30} calendar days</strong> per DPDP Act guidelines.
                    </p>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                      {dpoData?.cert_in_coordination || 'Direct incident reporting channel synchronized with CERT-In directions.'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            background: 'var(--bg-secondary)',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileCheck2 size={14} style={{ color: 'var(--color-primary)' }} />
            <span>Authenticated Indian Law & GxP Compliance Framework</span>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            style={{ padding: '0.45rem 1.25rem', fontSize: '0.85rem' }}
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
}
