import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageCircle,
  Megaphone,
  BarChart2,
  Package,
  Users,
  Settings,
  LogOut,
  ChevronRight,
  Bot,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth.jsx'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'לוח בקרה', icon: LayoutDashboard },
  { path: '/conversations', label: 'שיחות', icon: MessageCircle },
  { path: '/campaigns', label: 'קמפיינים', icon: Megaphone },
  { path: '/analytics', label: 'אנליטיקס', icon: BarChart2 },
  { path: '/products', label: 'מוצרים', icon: Package },
  { path: '/users', label: 'משתמשים', icon: Users },
  { path: '/settings', label: 'הגדרות', icon: Settings },
]

export default function Sidebar({ open, onToggle }) {
  const location = useLocation()
  const { logout } = useAuth()

  return (
    <div
      className={`sidebar fixed top-0 right-0 h-full transition-all duration-300 z-50 flex flex-col
        ${open ? 'w-64' : 'w-16'}`}
    >
      {/* Logo */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        {open && (
          <div className="flex items-center gap-2">
            <Bot className="text-blue-400" size={28} />
            <span className="text-white font-bold text-lg">Idobetz AI</span>
          </div>
        )}
        {!open && <Bot className="text-blue-400 mx-auto" size={28} />}
        <button
          onClick={onToggle}
          className="text-slate-400 hover:text-white transition-colors"
        >
          <ChevronRight
            size={20}
            className={`transition-transform ${open ? 'rotate-0' : 'rotate-180'}`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors
                ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
            >
              <Icon size={20} className="shrink-0" />
              {open && <span className="text-sm font-medium">{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="p-2 border-t border-slate-700">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300
            hover:bg-red-600/20 hover:text-red-400 transition-colors w-full"
        >
          <LogOut size={20} className="shrink-0" />
          {open && <span className="text-sm font-medium">התנתק</span>}
        </button>
      </div>
    </div>
  )
}
