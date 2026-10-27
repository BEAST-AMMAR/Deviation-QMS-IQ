import { useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Scale,
  Shield,
  ShieldCheck,
  User,
  UserPlus,
} from 'lucide-react';
import { useLoginMutation, useRegisterMutation } from '../store/apiSlice';
import { setCredentials } from '../store/authSlice';
import LegalModal from './LegalModal';
import CookieBanner from './CookieBanner';

export default function LoginPage() {
  const dispatch = useDispatch();
  const [login, { isLoading: isLoginLoading }] = useLoginMutation();
  const [register, { isLoading: isRegisterLoading }] = useRegisterMutation();

  const [mode, setMode] = useState('login'); // 'login' | 'register'

  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Register Form State
  const [regFullName, setRegFullName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regRole, setRegRole] = useState('quality_assurance');
  const [regDepartment, setRegDepartment] = useState('API Manufacturing Unit 01');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [regTermsAccepted, setRegTermsAccepted] = useState(false);
  const [regPrivacyConsent, setRegPrivacyConsent] = useState(false);

  // Legal Modal & Cookie Banner State
  const [showLegalModal, setShowLegalModal] = useState(false);
  const [legalTab, setLegalTab] = useState('privacy');

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!loginUsername.trim() || !loginPassword.trim()) {
      setErrorMsg('Please enter both username and password.');
      return;
    }

    try {
      const response = await login({
        username: loginUsername.trim(),
        password: loginPassword.trim(),
      }).unwrap();

      dispatch(setCredentials(response));
    } catch (err) {
      const message =
        err?.data?.error?.message ||
        err?.data?.detail ||
        'Authentication failed. Verify credentials and network connection.';
      setErrorMsg(message);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!regFullName.trim() || !regUsername.trim() || !regEmail.trim() || !regPassword.trim()) {
      setErrorMsg('All fields marked with an asterisk are required.');
      return;
    }

    if (regPassword.length < 6) {
      setErrorMsg('Password must be at least 6 characters long.');
      return;
    }

    if (regPassword !== regConfirmPassword) {
      setErrorMsg('Passwords do not match. Please re-enter.');
      return;
    }

    if (!regTermsAccepted || !regPrivacyConsent) {
      setErrorMsg('Under Section 6 of the DPDP Act 2023 and the IT Act 2000, affirmative consent to both the Terms of Service and Privacy Policy is mandatory.');
      return;
    }

    try {
      const response = await register({
        username: regUsername.trim(),
        email: regEmail.trim(),
        full_name: regFullName.trim(),
        role: regRole,
        department: regDepartment.trim(),
        password: regPassword.trim(),
        terms_accepted: regTermsAccepted,
        privacy_consent: regPrivacyConsent,
        policy_version: 'v1.0-2026',
      }).unwrap();

      dispatch(setCredentials(response));
    } catch (err) {
      const message =
        err?.data?.error?.message ||
        err?.data?.detail ||
        'Registration failed. Username or email may already be registered.';
      setErrorMsg(message);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setErrorMsg('');
    setSuccessMsg('');
  };

  const isLoading = isLoginLoading || isRegisterLoading;

  return (
    <div className="login-screen">
      {/* Background ambient lighting */}
      <div className="login-backdrop-glow" />

      <div className="login-container">
        {/* Header Branding */}
        <div className="login-brand-header">
          <div className="login-logo-badge">
            <span className="login-logo-text">DQ</span>
          </div>
          <h1 className="login-app-title">DeviationIQ</h1>
          <p className="login-app-subtitle">
            Pharmaceutical Deviation Intake & Incident Intelligence
          </p>
          <div className="login-compliance-pill">
            <Shield size={13} style={{ color: 'var(--color-primary)' }} />
            <span>FDA 21 CFR Part 11 • GAMP 5 • Electronic Signatures</span>
          </div>
        </div>

        {/* Main Card */}
        <div className="login-card">
          {/* Mode Switcher Tabs */}
          <div className="auth-tab-bar" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'login'}
              className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
              onClick={() => switchMode('login')}
            >
              <User size={15} />
              <span>Sign In</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'register'}
              className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
              onClick={() => switchMode('register')}
            >
              <UserPlus size={15} />
              <span>Create Account</span>
            </button>
          </div>

          <div className="login-card-header">
            <h2>{mode === 'login' ? 'Authorized Personnel Sign In' : 'Register Clinical Personnel'}</h2>
            <p>
              {mode === 'login'
                ? 'Enter your institutional credentials to access deviation intake logs.'
                : 'Create a new clinical user profile with verified role attribution.'}
            </p>
          </div>

          {errorMsg && (
            <div className="login-error-banner" role="alert">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="login-success-banner" role="status">
              <CheckCircle2 size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* SIGN IN FORM */}
          {mode === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="login-form">
              <div className="login-field-group">
                <label htmlFor="login-username">Clinical Username</label>
                <div className="login-input-wrapper">
                  <User size={16} className="login-field-icon" />
                  <input
                    id="login-username"
                    type="text"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    placeholder="e.g. sjenkins"
                    autoComplete="username"
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="login-field-group">
                <label htmlFor="login-password">Security Password</label>
                <div className="login-input-wrapper">
                  <Lock size={16} className="login-field-icon" />
                  <input
                    id="login-password"
                    type={showLoginPassword ? 'text' : 'password'}
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="Enter security password"
                    autoComplete="current-password"
                    disabled={isLoading}
                    required
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    tabIndex={-1}
                    aria-label="Toggle password visibility"
                  >
                    {showLoginPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="login-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="login-loading-spinner">Verifying credentials...</span>
                ) : (
                  <span>Sign In & Access Workspace</span>
                )}
              </button>

              <div className="auth-footer-toggle">
                <span>New to DeviationIQ? </span>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={() => switchMode('register')}
                >
                  Create an account
                </button>
              </div>
            </form>
          ) : (
            /* REGISTER / SIGN UP FORM */
            <form onSubmit={handleRegisterSubmit} className="login-form">
              <div className="login-form-grid">
                <div className="login-field-group">
                  <label htmlFor="reg-fullname">Full Name *</label>
                  <div className="login-input-wrapper">
                    <User size={16} className="login-field-icon" />
                    <input
                      id="reg-fullname"
                      type="text"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      placeholder="e.g. Dr. Sarah Jenkins"
                      disabled={isLoading}
                      required
                    />
                  </div>
                </div>

                <div className="login-field-group">
                  <label htmlFor="reg-username">Username *</label>
                  <div className="login-input-wrapper">
                    <User size={16} className="login-field-icon" />
                    <input
                      id="reg-username"
                      type="text"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="e.g. sjenkins"
                      autoComplete="username"
                      disabled={isLoading}
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="login-field-group">
                <label htmlFor="reg-email">Institutional Work Email *</label>
                <div className="login-input-wrapper">
                  <Mail size={16} className="login-field-icon" />
                  <input
                    id="reg-email"
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="e.g. sarah.jenkins@pharma.com"
                    autoComplete="email"
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div className="login-field-group">
                <label>Clinical Role Attribution *</label>
                <div className="auth-role-selector">
                  <button
                    type="button"
                    className={`auth-role-option ${regRole === 'quality_assurance' ? 'active' : ''}`}
                    onClick={() => setRegRole('quality_assurance')}
                  >
                    <ShieldCheck size={14} />
                    <span>QA Lead</span>
                  </button>
                  <button
                    type="button"
                    className={`auth-role-option ${regRole === 'technician' ? 'active' : ''}`}
                    onClick={() => setRegRole('technician')}
                  >
                    <Building2 size={14} />
                    <span>Process Tech</span>
                  </button>
                  <button
                    type="button"
                    className={`auth-role-option ${regRole === 'viewer' ? 'active' : ''}`}
                    onClick={() => setRegRole('viewer')}
                  >
                    <Shield size={14} />
                    <span>Viewer</span>
                  </button>
                </div>
              </div>

              <div className="login-field-group">
                <label htmlFor="reg-department">Facility / Department</label>
                <div className="login-input-wrapper">
                  <Building2 size={16} className="login-field-icon" />
                  <input
                    id="reg-department"
                    type="text"
                    value={regDepartment}
                    onChange={(e) => setRegDepartment(e.target.value)}
                    placeholder="e.g. API Manufacturing Unit 01"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="login-form-grid">
                <div className="login-field-group">
                  <label htmlFor="reg-password">Password (min. 6 chars) *</label>
                  <div className="login-input-wrapper">
                    <Lock size={16} className="login-field-icon" />
                    <input
                      id="reg-password"
                      type={showRegPassword ? 'text' : 'password'}
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Create password"
                      autoComplete="new-password"
                      disabled={isLoading}
                      required
                    />
                    <button
                      type="button"
                      className="login-password-toggle"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      tabIndex={-1}
                      aria-label="Toggle password visibility"
                    >
                      {showRegPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <div className="login-field-group">
                  <label htmlFor="reg-confirm-password">Confirm Password *</label>
                  <div className="login-input-wrapper">
                    <Lock size={16} className="login-field-icon" />
                    <input
                      id="reg-confirm-password"
                      type={showRegPassword ? 'text' : 'password'}
                      value={regConfirmPassword}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      placeholder="Repeat password"
                      autoComplete="new-password"
                      disabled={isLoading}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Statutory Compliance & Affirmative Consent (DPDP Act 2023 §6 & IT Act 2000) */}
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  fontSize: '0.82rem',
                  color: 'var(--text-secondary)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
                  <input
                    id="consent-terms"
                    type="checkbox"
                    checked={regTermsAccepted}
                    onChange={(e) => setRegTermsAccepted(e.target.checked)}
                    style={{ marginTop: '3px', cursor: 'pointer', accentColor: 'var(--color-primary)' }}
                    required
                  />
                  <label htmlFor="consent-terms" style={{ cursor: 'pointer', lineHeight: 1.45 }}>
                    I agree to the{' '}
                    <button
                      type="button"
                      onClick={() => {
                        setLegalTab('terms');
                        setShowLegalModal(true);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--color-primary)',
                        textDecoration: 'underline',
                        padding: 0,
                        cursor: 'pointer',
                        fontWeight: 600,
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                      }}
                    >
                      Terms & Conditions
                    </button>{' '}
                    governed by the laws of India and Information Technology Act, 2000.
                  </label>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
                  <input
                    id="consent-privacy"
                    type="checkbox"
                    checked={regPrivacyConsent}
                    onChange={(e) => setRegPrivacyConsent(e.target.checked)}
                    style={{ marginTop: '3px', cursor: 'pointer', accentColor: 'var(--color-primary)' }}
                    required
                  />
                  <label htmlFor="consent-privacy" style={{ cursor: 'pointer', lineHeight: 1.45 }}>
                    I affirmatively consent under Section 6 of the{' '}
                    <strong>Digital Personal Data Protection Act, 2023 (DPDP Act)</strong> to the collection and
                    processing of my clinical profile per the{' '}
                    <button
                      type="button"
                      onClick={() => {
                        setLegalTab('privacy');
                        setShowLegalModal(true);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--color-primary)',
                        textDecoration: 'underline',
                        padding: 0,
                        cursor: 'pointer',
                        fontWeight: 600,
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                      }}
                    >
                      Privacy Policy & Notice
                    </button>
                    .
                  </label>
                </div>
              </div>

              <button
                type="submit"
                className="login-submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="login-loading-spinner">Creating account...</span>
                ) : (
                  <span>Register & Access Workspace</span>
                )}
              </button>

              <div className="auth-footer-toggle">
                <span>Already have a verified account? </span>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={() => switchMode('login')}
                >
                  Sign in
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Security / Compliance Notice Footer */}
        <div className="login-footer-notice">
          <p>
            Enforces FDA 21 CFR Part 11 electronic signature integrity, Indian DPDP Act 2023 data fiduciary safeguards,
            and CERT-In 180-day audit retention.
          </p>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              marginTop: '0.65rem',
              fontSize: '0.78rem',
            }}
          >
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
              }}
            >
              DPDP Privacy Notice
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
              }}
            >
              Cookie Disclosure
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
              }}
            >
              DPO Grievance Redressal
            </button>
          </div>
        </div>
      </div>

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
