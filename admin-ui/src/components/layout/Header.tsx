import { Bell, User, LogOut, ChevronDown, Search, Command } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useState } from 'react'

export function Header() {
  const { user, logout } = useAuth()
  const [showDropdown, setShowDropdown] = useState(false)

  const handleLogout = () => {
    logout()
    setShowDropdown(false)
  }

  return (
    <header className="header-glass px-6 py-4 sticky top-0 z-30">
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div>
          <h2 className="text-xl font-bold text-gray-800">MCP Server Administration</h2>
          <p className="text-sm text-gray-500 mt-0.5">Manage tools, monitor executions, and view analytics</p>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="hidden md:flex items-center gap-2 px-4 py-2.5 bg-gray-100/80 hover:bg-gray-100 rounded-xl transition-colors cursor-pointer group">
            <Search className="w-4 h-4 text-gray-400 group-hover:text-gray-500" />
            <span className="text-sm text-gray-400 group-hover:text-gray-500">Search...</span>
            <div className="flex items-center gap-1 ml-4 px-2 py-0.5 bg-white rounded-md border border-gray-200 shadow-sm">
              <Command className="w-3 h-3 text-gray-400" />
              <span className="text-xs text-gray-400">K</span>
            </div>
          </div>

          {/* Notifications */}
          <button className="relative p-2.5 text-gray-500 hover:text-gray-700 bg-gray-100/80 hover:bg-gray-100 rounded-xl transition-all hover:shadow-sm group">
            <Bell className="w-5 h-5" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full pulse-notification"></span>
          </button>

          {/* Divider */}
          <div className="h-8 w-px bg-gray-200 mx-2" />

          {/* User Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-3 hover:bg-gray-50 rounded-xl p-2 transition-all group"
            >
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
              </div>
              <div className="text-sm text-left hidden sm:block">
                <p className="font-semibold text-gray-800">{user?.name || 'User'}</p>
                <p className="text-gray-500 text-xs">{user?.roles?.[0] || 'Administrator'}</p>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
            </button>

            {showDropdown && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowDropdown(false)}
                />
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-20 animate-scaleIn">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="font-semibold text-gray-800">{user?.name}</p>
                    <p className="text-sm text-gray-500 truncate">{user?.email}</p>
                  </div>
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-2">Roles</p>
                    <div className="flex flex-wrap gap-1.5">
                      {user?.roles.map((role) => (
                        <span
                          key={role}
                          className="badge-info"
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="pt-2">
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span className="font-medium">Sign Out</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
