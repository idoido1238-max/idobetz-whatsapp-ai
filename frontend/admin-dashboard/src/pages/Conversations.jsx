import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { MessageCircle, Clock, User } from 'lucide-react'

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-700',
  resolved: 'bg-gray-100 text-gray-700',
  escalated: 'bg-red-100 text-red-700',
  waiting: 'bg-yellow-100 text-yellow-700',
}

const SENTIMENT_COLORS = {
  positive: 'text-green-600',
  negative: 'text-red-600',
  neutral: 'text-gray-500',
}

export default function Conversations() {
  const [selected, setSelected] = useState(null)
  const [platformFilter, setPlatformFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ['conversations', platformFilter, statusFilter],
    queryFn: () =>
      axios.get('/api/v1/admin/conversations', {
        params: { platform: platformFilter || undefined, status: statusFilter || undefined },
      }).then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: messages = [] } = useQuery({
    queryKey: ['messages', selected],
    queryFn: () =>
      axios.get(`/api/v1/admin/conversations/${selected}/messages`).then(r => r.data),
    enabled: !!selected,
  })

  return (
    <div className="h-screen flex" dir="rtl">
      {/* Conversation list */}
      <div className="w-96 border-l bg-white flex flex-col">
        {/* Filters */}
        <div className="p-4 border-b space-y-2">
          <h2 className="font-semibold text-gray-800 text-lg">שיחות</h2>
          <div className="flex gap-2">
            <select
              value={platformFilter}
              onChange={e => setPlatformFilter(e.target.value)}
              className="flex-1 text-sm border rounded-lg px-2 py-1.5 bg-gray-50"
            >
              <option value="">כל הפלטפורמות</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="messenger">Messenger</option>
              <option value="instagram">Instagram</option>
            </select>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="flex-1 text-sm border rounded-lg px-2 py-1.5 bg-gray-50"
            >
              <option value="">כל הסטטוסים</option>
              <option value="active">פעיל</option>
              <option value="resolved">סגור</option>
              <option value="escalated">הועבר</option>
            </select>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-8 text-center text-gray-400">טוען...</div>
          ) : conversations.length === 0 ? (
            <div className="p-8 text-center text-gray-400">אין שיחות</div>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => setSelected(conv.id)}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors
                  ${selected === conv.id ? 'bg-blue-50 border-r-2 border-r-blue-500' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm text-gray-800 capitalize">
                    {conv.platform}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[conv.status] || 'bg-gray-100'}`}>
                    {conv.status === 'active' ? 'פעיל' : conv.status === 'resolved' ? 'סגור' : conv.status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className={SENTIMENT_COLORS[conv.sentiment]}>
                    {conv.sentiment === 'positive' ? '😊 חיובי' : conv.sentiment === 'negative' ? '😞 שלילי' : '😐 ניטרלי'}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageCircle size={12} />
                    {conv.total_messages}
                  </span>
                </div>
                {conv.intent && (
                  <div className="text-xs text-blue-500 mt-1">{conv.intent}</div>
                )}
                {conv.last_message_at && (
                  <div className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <Clock size={11} />
                    {new Date(conv.last_message_at).toLocaleString('he-IL')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Message view */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {selected ? (
          <>
            <div className="p-4 bg-white border-b">
              <h3 className="font-semibold text-gray-800">
                שיחה: <span className="font-mono text-sm text-gray-500">{selected}</span>
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-md px-4 py-2 rounded-2xl text-sm
                    ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}
                  >
                    <div>{msg.content}</div>
                    <div className="text-xs opacity-60 mt-1">
                      {new Date(msg.created_at).toLocaleTimeString('he-IL')}
                      {msg.ai_provider && ` · ${msg.ai_provider}`}
                      {msg.tokens_used && ` · ${msg.tokens_used} tokens`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <MessageCircle size={48} className="mx-auto mb-3 opacity-30" />
              <p>בחר שיחה לצפייה</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
