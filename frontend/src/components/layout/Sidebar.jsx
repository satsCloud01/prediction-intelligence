import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, FolderKanban, Network, Users, Play,
  FileText, MessageCircle, Settings, Brain,
} from 'lucide-react'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/graph', icon: Network, label: 'Graph Builder' },
  { to: '/agents', icon: Users, label: 'Agent Gallery' },
  { to: '/simulation', icon: Play, label: 'Simulation' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/interaction', icon: MessageCircle, label: 'Interaction' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-white flex flex-col z-40"
      style={{ borderRight: '1px solid rgba(30,45,82,0.1)' }}>
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-5" style={{ borderBottom: '1px solid rgba(30,45,82,0.1)' }}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center animate-glow"
          style={{ background: 'var(--navy)' }}>
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold text-navy-700 font-display">Prediction</div>
          <div className="text-[10px] uppercase tracking-[3px] text-gold-500 font-semibold">Intelligence</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200',
                isActive
                  ? 'font-semibold text-navy-700'
                  : 'text-navy-400 hover:text-navy-700'
              )
            }
            style={({ isActive }) => isActive ? {
              background: 'rgba(30,58,110,0.06)',
              boxShadow: 'inset 3px 0 0 var(--navy)',
            } : {}}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 text-center" style={{ borderTop: '1px solid rgba(30,45,82,0.1)' }}>
        <div className="text-[10px] text-navy-300 uppercase tracking-[2px]">Swarm Intelligence</div>
      </div>
    </aside>
  )
}
