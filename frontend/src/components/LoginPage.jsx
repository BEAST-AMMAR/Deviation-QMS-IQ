import { useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  Lock,
  Shield,
  ShieldCheck,
  User,
} from 'lucide-react';
import { useLoginMutation } from '../store/apiSlice';
import { setCredentials } from '../store/authSlice';

export default function LoginPage() {
  const dispatch = useDispatch();
  const [login, { isLoading }] = useLoginMutation();

  const [username, setUsername] = useState('qa_officer');
  const [password, setPassword] = useState('PharmaQuality2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const demoAccounts = [
    {
      role: 'QA Lead',
      name: 'Dr. Elena Vance',
      user: 'qa_officer',
      pass: 'PharmaQuality2026!',
      dept: 'Quality Assurance & Regulatory',
      badgeClass: 'badge-high',
      icon: ShieldCheck,
    },
    {
      role: 'Process Tech',
      name: 'Marcus Brody',
      user: 'tech_lead',
      pass: 'PharmaTech2026!',
      dept: 'API Manufacturing Unit 01',
      badgeClass: 'badge-medium',
      icon: Building2,
    },
    {
      role: 'Quality Admin',
      name: 'Dr. Arthur Pendelton',
      user: 'admin',
      pass: 'PharmaAdmin2026!',
      dept: 'Executive Quality Operations',
      badgeClass: 'badge-low',
      icon: KeyRound,
    },
  ];

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setErrorMsg('');

    if (!username.trim() || !password.trim()) {
      setErrorMsg('Please enter both clinical username and password.');
      return;
    }

    try {
      const response = await login({
        username: username.trim(),
        password: password.trim(),
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

  const handleSelectDemo = (acc) => {
    setUsername(acc.user);
    setPassword(acc.pass);
    setErrorMsg('');
  };

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
          <div className="login-card-header">
            <h2>Authorized Personnel Sign In</h2>
            <p>Enter your institutional credentials to access deviation intake logs.</p>
          </div>

          {errorMsg && (
            <div className="login-error-banner" role="alert">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="login-field-group">
              <label htmlFor="username">Clinical Username</label>
              <div className="login-input-wrapper">
                <User size={16} className="login-field-icon" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. qa_officer"
                  autoComplete="username"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>

            <div className="login-field-group">
              <label htmlFor="password">Security Password</label>
              <div className="login-input-wrapper">
                <Lock size={16} className="login-field-icon" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  autoComplete="current-password"
                  disabled={isLoading}
                  required
                />
                <button
                  type="button"
                  className="login-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
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
                <span>Authenticate & Access Module</span>
              )}
            </button>
          </form>

          {/* Preset Clinical Personas for frictionless evaluation */}
          <div className="login-demo-section">
            <div className="login-demo-divider">
              <span>Quick Login (Demo Personas)</span>
            </div>
            <div className="login-demo-grid">
              {demoAccounts.map((acc) => {
                const isSelected = username === acc.user;
                const IconComponent = acc.icon;
                return (
                  <button
                    key={acc.user}
                    type="button"
                    className={`login-demo-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectDemo(acc)}
                    title={`Click to fill credentials for ${acc.name}`}
                  >
                    <div className="login-demo-card-top">
                      <IconComponent size={14} className="login-demo-icon" />
                      <span className={`login-role-badge ${acc.badgeClass}`}>
                        {acc.role}
                      </span>
                    </div>
                    <div className="login-demo-name">{acc.name}</div>
                    <div className="login-demo-dept">{acc.dept}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Security / Compliance Notice Footer */}
        <div className="login-footer-notice">
          <p>
            This system is for authorized pharmaceutical quality operations. Every authentication
            event, session, and deviation sign-off is recorded in the permanent audit trail.
          </p>
        </div>
      </div>
    </div>
  );
}
