import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Users as UsersIcon, Search, Crown, Star } from 'lucide-react'

const TIER_ICONS = {
  standard: null,
  silver: '🥈',
  gold: '⭐',
  platinum: '💎',
  vip: '👑',
}

export default function Users() {
  const [platformFilter, setPlatformFilter] = useState('')
  const [tierFilter, setTierFilter] = useState('')

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users', platformFilter, tierFilter],
    queryFn: () =>
      axios.get('/api/v1/users', {
        params: {
          platform: platformFilter || undefined,
          tier: tierFilter || undefined,
        },
      }).then(r => r.data),
    refetchInterval: 30000,
  })

  return (
    <div className="p-8" dir="rtl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">משתמשים</h1>
        <p className="text-gray-500 mt-1">{users.length} משתמשים נטענו</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select
          value={platformFilter}
          onChange={e => setPlatformFilter(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">כל הפלטפורמות</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="messenger">Messenger</option>
          <option value="instagram">Instagram</option>
        </select>
        <select
          value={tierFilter}
          onChange={e => setTierFilter(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">כל הדרגות</option>
          <option value="standard">Standard</option>
          <option value="silver">Silver</option>
          <option value="gold">Gold</option>
          <option value="platinum">Platinum</option>
          <option value="vip">VIP</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">טוען...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-right px-4 py-3 font-medium text-gray-600">שם</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">פלטפורמה</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">דרגה</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">נקודות</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">הזמנות</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">סה״כ קניות</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">נצפה לאחרונה</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800">{user.name || 'לא ידוע'}</div>
                    {user.phone_number && (
                      <div className="text-xs text-gray-400 ltr">{user.phone_number}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 capitalize text-gray-600">{user.platform}</td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1">
                      {TIER_ICONS[user.tier] && <span>{TIER_ICONS[user.tier]}</span>}
                      <span className="capitalize text-gray-600">{user.tier}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 ltr text-gray-700">{user.loyalty_points?.toLocaleString()}</td>
                  <td className="px-4 py-3 ltr text-gray-700">{user.purchase_count}</td>
                  <td className="px-4 py-3 ltr text-gray-700">₪{user.total_purchases?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {user.last_seen_at ? new Date(user.last_seen_at).toLocaleString('he-IL') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <UsersIcon size={36} className="mx-auto mb-2 opacity-30" />
              אין משתמשים
            </div>
          )}
        </div>
      )}
    </div>
  )
}
