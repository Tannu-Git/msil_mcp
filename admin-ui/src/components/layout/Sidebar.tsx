import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Wrench, Settings, Upload, Shield, FileText, Calendar, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: Wrench, label: 'Tools', path: '/tools' },
  { icon: Upload, label: 'Import OpenAPI', path: '/import' },
  { icon: Shield, label: 'Policies', path: '/policies' },
  { icon: FileText, label: 'Audit Logs', path: '/audit-logs' },
  { icon: Calendar, label: 'Service Booking', path: '/service-booking' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar() {
  return (
    <aside className="w-72 sidebar-gradient text-white flex flex-col shadow-2xl relative overflow-hidden">
      {/* Decorative Elements */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-20 left-0 w-32 h-32 bg-white/5 rounded-full -translate-x-1/2" />
      
      {/* Logo Section */}
      <div className="p-6 border-b border-white/10 relative">
        <div className="flex flex-col items-center gap-3">
          <div className="bg-white px-4 py-3 rounded-xl shadow-lg">
            <img 
              src="/Maruti-suzuki_logo_v1.svg" 
              alt="Maruti Suzuki" 
              className="h-10 w-auto object-contain"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-blue-300" />
            <p className="text-xs text-blue-200 font-medium">MCP Admin Console</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 relative">
        <p className="px-4 py-2 text-xs font-semibold text-blue-300 uppercase tracking-wider">Main Menu</p>
        <ul className="space-y-1.5 mt-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                  isActive
                    ? "nav-item-active font-medium"
                    : "text-white/70 hover:bg-white/10 hover:text-white hover:translate-x-1"
                )}
              >
                <div className={cn(
                  "p-2 rounded-lg transition-all duration-200",
                  "bg-white/10 group-hover:bg-white/20"
                )}>
                  <item.icon className="w-4 h-4" />
                </div>
                <span className="text-sm">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/10 relative">
        <div className="glass rounded-xl p-4 bg-white/5">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-emerald-400 rounded-full pulse-notification" />
            <span className="text-xs text-white/80">System Online</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-white/50">
            <span>v1.0.0</span>
            <span className="px-2 py-0.5 bg-blue-500/30 rounded text-blue-200 font-medium">Production</span>
          </div>
        </div>
        <p className="mt-3 text-center text-[10px] text-white/40">
          Powered by Nagarro
        </p>
      </div>
    </aside>
  )
}
