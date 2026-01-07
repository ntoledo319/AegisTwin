import { Outlet, NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Play, 
  Shield, 
  FileText, 
  Settings,
  Activity
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/runs', icon: Play, label: 'Runs' },
  { to: '/policies', icon: Shield, label: 'Policies' },
  { to: '/audit', icon: FileText, label: 'Audit Log' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Activity className="h-8 w-8 text-aegis-500" />
            <span className="text-xl font-bold">AegisTwin</span>
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-aegis-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                )
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        
        <div className="p-4 border-t border-gray-700 text-sm text-gray-400">
          v0.2.0
        </div>
      </aside>
      
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
