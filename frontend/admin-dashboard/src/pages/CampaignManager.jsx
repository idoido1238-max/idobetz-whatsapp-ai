import React, { useMemo, useState } from 'react'
import { Copy, Megaphone, Pause, Pencil, Plus, Trash2 } from 'lucide-react'
import CampaignModal from '../components/CampaignModal.jsx'
import { useCampaignActions, useCampaigns } from '../hooks/useCampaigns.js'

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700',
  scheduled: 'bg-blue-100 text-blue-700',
  running: 'bg-green-100 text-green-700',
  paused: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-purple-100 text-purple-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function CampaignManager() {
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [activeCampaign, setActiveCampaign] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)

  const filters = useMemo(() => ({ status: status || undefined, search: search || undefined }), [status, search])
  const { data: campaigns = [], isLoading } = useCampaigns(filters)
  const { createCampaign, updateCampaign, deleteCampaign } = useCampaignActions()

  const openCreate = () => {
    setActiveCampaign(null)
    setModalOpen(true)
  }

  const openEdit = campaign => {
    setActiveCampaign(campaign)
    setModalOpen(true)
  }

  const onSave = payload => {
    if (activeCampaign) {
      updateCampaign.mutate({ id: activeCampaign.id, payload }, { onSuccess: () => setModalOpen(false) })
      return
    }
    createCampaign.mutate(payload, { onSuccess: () => setModalOpen(false) })
  }

  const duplicateCampaign = campaign => {
    createCampaign.mutate({
      ...campaign,
      name: `${campaign.name} (עותק)`,
      status: 'draft',
      scheduled_at: null,
    })
  }

  return (
    <div className="p-4 md:p-8" dir="rtl">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">Campaign Manager</h1>
          <p className="text-gray-500 dark:text-gray-400">ניהול קמפיינים, תזמון וביצועים</p>
        </div>
        <button onClick={openCreate} className="flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg">
          <Plus size={16} /> קמפיין חדש
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4 mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <input className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="חיפוש קמפיין..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">כל הסטטוסים</option>
          <option value="draft">DRAFT</option>
          <option value="scheduled">SCHEDULED</option>
          <option value="running">RUNNING</option>
          <option value="paused">PAUSED</option>
          <option value="completed">COMPLETED</option>
        </select>
      </div>

      {isLoading ? <div className="py-10 text-center text-gray-500">טוען...</div> : (
        <div className="space-y-3">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-700 rounded-xl p-4">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{campaign.name}</h3>
                    <span className={`text-xs px-2 py-1 rounded-full ${STATUS_COLORS[campaign.status] || STATUS_COLORS.draft}`}>{(campaign.status || '').toUpperCase()}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm text-gray-600 dark:text-gray-300">
                    <div>נשלח: <b>{campaign.sent_count || 0}</b></div>
                    <div>פתיחות: <b>{campaign.read_count || 0}</b></div>
                    <div>קליקים/המרות: <b>{campaign.conversion_count || 0}</b></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">תזמון: {campaign.scheduled_at ? new Date(campaign.scheduled_at).toLocaleString('he-IL') : 'ללא'}</div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button onClick={() => openEdit(campaign)} className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-slate-800 dark:text-gray-200 flex items-center gap-1"><Pencil size={14} />ערוך</button>
                  <button onClick={() => updateCampaign.mutate({ id: campaign.id, payload: { status: 'paused' } })} className="px-3 py-2 rounded-lg bg-yellow-100 text-yellow-700 flex items-center gap-1"><Pause size={14} />השהה</button>
                  <button onClick={() => duplicateCampaign(campaign)} className="px-3 py-2 rounded-lg bg-blue-100 text-blue-700 flex items-center gap-1"><Copy size={14} />שכפל</button>
                  <button onClick={() => deleteCampaign.mutate(campaign.id)} className="px-3 py-2 rounded-lg bg-red-100 text-red-700 flex items-center gap-1"><Trash2 size={14} />מחק</button>
                </div>
              </div>
            </div>
          ))}

          {campaigns.length === 0 && (
            <div className="text-center py-10 text-gray-400">
              <Megaphone className="mx-auto mb-2" size={34} />
              אין קמפיינים להצגה
            </div>
          )}
        </div>
      )}

      <CampaignModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={onSave}
        initialData={activeCampaign}
        isSaving={createCampaign.isPending || updateCampaign.isPending}
      />
    </div>
  )
}
