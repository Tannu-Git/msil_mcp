import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Wrench, Settings, Car, Upload, Shield, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: Wrench, label: 'Tools', path: '/tools' },
  { icon: Upload, label: 'Import OpenAPI', path: '/import' },
  { icon: Shield, label: 'Policies', path: '/policies' },
  { icon: FileText, label: 'Audit Logs', path: '/audit-logs' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar() {
  return (
    <aside className="w-64 bg-msil-blue text-white flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-msil-blue-light">
        <div className="flex items-center gap-3">
          <div className="bg-white p-2 rounded-lg">
            <Car className="w-6 h-6 text-msil-blue" />
          </div>
          <div>
            <h1 className="font-bold text-lg">MARUTI SUZUKI</h1>
            <p className="text-xs text-msil-silver opacity-80">MCP Admin Console</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                )}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-msil-blue-light">
        <div className="flex items-center gap-3 px-4 py-2">
          <Settings className="w-5 h-5 text-white/70" />
          <span className="text-sm text-white/70">Settings</span>
        </div>
        <div className="mt-4 px-4 text-xs text-white/50">
          <p>Version 1.0.0</p>
          <p>API Mode: Mock</p>
        </div>
      </div>
    </aside>
  )
}
