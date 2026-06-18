import React from 'react'
import { X } from 'lucide-react'

export default function UserProfileModal({ user, onClose }) {
  if (!user) return null

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700 shadow-xl">
        <div className="p-4 border-b border-gray-100 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">פרופיל משתמש</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-300"><X size={18} /></button>
        </div>
        <div className="p-4 space-y-3 text-sm">
          <div><span className="text-gray-500">שם:</span> <span className="font-medium dark:text-gray-200">{user.name || '-'}</span></div>
          <div><span className="text-gray-500">אימייל:</span> <span className="font-medium dark:text-gray-200">{user.email || '-'}</span></div>
          <div><span className="text-gray-500">פילוח:</span> <span className="font-medium dark:text-gray-200">{user.segment || '-'}</span></div>
          <div><span className="text-gray-500">ערך לקוח:</span> <span className="font-medium dark:text-gray-200">₪{(user.lifetime_value || 0).toFixed(2)}</span></div>
          <div><span className="text-gray-500">Engagement:</span> <span className="font-medium dark:text-gray-200">{user.engagement_score || 0}/100</span></div>
          <div><span className="text-gray-500">תגיות:</span> <span className="font-medium dark:text-gray-200">{(user.tags || []).join(', ') || '-'}</span></div>
        </div>
      </div>
    </div>
  )
}
