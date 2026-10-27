import { Building2, ChevronRight, History } from 'lucide-react';
import { useListDeviationsQuery } from '../store/apiSlice';

export default function Navbar({ onOpenHistory }) {
  const { data: deviations = [] } = useListDeviationsQuery(undefined, {
    pollingInterval: 10000,
  });

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

        <div className="navbar-facility">
          <Building2 size={14} />
          API Manufacturing Unit 01
        </div>
        <div className="navbar-user" title="Quality Officer QO-01">QO</div>
      </div>
    </nav>
  );
}
