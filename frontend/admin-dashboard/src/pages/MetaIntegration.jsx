import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import {
  CheckCircle, XCircle, AlertCircle, Copy, RefreshCw,
  ExternalLink, Eye, EyeOff, Link2, Shield, Info
} from 'lucide-react'

const WEBHOOK_BASE = window.location.origin.includes('localhost')
  ? 'https://your-domain.com'
  : window.location.origin

function StatusBadge({ status }) {
  if (status === 'connected') {
    return (
      <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
        <CheckCircle size={16} /> מחובר
      </span>
    )
  }
  if (status === 'error') {
    return (
      <span className="flex items-center gap-1 text-red-500 text-sm font-medium">
        <XCircle size={16} /> שגיאה
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-gray-400 text-sm font-medium">
      <AlertCircle size={16} /> לא מוגדר
    </span>
  )
}

function CopyField({ label, value }) {
  const copy = () => {
    navigator.clipboard.writeText(value).then(() => toast.success('הועתק!'))
  }
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <code className="flex-1 bg-gray-100 rounded px-3 py-2 text-xs text-gray-700 font-mono truncate ltr">
          {value}
        </code>
        <button
          onClick={copy}
          className="shrink-0 text-gray-400 hover:text-blue-600 transition-colors"
        >
          <Copy size={16} />
        </button>
      </div>
    </div>
  )
}

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
          {show ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
    </div>
  )
}

function PlatformSection({ title, platform, emoji, status, webhookPath, docsUrl, children, onTest, testing }) {
  const [open, setOpen] = useState(true)
  const webhookUrl = `${WEBHOOK_BASE}/api/v1/webhooks/${webhookPath}`
  const curlCommand = `curl -X GET "${webhookUrl}?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"`

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-5 text-right"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{emoji}</span>
          <div>
            <div className="font-semibold text-gray-800 text-lg">{title}</div>
            <div className="mt-0.5">
              <StatusBadge status={status} />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="text-xs text-blue-600 hover:underline flex items-center gap-1"
          >
            <ExternalLink size={12} /> תיעוד Meta
          </a>
          <span className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}>▼</span>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-50 pt-4 space-y-4">
          {children}

          {/* Webhook URL */}
          <CopyField label="Webhook URL" value={webhookUrl} />

          {/* Last synced */}
          {status === 'connected' && (
            <div className="text-xs text-gray-400 flex items-center gap-1">
              <CheckCircle size={12} className="text-green-500" />
              Webhook פעיל ומחובר
            </div>
          )}

          {/* Test Webhook button */}
          <button
            onClick={() => onTest(platform)}
            disabled={testing === platform}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw size={14} className={testing === platform ? 'animate-spin' : ''} />
            {testing === platform ? 'בודק...' : 'בדוק Webhook'}
          </button>

          {/* Curl command */}
          <CopyField
            label="curl לבדיקת Webhook Verification"
            value={curlCommand}
          />
        </div>
      )}
    </div>
  )
}

export default function MetaIntegration() {
  const [testing, setTesting] = useState(null)
  const [waForm, setWaForm] = useState({ phone_id: '', api_token: '', business_account_id: '' })
  const [msgForm, setMsgForm] = useState({ page_id: '', page_token: '' })
  const [igForm, setIgForm] = useState({ account_id: '', page_token: '' })

  const { data: metaStatus = {} } = useQuery({
    queryKey: ['meta-status'],
    queryFn: () => axios.get('/api/v1/admin/meta/status').then(r => r.data).catch(() => ({})),
    refetchInterval: 30000,
  })

  const handleTest = async (platform) => {
    setTesting(platform)
    try {
      await axios.post('/api/v1/admin/meta/test-webhook', null, { params: { platform } })
      toast.success(`Webhook של ${platform} תקין ✅`)
    } catch {
      toast.error(`שגיאה בבדיקת Webhook של ${platform}`)
    } finally {
      setTesting(null)
    }
  }

  const waStatus = metaStatus?.whatsapp?.status || 'unknown'
  const msgStatus = metaStatus?.messenger?.status || 'unknown'
  const igStatus = metaStatus?.instagram?.status || 'unknown'

  const checklistItems = [
    {
      label: 'Privacy Policy',
      sub: 'נדרש לאישור Meta',
      url: '/privacy-policy',
      icon: Shield,
    },
    {
      label: 'Terms of Service',
      sub: 'נדרש לאישור Meta',
      url: '/terms',
      icon: Shield,
    },
    {
      label: 'Data Deletion Endpoint',
      sub: '/api/v1/webhooks/data-deletion',
      url: null,
      endpoint: `${WEBHOOK_BASE}/api/v1/webhooks/data-deletion`,
      icon: Link2,
    },
    {
      label: 'Webhook Verification',
      sub: 'כל ה-webhooks מוגנים עם HMAC',
      url: null,
      icon: CheckCircle,
      done: true,
    },
  ]

  return (
    <div className="p-8" dir="rtl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Meta Platform Integration</h1>
        <p className="text-gray-500 mt-1">חיבור ופיקוח על WhatsApp, Messenger ו-Instagram</p>
      </div>

      <div className="space-y-6">
        {/* WhatsApp */}
        <PlatformSection
          title="WhatsApp Business API"
          platform="whatsapp"
          emoji="📱"
          status={waStatus}
          webhookPath="whatsapp"
          docsUrl="https://developers.facebook.com/docs/whatsapp/cloud-api"
          onTest={handleTest}
          testing={testing}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number ID</label>
              <input
                type="text"
                value={waForm.phone_id}
                onChange={e => setWaForm(f => ({ ...f, phone_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Account ID</label>
              <input
                type="text"
                value={waForm.business_account_id}
                onChange={e => setWaForm(f => ({ ...f, business_account_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <div className="md:col-span-2">
              <MaskedInput
                label="API Token"
                name="api_token"
                value={waForm.api_token}
                onChange={e => setWaForm(f => ({ ...f, api_token: e.target.value }))}
              />
            </div>
          </div>
        </PlatformSection>

        {/* Messenger */}
        <PlatformSection
          title="Meta Messenger"
          platform="messenger"
          emoji="💬"
          status={msgStatus}
          webhookPath="messenger"
          docsUrl="https://developers.facebook.com/docs/messenger-platform"
          onTest={handleTest}
          testing={testing}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Page ID</label>
              <input
                type="text"
                value={msgForm.page_id}
                onChange={e => setMsgForm(f => ({ ...f, page_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <MaskedInput
              label="Page Token"
              name="page_token"
              value={msgForm.page_token}
              onChange={e => setMsgForm(f => ({ ...f, page_token: e.target.value }))}
            />
          </div>
        </PlatformSection>

        {/* Instagram */}
        <PlatformSection
          title="Instagram Business"
          platform="instagram"
          emoji="📸"
          status={igStatus}
          webhookPath="instagram"
          docsUrl="https://developers.facebook.com/docs/instagram-api/guides/webhooks"
          onTest={handleTest}
          testing={testing}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Account ID</label>
              <input
                type="text"
                value={igForm.account_id}
                onChange={e => setIgForm(f => ({ ...f, account_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="1234567890"
              />
            </div>
            <MaskedInput
              label="Page Access Token"
              name="page_token"
              value={igForm.page_token}
              onChange={e => setIgForm(f => ({ ...f, page_token: e.target.value }))}
            />
          </div>
        </PlatformSection>

        {/* Verification Checklist */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={18} className="text-blue-600" />
            <h3 className="font-semibold text-gray-800">רשימת בדיקה לאישור Meta</h3>
          </div>
          <div className="space-y-3">
            {checklistItems.map((item, idx) => (
              <div key={idx} className="flex items-start gap-3 py-2 border-b last:border-0">
                <div className={`mt-0.5 ${item.done ? 'text-green-500' : 'text-gray-300'}`}>
                  {item.done ? <CheckCircle size={16} /> : <item.icon size={16} />}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-800">{item.label}</div>
                  <div className="text-xs text-gray-400">{item.sub}</div>
                  {item.endpoint && (
                    <div className="mt-1">
                      <CopyField label="" value={item.endpoint} />
                    </div>
                  )}
                </div>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1 shrink-0"
                  >
                    <ExternalLink size={12} /> פתח
                  </a>
                )}
              </div>
            ))}
          </div>

          {/* Info box */}
          <div className="mt-4 bg-blue-50 rounded-lg p-4 flex gap-3">
            <Info size={16} className="text-blue-600 mt-0.5 shrink-0" />
            <p className="text-xs text-blue-700">
              לצורך אישור Meta, ודא שהאפליקציה כוללת עמוד Privacy Policy, Terms of Service
              ו-Data Deletion endpoint פעיל. כל ה-webhooks מוגנים עם HMAC-SHA256.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
