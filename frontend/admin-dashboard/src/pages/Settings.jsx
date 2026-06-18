import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import {
  Settings as SettingsIcon, Eye, EyeOff, Sun, Moon,
  CheckCircle, AlertCircle, Save, RefreshCw
} from 'lucide-react'

function MaskedInput({ label, name, value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder || '••••••••'}
          className="w-full border rounded-lg px-3 py-2 text-sm pl-9"
          autoComplete="new-password"
        />
        <button
          type="button"
          onClick={() => setShow(s => !s)}
          className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  )
}

const CONNECTION_ITEMS = [
  { key: 'openai', name: 'OpenAI GPT-4o' },
  { key: 'claude', name: 'Anthropic Claude' },
  { key: 'whatsapp', name: 'WhatsApp Business API' },
  { key: 'messenger', name: 'Meta Messenger API' },
  { key: 'instagram', name: 'Instagram API' },
  { key: 'website', name: 'Website API' },
  { key: 'postgres', name: 'PostgreSQL' },
  { key: 'redis', name: 'Redis' },
]

export default function Settings() {
  const [darkMode, setDarkMode] = useState(
    () => document.documentElement.classList.contains('dark')
  )
  const [form, setForm] = useState({
    openai_api_key: '',
    claude_api_key: '',
    whatsapp_phone_id: '',
    whatsapp_api_token: '',
    messenger_page_id: '',
    messenger_page_token: '',
    instagram_account_id: '',
    instagram_page_token: '',
    website_api_url: '',
    website_api_key: '',
  })
  const [testing, setTesting] = useState(null)

  const { data: statusData = {} } = useQuery({
    queryKey: ['settings-status'],
    queryFn: () => axios.get('/api/v1/admin/settings').then(r => r.data).catch(() => ({})),
    refetchInterval: 30000,
  })

  const saveMutation = useMutation({
    mutationFn: (data) => axios.put('/api/v1/admin/settings', data),
    onSuccess: () => toast.success('הגדרות נשמרו בהצלחה'),
    onError: () => toast.error('שגיאה בשמירת הגדרות'),
  })

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSave = () => {
    const filtered = Object.fromEntries(
      Object.entries(form).filter(([, v]) => v !== '')
    )
    saveMutation.mutate(filtered)
  }

  const handleTest = async (platform) => {
    setTesting(platform)
    try {
      await axios.post('/api/v1/admin/settings/test-connection', null, { params: { platform } })
      toast.success(`חיבור ל-${platform} תקין`)
    } catch {
      toast.error(`לא ניתן להתחבר ל-${platform}`)
    } finally {
      setTesting(null)
    }
  }

  const toggleDark = () => {
    const next = !darkMode
    setDarkMode(next)
    document.documentElement.classList.toggle('dark', next)
    toast.success(next ? 'מצב כהה הופעל' : 'מצב בהיר הופעל')
  }

  const getStatus = (key) => {
    const s = statusData?.connections?.[key]
    if (s === true || s === 'connected') return 'connected'
    if (s === false || s === 'error') return 'error'
    return 'unknown'
  }

  return (
    <div className="p-8" dir="rtl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">הגדרות</h1>
          <p className="text-gray-500 mt-1">תצורת המערכת</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleDark}
            className="flex items-center gap-2 border rounded-lg px-3 py-2 text-sm hover:bg-gray-50"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
            {darkMode ? 'מצב בהיר' : 'מצב כהה'}
          </button>
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            <Save size={16} />
            {saveMutation.isPending ? 'שומר...' : 'שמור הגדרות'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI API Keys */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">מפתחות API לבינה מלאכותית</h3>
          <div className="space-y-4">
            <MaskedInput
              label="OpenAI API Key"
              name="openai_api_key"
              value={form.openai_api_key}
              onChange={handleChange}
              placeholder="sk-..."
            />
            <MaskedInput
              label="Anthropic Claude API Key"
              name="claude_api_key"
              value={form.claude_api_key}
              onChange={handleChange}
              placeholder="sk-ant-..."
            />
          </div>
        </div>

        {/* WhatsApp */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">WhatsApp Business</h3>
            <button
              onClick={() => handleTest('whatsapp')}
              disabled={testing === 'whatsapp'}
              className="text-xs flex items-center gap-1 text-blue-600 hover:underline disabled:opacity-50"
            >
              <RefreshCw size={12} className={testing === 'whatsapp' ? 'animate-spin' : ''} />
              בדוק חיבור
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone ID</label>
              <input
                type="text"
                name="whatsapp_phone_id"
                value={form.whatsapp_phone_id}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <MaskedInput
              label="API Token"
              name="whatsapp_api_token"
              value={form.whatsapp_api_token}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Messenger */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Meta Messenger</h3>
            <button
              onClick={() => handleTest('messenger')}
              disabled={testing === 'messenger'}
              className="text-xs flex items-center gap-1 text-blue-600 hover:underline disabled:opacity-50"
            >
              <RefreshCw size={12} className={testing === 'messenger' ? 'animate-spin' : ''} />
              בדוק חיבור
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Page ID</label>
              <input
                type="text"
                name="messenger_page_id"
                value={form.messenger_page_id}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <MaskedInput
              label="Page Token"
              name="messenger_page_token"
              value={form.messenger_page_token}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Instagram */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Instagram Business</h3>
            <button
              onClick={() => handleTest('instagram')}
              disabled={testing === 'instagram'}
              className="text-xs flex items-center gap-1 text-blue-600 hover:underline disabled:opacity-50"
            >
              <RefreshCw size={12} className={testing === 'instagram' ? 'animate-spin' : ''} />
              בדוק חיבור
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Account ID</label>
              <input
                type="text"
                name="instagram_account_id"
                value={form.instagram_account_id}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <MaskedInput
              label="Page Access Token"
              name="instagram_page_token"
              value={form.instagram_page_token}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Website API */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Website API</h3>
            <button
              onClick={() => handleTest('website')}
              disabled={testing === 'website'}
              className="text-xs flex items-center gap-1 text-blue-600 hover:underline disabled:opacity-50"
            >
              <RefreshCw size={12} className={testing === 'website' ? 'animate-spin' : ''} />
              בדוק חיבור
            </button>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website API URL</label>
              <input
                type="url"
                name="website_api_url"
                value={form.website_api_url}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="https://your-store.com/api"
              />
            </div>
            <MaskedInput
              label="API Key"
              name="website_api_key"
              value={form.website_api_key}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Platform Integration Status */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">סטטוס חיבורים</h3>
          <div className="space-y-2">
            {CONNECTION_ITEMS.map(item => {
              const status = getStatus(item.key)
              return (
                <div key={item.key} className="flex items-center justify-between py-1.5 border-b last:border-0">
                  <span className="text-sm text-gray-700">{item.name}</span>
                  <span className={`flex items-center gap-1 text-xs font-medium ${
                    status === 'connected' ? 'text-green-600' :
                    status === 'error' ? 'text-red-500' : 'text-yellow-600'
                  }`}>
                    {status === 'connected'
                      ? <CheckCircle size={13} />
                      : <AlertCircle size={13} />}
                    {status === 'connected' ? 'פעיל' : status === 'error' ? 'שגיאה' : 'לא מוגדר'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Environment note */}
      <div className="mt-6 bg-blue-50 rounded-xl p-5 border border-blue-100">
        <div className="flex items-start gap-3">
          <SettingsIcon size={18} className="text-blue-600 mt-0.5 shrink-0" />
          <div>
            <h4 className="font-semibold text-blue-800 mb-1">שים לב</h4>
            <p className="text-sm text-blue-700">
              שינויים ב-API keys ישפיעו מיידית. ניתן גם לנהל הגדרות דרך קובץ{' '}
              <code className="bg-blue-100 px-1 rounded">.env</code>.
              הערכים לא מוצגים מסיבות אבטחה — מלא רק שדות שברצונך לעדכן.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
