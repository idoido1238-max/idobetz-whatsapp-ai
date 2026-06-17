import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Play, Pause, X, Clock, Plus, Megaphone } from 'lucide-react'

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-600',
  scheduled: 'bg-blue-100 text-blue-700',
  running: 'bg-green-100 text-green-700',
  paused: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-purple-100 text-purple-700',
  cancelled: 'bg-red-100 text-red-700',
}

const STATUS_HE = {
  draft: 'טיוטה',
  scheduled: 'מתוזמן',
  running: 'פעיל',
  paused: 'מושהה',
  completed: 'הושלם',
  cancelled: 'בוטל',
}

const TYPE_HE = {
  broadcast: 'שידור',
  scheduled: 'מתוזמן',
  abandoned_cart: 'עגלה נטושה',
  birthday: 'יום הולדת',
  anniversary: 'יום שנה',
  reengagement: 'החזרת לקוחות',
  loyalty_reward: 'פרס נאמנות',
  reorder_reminder: 'תזכורת הזמנה',
  custom: 'מותאם אישית',
}

function CreateCampaignModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: '',
    campaign_type: 'broadcast',
    message_content_he: '',
    message_content: '',
    target_platform: 'whatsapp',
  })

  const mutation = useMutation({
    mutationFn: (data) => axios.post('/api/v1/campaigns', data),
    onSuccess: () => {
      toast.success('קמפיין נוצר בהצלחה')
      onCreated()
      onClose()
    },
    onError: () => toast.error('שגיאה ביצירת קמפיין'),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" dir="rtl">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">קמפיין חדש</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">שם הקמפיין</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="שם תיאורי לקמפיין"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">סוג קמפיין</label>
            <select
              value={form.campaign_type}
              onChange={e => setForm(p => ({ ...p, campaign_type: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              {Object.entries(TYPE_HE).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">הודעה (עברית)</label>
            <textarea
              value={form.message_content_he}
              onChange={e => setForm(p => ({ ...p, message_content_he: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none"
              placeholder="תוכן ההודעה בעברית..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">פלטפורמה</label>
            <select
              value={form.target_platform}
              onChange={e => setForm(p => ({ ...p, target_platform: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="whatsapp">WhatsApp</option>
              <option value="messenger">Messenger</option>
              <option value="instagram">Instagram</option>
              <option value="all">כל הפלטפורמות</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={() => mutation.mutate({ ...form, message_content: form.message_content_he })}
            disabled={!form.name || !form.message_content_he || mutation.isPending}
            className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium
              hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? 'יוצר...' : 'צור קמפיין'}
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

export default function Campaigns() {
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => axios.get('/api/v1/campaigns').then(r => r.data),
    refetchInterval: 15000,
  })

  const activateMutation = useMutation({
    mutationFn: (id) => axios.post(`/api/v1/campaigns/${id}/activate`),
    onSuccess: () => { toast.success('קמפיין הופעל'); queryClient.invalidateQueries(['campaigns']) },
    onError: (e) => toast.error(e.response?.data?.detail || 'שגיאה'),
  })

  const pauseMutation = useMutation({
    mutationFn: (id) => axios.post(`/api/v1/campaigns/${id}/pause`),
    onSuccess: () => { toast.success('קמפיין הושהה'); queryClient.invalidateQueries(['campaigns']) },
  })

  const cancelMutation = useMutation({
    mutationFn: (id) => axios.post(`/api/v1/campaigns/${id}/cancel`),
    onSuccess: () => { toast.success('קמפיין בוטל'); queryClient.invalidateQueries(['campaigns']) },
  })

  return (
    <div className="p-8" dir="rtl">
      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreated={() => queryClient.invalidateQueries(['campaigns'])}
        />
      )}

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">קמפיינים</h1>
          <p className="text-gray-500 mt-1">ניהול קמפיינים שיווקיים</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          קמפיין חדש
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">טוען...</div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-12">
          <Megaphone size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">אין קמפיינים עדיין</p>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-800">{campaign.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[campaign.status]}`}>
                      {STATUS_HE[campaign.status] || campaign.status}
                    </span>
                    <span className="text-xs text-gray-400">
                      {TYPE_HE[campaign.campaign_type] || campaign.campaign_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="text-gray-400">נמענים: </span>
                      <span className="font-medium">{campaign.total_recipients}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">נשלח: </span>
                      <span className="font-medium">{campaign.sent_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">נקרא: </span>
                      <span className="font-medium">{campaign.read_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">המרות: </span>
                      <span className="font-medium">{campaign.conversion_count}</span>
                    </div>
                  </div>

                  {campaign.scheduled_at && (
                    <div className="text-xs text-blue-500 mt-2 flex items-center gap-1">
                      <Clock size={12} />
                      מתוזמן: {new Date(campaign.scheduled_at).toLocaleString('he-IL')}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 mr-4">
                  {campaign.status === 'draft' && (
                    <button
                      onClick={() => activateMutation.mutate(campaign.id)}
                      className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-green-700"
                    >
                      <Play size={14} />
                      הפעל
                    </button>
                  )}
                  {campaign.status === 'running' && (
                    <button
                      onClick={() => pauseMutation.mutate(campaign.id)}
                      className="flex items-center gap-1 bg-yellow-500 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-yellow-600"
                    >
                      <Pause size={14} />
                      השהה
                    </button>
                  )}
                  {['draft', 'scheduled', 'paused'].includes(campaign.status) && (
                    <button
                      onClick={() => cancelMutation.mutate(campaign.id)}
                      className="flex items-center gap-1 bg-red-50 text-red-600 px-3 py-1.5 rounded-lg text-sm hover:bg-red-100"
                    >
                      <X size={14} />
                      בטל
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
