import React, { useMemo, useState } from 'react'
import { X } from 'lucide-react'

const CAMPAIGN_TYPES = [
  { value: 'broadcast', label: 'שידור' },
  { value: 'scheduled', label: 'מתוזמן' },
  { value: 'abandoned_cart', label: 'עגלה נטושה' },
  { value: 'birthday', label: 'יום הולדת' },
  { value: 'custom', label: 'מותאם אישית' },
]

const TEMPLATE_OPTIONS = [
  { value: '', label: 'ללא תבנית' },
  { value: 'welcome', label: 'Welcome' },
  { value: 'promotion', label: 'Promotion' },
  { value: 'followup', label: 'Follow-up' },
]

export default function CampaignModal({ isOpen, onClose, onSave, initialData, isSaving }) {
  const initialScheduled = useMemo(() => {
    if (!initialData?.scheduled_at) return ''
    const date = new Date(initialData.scheduled_at)
    return Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 16)
  }, [initialData])

  const [form, setForm] = useState({
    name: initialData?.name || '',
    campaign_type: initialData?.campaign_type || 'broadcast',
    status: initialData?.status || 'draft',
    message_content_he: initialData?.message_content_he || initialData?.message_content || '',
    target_platform: initialData?.target_platform || 'whatsapp',
    target_segment: initialData?.target_segment?.segment || '',
    target_tags: (initialData?.target_tags || []).join(', '),
    target_user_tiers: (initialData?.target_user_tiers || []).join(', '),
    template_id: initialData?.template_id || '',
    scheduled_at: initialScheduled,
  })

  if (!isOpen) return null

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  const handleSubmit = () => {
    onSave({
      ...form,
      message_content: form.message_content_he,
      target_segment: form.target_segment ? { segment: form.target_segment } : {},
      target_tags: form.target_tags.split(',').map(v => v.trim()).filter(Boolean),
      target_user_tiers: form.target_user_tiers.split(',').map(v => v.trim()).filter(Boolean),
      scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" dir="rtl">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700 shadow-xl">
        <div className="p-4 border-b border-gray-100 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{initialData ? 'עריכת קמפיין' : 'קמפיין חדש'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400">
            <X size={18} />
          </button>
        </div>

        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="text-sm text-gray-700 dark:text-gray-300">שם קמפיין</label>
            <input className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.name} onChange={e => update('name', e.target.value)} />
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">סוג קמפיין</label>
            <select className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.campaign_type} onChange={e => update('campaign_type', e.target.value)}>
              {CAMPAIGN_TYPES.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">סטטוס</label>
            <select className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.status} onChange={e => update('status', e.target.value)}>
              <option value="draft">DRAFT</option>
              <option value="scheduled">SCHEDULED</option>
              <option value="running">RUNNING</option>
              <option value="paused">PAUSED</option>
              <option value="completed">COMPLETED</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">תאריך ושעת שליחה</label>
            <input type="datetime-local" className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.scheduled_at} onChange={e => update('scheduled_at', e.target.value)} />
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">פילטר קהל יעד</label>
            <input className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="למשל: vip" value={form.target_segment} onChange={e => update('target_segment', e.target.value)} />
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">פלטפורמה</label>
            <select className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.target_platform} onChange={e => update('target_platform', e.target.value)}>
              <option value="whatsapp">WhatsApp</option>
              <option value="messenger">Messenger</option>
              <option value="instagram">Instagram</option>
              <option value="all">All</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-700 dark:text-gray-300">תבנית</label>
            <select className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.template_id} onChange={e => update('template_id', e.target.value)}>
              {TEMPLATE_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm text-gray-700 dark:text-gray-300">תגיות</label>
            <input className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="vip, summer-sale" value={form.target_tags} onChange={e => update('target_tags', e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="text-sm text-gray-700 dark:text-gray-300">שכבות לקוחות</label>
            <input className="w-full border rounded-lg px-3 py-2 mt-1 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="standard, vip" value={form.target_user_tiers} onChange={e => update('target_user_tiers', e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="text-sm text-gray-700 dark:text-gray-300">תוכן הודעה</label>
            <textarea className="w-full border rounded-lg px-3 py-2 mt-1 h-28 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={form.message_content_he} onChange={e => update('message_content_he', e.target.value)} />
          </div>
        </div>

        <div className="p-4 border-t border-gray-100 dark:border-slate-700 flex gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-slate-800 dark:text-gray-200">ביטול</button>
          <button onClick={handleSubmit} disabled={!form.name || isSaving} className="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-60">
            {isSaving ? 'שומר...' : 'שמור'}
          </button>
        </div>
      </div>
    </div>
  )
}
