import React, { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

const defaults = {
  openai_api_key: '',
  claude_api_key: '',
  whatsapp_api_token: '',
  whatsapp_phone_id: '',
  messenger_token_status: 'not_configured',
  instagram_business_id: '',
  website_api_url: '',
  bot_name: '',
  response_language: 'he',
  support_email: '',
  theme: 'light',
}

export default function Settings() {
  const [form, setForm] = useState(defaults)

  const { data } = useQuery({
    queryKey: ['admin-settings'],
    queryFn: () => axios.get('/api/v1/admin/settings').then(r => r.data),
  })

  useEffect(() => {
    if (data) setForm(prev => ({ ...prev, ...data }))
  }, [data])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', form.theme === 'dark')
  }, [form.theme])

  const saveMutation = useMutation({
    mutationFn: payload => axios.put('/api/v1/admin/settings', payload),
    onSuccess: () => toast.success('ההגדרות נשמרו בהצלחה'),
    onError: () => toast.error('שגיאה בשמירת הגדרות'),
  })

  const testMutation = useMutation({
    mutationFn: () => axios.post('/api/v1/admin/settings/test-connection'),
    onSuccess: () => toast.success('בדיקת חיבור הושלמה'),
    onError: () => toast.error('בדיקת חיבור נכשלה'),
  })

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  return (
    <div className="p-4 md:p-8" dir="rtl">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">Settings</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">ניהול תצורות API, אינטגרציות והגדרות כלליות</p>

      <div className="space-y-4">
        <section className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
          <h3 className="font-semibold mb-3 dark:text-gray-100">API Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input type="password" value={form.openai_api_key} onChange={e => update('openai_api_key', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="OPENAI_API_KEY" />
            <input type="password" value={form.claude_api_key} onChange={e => update('claude_api_key', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="CLAUDE_API_KEY" />
            <input type="password" value={form.whatsapp_api_token} onChange={e => update('whatsapp_api_token', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="WHATSAPP_API_TOKEN" />
          </div>
        </section>

        <section className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
          <h3 className="font-semibold mb-3 dark:text-gray-100">Platform Integration</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input value={form.whatsapp_phone_id} onChange={e => update('whatsapp_phone_id', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="WhatsApp Phone ID" />
            <input value={form.messenger_token_status} onChange={e => update('messenger_token_status', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="Messenger Token status" />
            <input value={form.instagram_business_id} onChange={e => update('instagram_business_id', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="Instagram Business ID" />
          </div>
        </section>

        <section className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
          <h3 className="font-semibold mb-3 dark:text-gray-100">Website Integration</h3>
          <div className="flex flex-col md:flex-row gap-3">
            <input value={form.website_api_url} onChange={e => update('website_api_url', e.target.value)} className="flex-1 border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="API URL" />
            <button onClick={() => testMutation.mutate()} className="bg-blue-100 text-blue-700 px-4 py-2 rounded-lg">Test connection</button>
          </div>
        </section>

        <section className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
          <h3 className="font-semibold mb-3 dark:text-gray-100">General Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input value={form.bot_name} onChange={e => update('bot_name', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="Bot name" />
            <select value={form.response_language} onChange={e => update('response_language', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white">
              <option value="he">Hebrew</option>
              <option value="en">English</option>
            </select>
            <input value={form.support_email} onChange={e => update('support_email', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white" placeholder="Support email" />
            <select value={form.theme} onChange={e => update('theme', e.target.value)} className="border rounded-lg px-3 py-2 dark:bg-slate-800 dark:border-slate-700 dark:text-white">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
        </section>

        <button onClick={() => saveMutation.mutate(form)} className="bg-green-600 text-white px-5 py-2 rounded-lg">Save</button>
      </div>
    </div>
  )
}
