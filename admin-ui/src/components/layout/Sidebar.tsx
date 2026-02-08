import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Wrench, Settings, Upload, Shield, FileText, Calendar, Sparkles, Eye, Users, Code, TestTube, Lock, CheckCircle2, LogSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavSection {
  title: string
  color: string
  items: NavItem[]
}

interface NavItem {
  icon: React.ComponentType<{ className?: string }>
  label: string
  path: string
  description?: string
}

// Main navigation items grouped by section
const navSections: NavSection[] = [
  {
    title: 'CORE',
    color: 'blue',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    ]
  },
  {
    title: 'TOOLS',
    color: 'blue',
    items: [
      { icon: Wrench, label: 'Tools', path: '/tools' },
      { icon: Upload, label: 'Import OpenAPI', path: '/import' },
    ]
  },
  {
    title: 'AUTHORIZATION & ACCESS CONTROL',
    color: 'blue',
    items: [
      { icon: Shield, label: 'Policies', path: '/policies', description: 'RBAC roles & permissions' },
      { icon: Users, label: 'Users', path: '/users', description: 'Assign roles to users' },
      { icon: Code, label: 'OPA Policies', path: '/opa-policies', description: 'Advanced policy rules' },
      { icon: TestTube, label: 'Test Authorization', path: '/test-authz', description: 'Validate before deploy' },
    ]
  },
  {
    title: 'TOOL EXPOSURE',
    color: 'green',
    items: [
      { icon: Eye, label: 'Exposure Governance', path: '/exposure', description: 'Control tool visibility' },
    ]
  },
  {
    title: 'COMPLIANCE & MONITORING',
    color: 'gray',
    items: [
      { icon: FileText, label: 'Audit Logs', path: '/audit-logs' },
      { icon: Settings, label: 'Settings', path: '/settings' },
    ]
  },
  {
    title: 'WORKFLOWS',
    color: 'purple',
    items: [
      { icon: Calendar, label: 'Service Booking', path: '/service-booking' },
    ]
  }
]

// Helper to get section color classes
const getSectionColors = (color: string) => {
  const colors: Record<string, { header: string; icon: string; hover: string }> = {
    blue: {
      header: 'text-blue-300',
      icon: 'text-blue-400 bg-blue-500/20 group-hover:bg-blue-500/30',
      hover: 'hover:bg-blue-500/10'
    },
    green: {
      header: 'text-green-300',
      icon: 'text-green-400 bg-green-500/20 group-hover:bg-green-500/30',
      hover: 'hover:bg-green-500/10'
    },
    gray: {
      header: 'text-gray-300',
      icon: 'text-gray-400 bg-gray-500/20 group-hover:bg-gray-500/30',
      hover: 'hover:bg-gray-500/10'
    },
    purple: {
      header: 'text-purple-300',
      icon: 'text-purple-400 bg-purple-500/20 group-hover:bg-purple-500/30',
      hover: 'hover:bg-purple-500/10'
    }
  }
  return colors[color] || colors.blue
}

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
      <nav className="flex-1 overflow-y-auto relative space-y-2 p-4">
        {navSections.map((section) => {
          const colors = getSectionColors(section.color)
          return (
            <div key={section.title} className="space-y-2">
              {/* Section Header */}
              <div className="flex items-center gap-2 px-4 py-2 mt-2">
                <div className={cn(
                  'h-0.5 flex-1 rounded-full',
                  section.color === 'blue' && 'bg-blue-500/40',
                  section.color === 'green' && 'bg-green-500/40',
                  section.color === 'gray' && 'bg-gray-500/40',
                  section.color === 'purple' && 'bg-purple-500/40'
                )} />
                <p className={cn('text-xs font-bold tracking-widest uppercase', colors.header)}>
                  {section.title}
                </p>
                <div className={cn(
                  'h-0.5 flex-1 rounded-full',
                  section.color === 'blue' && 'bg-blue-500/40',
                  section.color === 'green' && 'bg-green-500/40',
                  section.color === 'gray' && 'bg-gray-500/40',
                  section.color === 'purple' && 'bg-purple-500/40'
                )} />
              </div>

              {/* Section Items */}
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.path} className="relative">
                    <NavLink
                      to={item.path}
                      className={({ isActive }) => cn(
                        "flex items-start gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group",
                        isActive
                          ? "nav-item-active font-medium shadow-lg"
                          : cn("text-white/70 hover:text-white", colors.hover)
                      )}
                    >
                      {/* Icon Container - Color Coded */}
                      <div className={cn(
                        "p-2 rounded-lg transition-all duration-200 flex-shrink-0 mt-0.5",
                        colors.icon
                      )}>
                        <item.icon className="w-4 h-4" />
                      </div>

                      {/* Label & Description */}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{item.label}</div>
                        {item.description && (
                          <div className="text-xs text-white/50 group-hover:text-white/70 transition-colors">
                            {item.description}
                          </div>
                        )}
                      </div>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
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
