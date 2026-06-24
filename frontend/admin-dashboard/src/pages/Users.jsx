import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Users as UsersIcon, Search, Crown, ChevronDown, ChevronUp, X } from 'lucide-react'

const TIER_ICONS = {
  standard: '👤',
  silver: '🥈',
  gold: '⭐',
  platinum: '💎',
  vip: '👑',
}

const TIER_COLORS = {
  standard: 'bg-gray-100 text-gray-600',
  silver: 'bg-slate-100 text-slate-600',
  gold: 'bg-yellow-100 text-yellow-700',
  platinum: 'bg-purple-100 text-purple-700',
  vip: 'bg-pink-100 text-pink-700',
}

function UserProfileModal({ user, onClose, onUpdated }) {
  const queryClient = useQueryClient()
  const [vip, setVip] = useState(user.tier === 'vip')

  const updateMutation = useMutation({
    mutationFn: (data) => axios.put(`/api/v1/admin/users/${user.id}`, data),
    onSuccess: () => {
      toast.success('משתמש עודכן')
      queryClient.invalidateQueries(['admin-users'])
      onUpdated?.()
      onClose()
    },
    onError: () => toast.error('שגיאה בעדכון'),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" dir="rtl">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-xl">
              {TIER_ICONS[user.tier] || '👤'}
            </div>
            <div>
              <div className="font-bold text-gray-900 text-lg">{user.name || 'לא ידוע'}</div>
              <div className="text-sm text-gray-500 capitalize">{user.platform}</div>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-5">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{user.purchase_count || 0}</div>
            <div className="text-xs text-gray-500 mt-1">הזמנות</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-600">₪{(user.total_purchases || 0).toFixed(0)}</div>
            <div className="text-xs text-gray-500 mt-1">ערך לכל החיים</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-600">{user.loyalty_points?.toLocaleString() || 0}</div>
            <div className="text-xs text-gray-500 mt-1">נקודות נאמנות</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className={`text-lg font-semibold ${TIER_COLORS[user.tier]?.split(' ')[1] || 'text-gray-600'} capitalize`}>
              {TIER_ICONS[user.tier]} {user.tier}
            </div>
            <div className="text-xs text-gray-500 mt-1">דרגה</div>
          </div>
        </div>

        {user.phone_number && (
          <div className="mb-4 text-sm text-gray-600 ltr">{user.phone_number}</div>
        )}

        {user.last_seen_at && (
          <div className="mb-4 text-sm text-gray-500">
            נצפה לאחרונה: {new Date(user.last_seen_at).toLocaleString('he-IL')}
          </div>
        )}

        {/* VIP Toggle */}
        <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-100 mb-5">
          <div>
            <div className="text-sm font-medium text-gray-800">סטטוס VIP 👑</div>
            <div className="text-xs text-gray-500">VIP מקבל עדיפות ושירות מיוחד</div>
          </div>
          <button
            onClick={() => setVip(v => !v)}
            className={`relative w-12 h-6 rounded-full transition-colors ${vip ? 'bg-yellow-500' : 'bg-gray-200'}`}
          >
            <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all ${vip ? 'right-0.5' : 'left-0.5'}`} />
          </button>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => updateMutation.mutate({ tier: vip ? 'vip' : 'standard' })}
            disabled={updateMutation.isPending}
            className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {updateMutation.isPending ? 'שומר...' : 'שמור שינויים'}
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-100 text-gray-700 rounded-lg py-2 text-sm font-medium hover:bg-gray-200"
          >
            ביטול
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Users() {
  const [platformFilter, setPlatformFilter] = useState('')
  const [tierFilter, setTierFilter] = useState('')
  const [search, setSearch] = useState('')
  const [expandedUser, setExpandedUser] = useState(null)
  const [profileModal, setProfileModal] = useState(null)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users', platformFilter, tierFilter],
    queryFn: () =>
      axios.get('/api/v1/users', {
        params: {
          platform: platformFilter || undefined,
          tier: tierFilter || undefined,
          limit: 100,
        },
      }).then(r => r.data),
    refetchInterval: 30000,
  })

  const filtered = users.filter(u => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      (u.name || '').toLowerCase().includes(q) ||
      (u.phone_number || '').includes(q)
    )
  })

  return (
    <div className="p-8" dir="rtl">
      {profileModal && (
        <UserProfileModal
          user={profileModal}
          onClose={() => setProfileModal(null)}
          onUpdated={() => setProfileModal(null)}
        />
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ניהול משתמשים</h1>
        <p className="text-gray-500 mt-1">{filtered.length} משתמשים</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="חפש לפי שם או טלפון..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full border rounded-lg pr-9 px-3 py-2 text-sm"
          />
        </div>
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
                <th className="text-right px-4 py-3 font-medium text-gray-600">ערך לכל החיים</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">נצפה</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered.map(user => (
                <React.Fragment key={user.id}>
                  <tr
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedUser(expandedUser === user.id ? null : user.id)}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-800">{user.name || 'לא ידוע'}</div>
                      {user.phone_number && (
                        <div className="text-xs text-gray-400 ltr">{user.phone_number}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize text-gray-600">{user.platform}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${TIER_COLORS[user.tier] || 'bg-gray-100 text-gray-600'}`}>
                        {TIER_ICONS[user.tier]}
                        <span className="capitalize">{user.tier}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 ltr text-gray-700">{user.loyalty_points?.toLocaleString()}</td>
                    <td className="px-4 py-3 ltr text-gray-700">{user.purchase_count}</td>
                    <td className="px-4 py-3 ltr text-gray-700 font-medium text-green-700">
                      ₪{(user.total_purchases || 0).toFixed(0)}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {user.last_seen_at ? new Date(user.last_seen_at).toLocaleString('he-IL') : '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {expandedUser === user.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </td>
                  </tr>
                  {expandedUser === user.id && (
                    <tr className="bg-blue-50 border-b">
                      <td colSpan={8} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="grid grid-cols-3 gap-6 text-sm">
                            <div>
                              <span className="text-gray-500">סה״כ קניות: </span>
                              <span className="font-semibold text-green-700">₪{(user.total_purchases || 0).toFixed(2)}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">הזמנות: </span>
                              <span className="font-semibold">{user.purchase_count || 0}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">נקודות נאמנות: </span>
                              <span className="font-semibold text-purple-700">{user.loyalty_points?.toLocaleString() || 0}</span>
                            </div>
                          </div>
                          <button
                            onClick={e => { e.stopPropagation(); setProfileModal(user) }}
                            className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700"
                          >
                            ערוך פרופיל
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
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
