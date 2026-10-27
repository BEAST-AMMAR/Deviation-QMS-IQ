import { useDispatch, useSelector } from 'react-redux';
import { Building2, ChevronRight, History, LogOut, ShieldCheck, User } from 'lucide-react';
import { apiSlice, useListDeviationsQuery } from '../store/apiSlice';
import { logout } from '../store/authSlice';
import { resetDraft } from '../store/draftSlice';
import { clearMessages } from '../store/chatSlice';

export default function Navbar({ onOpenHistory }) {
  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);

  const { data: deviations = [] } = useListDeviationsQuery(undefined, {
    pollingInterval: 10000,
  });

  const getInitials = (name) => {
    if (!name) return 'QO';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  };

  const formatRole = (role) => {
    if (!role) return 'Technician';
    if (role === 'quality_assurance') return 'QA Lead';
    if (role === 'admin') return 'Admin';
    return 'Technician';
  };

  const handleSignOut = () => {
    dispatch(logout());
    dispatch(resetDraft());
    dispatch(clearMessages());
    dispatch(apiSlice.util.resetApiState());
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="navbar-logo">DQ</div>
        <div>
          <div className="navbar-title">DeviationIQ</div>
        </div>
      </div>

      <div className="navbar-breadcrumb">
        <span>Quality Management</span>
        <ChevronRight size={14} style={{ opacity: 0.35 }} />
        <span>Deviations</span>
        <ChevronRight size={14} style={{ opacity: 0.35 }} />
        <span className="active">Log Deviation</span>
      </div>

      <div className="navbar-right">
        <button
          className="navbar-history-btn"
          onClick={onOpenHistory}
          title="View Pipeline History & Archived Sessions"
        >
          <History size={15} />
          <span>Pipeline History</span>
          {deviations.length > 0 && (
            <span className="navbar-history-count">{deviations.length}</span>
          )}
        </button>

        <div className="navbar-facility" title={user?.department || 'API Manufacturing Unit 01'}>
          <Building2 size={14} />
          <span>{user?.department ? user.department.split('&')[0].trim() : 'API Unit 01'}</span>
        </div>

        {/* Authenticated User Capsule */}
        <div className="navbar-user-capsule" title={`Signed in as ${user?.full_name || 'Clinical User'}`}>
          <div className="navbar-user-avatar">
            {getInitials(user?.full_name)}
          </div>
          <div className="navbar-user-info">
            <span className="navbar-user-name">{user?.full_name || 'Dr. Elena Vance'}</span>
            <span className="navbar-user-role">{formatRole(user?.role)}</span>
          </div>
          <button
            className="navbar-logout-btn"
            onClick={handleSignOut}
            title="Sign out of clinical session"
            aria-label="Sign Out"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </nav>
  );
}
