import React, { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import { ChevronDown, Crown, Search, User } from 'lucide-react'
import UserProfileModal from '../components/UserProfileModal.jsx'

export default function UserManagement() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [platform, setPlatform] = useState('')
  const [vipOnly, setVipOnly] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [expandedUserId, setExpandedUserId] = useState(null)
  const [selectedUser, setSelectedUser] = useState(null)

  const filters = useMemo(() => ({
    search: search || undefined,
    platform: platform || undefined,
    vip: vipOnly === '' ? undefined : vipOnly === 'true',
    is_active: activeFilter === '' ? undefined : activeFilter === 'true',
  }), [search, platform, vipOnly, activeFilter])

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users', filters],
    queryFn: () => axios.get('/api/v1/admin/users', { params: filters }).then(r => r.data),
  })

  const { data: details } = useQuery({
    queryKey: ['admin-user-details', expandedUserId],
    enabled: Boolean(expandedUserId),
    queryFn: () => axios.get(`/api/v1/admin/users/${expandedUserId}`).then(r => r.data),
  })

  const updateUser = useMutation({
    mutationFn: ({ userId, payload }) => axios.put(`/api/v1/admin/users/${userId}`, payload),
    onSuccess: () => {
      toast.success('המשתמש עודכן')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      if (expandedUserId) queryClient.invalidateQueries({ queryKey: ['admin-user-details', expandedUserId] })
    },
    onError: () => toast.error('שגיאה בעדכון משתמש'),
  })

  return (
    <div className="p-4 md:p-8" dir="rtl">
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">User Management</h1>
        <p className="text-gray-500 dark:text-gray-400">ניהול משתמשים, פעילות ופילוחים</p>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4 mb-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="relative">
          <Search size={14} className="absolute top-3 right-3 text-gray-400" />
          <input className="w-full border rounded-lg px-9 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="חיפוש שם/אימייל" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={platform} onChange={e => setPlatform(e.target.value)}>
          <option value="">כל הפלטפורמות</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="messenger">Messenger</option>
          <option value="instagram">Instagram</option>
        </select>
        <select className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={vipOnly} onChange={e => setVipOnly(e.target.value)}>
          <option value="">כל המשתמשים</option>
          <option value="true">VIP בלבד</option>
          <option value="false">ללא VIP</option>
        </select>
        <select className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={activeFilter} onChange={e => setActiveFilter(e.target.value)}>
          <option value="">כולם</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 overflow-x-auto">
        <table className="w-full text-sm min-w-[850px]">
          <thead className="bg-gray-50 dark:bg-slate-800/80 text-gray-600 dark:text-gray-300">
            <tr>
              <th className="p-3 text-right">שם</th>
              <th className="p-3 text-right">Email</th>
              <th className="p-3 text-right">Platform</th>
              <th className="p-3 text-right">Join Date</th>
              <th className="p-3 text-right">VIP</th>
              <th className="p-3 text-right">Last Activity</th>
              <th className="p-3 text-right">סטטוס</th>
              <th className="p-3 text-right">פעולות</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={8} className="p-8 text-center text-gray-400">טוען...</td></tr>
            ) : users.map(user => {
              const isExpanded = expandedUserId === user.id
              return (
                <React.Fragment key={user.id}>
                  <tr className="border-t border-gray-100 dark:border-slate-700">
                    <td className="p-3">
                      <button className="flex items-center gap-2" onClick={() => setExpandedUserId(isExpanded ? null : user.id)}>
                        <ChevronDown size={14} className={`transition ${isExpanded ? 'rotate-180' : ''}`} />
                        <span className="font-medium text-gray-800 dark:text-gray-100">{user.name || '-'}</span>
                      </button>
                    </td>
                    <td className="p-3 text-gray-600 dark:text-gray-300">{user.email || '-'}</td>
                    <td className="p-3 capitalize text-gray-600 dark:text-gray-300">{user.platform}</td>
                    <td className="p-3 text-gray-500">{user.join_date ? new Date(user.join_date).toLocaleDateString('he-IL') : '-'}</td>
                    <td className="p-3">{user.is_vip ? <Crown size={16} className="text-yellow-500" /> : '-'}</td>
                    <td className="p-3 text-gray-500">{user.last_seen_at ? new Date(user.last_seen_at).toLocaleString('he-IL') : '-'}</td>
                    <td className="p-3">
                      <span className={`inline-block w-2 h-2 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    </td>
                    <td className="p-3">
                      <div className="flex gap-2">
                        <button onClick={() => updateUser.mutate({ userId: user.id, payload: { is_vip: !user.is_vip } })} className="px-2 py-1 rounded bg-yellow-100 text-yellow-700 text-xs">{user.is_vip ? 'הסר VIP' : 'Mark VIP'}</button>
                        <button onClick={() => setSelectedUser(details && details.id === user.id ? details : user)} className="px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs">פרופיל</button>
                      </div>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr className="bg-gray-50/60 dark:bg-slate-800/40">
                      <td colSpan={8} className="p-4">
                        {!details || details.id !== user.id ? (
                          <div className="text-gray-400">טוען פרטי משתמש...</div>
                        ) : (
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
                            <div><div className="text-gray-500">Purchase history</div><div className="font-medium dark:text-gray-100">{details.purchase_history?.length || 0} הזמנות</div></div>
                            <div><div className="text-gray-500">Lifetime value</div><div className="font-medium dark:text-gray-100">₪{(details.lifetime_value || 0).toFixed(2)}</div></div>
                            <div><div className="text-gray-500">Engagement score</div><div className="font-medium dark:text-gray-100">{details.engagement_score || 0}/100</div></div>
                            <div>
                              <div className="text-gray-500">Tags/segments</div>
                              <div className="font-medium dark:text-gray-100">{(details.tags || []).join(', ') || details.segment || '-'}</div>
                            </div>
                            <div className="md:col-span-4 flex items-center gap-2">
                              <input defaultValue={details.segment || ''} onBlur={e => updateUser.mutate({ userId: user.id, payload: { segment: e.target.value } })} className="border rounded px-3 py-2 text-sm w-full md:max-w-sm dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="עריכת סגמנט" />
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
            {!isLoading && users.length === 0 && (
              <tr><td colSpan={8} className="p-8 text-center text-gray-400"><User className="mx-auto mb-2" />אין משתמשים</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <UserProfileModal user={selectedUser} onClose={() => setSelectedUser(null)} />
    </div>
  )
}
