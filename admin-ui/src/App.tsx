import { Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { Dashboard } from './pages/Dashboard'
import { Tools } from './pages/Tools'
import { Import } from './pages/Import'
import Login from './pages/Login'
import Policies from './pages/Policies'
import AuditLogs from './pages/AuditLogs'
import Settings from './pages/Settings'
import ServiceBookingWizard from './pages/ServiceBookingWizard'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 animate-pulse shadow-lg shadow-blue-500/30" />
            <div className="absolute inset-0 w-14 h-14 rounded-2xl border-2 border-blue-400 border-t-transparent animate-spin" />
          </div>
          <p className="text-sm text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="flex h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-blue-50">
              <Sidebar />
              <div className="flex-1 flex flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto p-6 lg:p-8">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/tools" element={<Tools />} />
                    <Route path="/import" element={<Import />} />
                    <Route path="/policies" element={<Policies />} />
                    <Route path="/audit-logs" element={<AuditLogs />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/service-booking" element={<ServiceBookingWizard />} />
                  </Routes>
                </main>
              </div>
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
