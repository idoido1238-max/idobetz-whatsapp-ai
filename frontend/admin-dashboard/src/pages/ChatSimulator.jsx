import React, { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import {
  Send, RotateCcw, Trash2, Download, Save, Edit3, X,
  Bot, User, Loader2, ChevronDown, ChevronUp, Zap,
  MessageSquare, Activity, Tag, Globe,
} from 'lucide-react'

const PLATFORMS = [
  { value: 'whatsapp', label: 'WhatsApp', color: 'text-green-600' },
  { value: 'messenger', label: 'Messenger', color: 'text-blue-600' },
  { value: 'instagram', label: 'Instagram', color: 'text-pink-600' },
  { value: 'website', label: 'אתר אינטרנט', color: 'text-purple-600' },
]

const AI_PROVIDERS = [
  { value: '', label: 'ברירת מחדל' },
  { value: 'openai', label: 'OpenAI GPT-4o' },
  { value: 'claude', label: 'Anthropic Claude' },
  { value: 'ollama', label: 'Ollama (Local)' },
]

const USER_PROFILES = [
  { value: 'standard', label: 'לקוח רגיל' },
  { value: 'vip', label: 'לקוח VIP' },
  { value: 'new', label: 'לקוח חדש' },
  { value: 'returning', label: 'לקוח חוזר' },
]

const SENTIMENT_CONFIG = {
  positive: { label: 'חיובי', color: 'text-green-600', bg: 'bg-green-50', emoji: '😊' },
  negative: { label: 'שלילי', color: 'text-red-600', bg: 'bg-red-50', emoji: '😞' },
  neutral: { label: 'ניטרלי', color: 'text-gray-600', bg: 'bg-gray-50', emoji: '😐' },
}

const INTENT_LABELS = {
  order_status: 'סטטוס הזמנה',
  order_cancel: 'ביטול הזמנה',
  product_inquiry: 'שאלה על מוצר',
  product_recommendation: 'המלצת מוצר',
  price_inquiry: 'שאלת מחיר',
  stock_inquiry: 'שאלת מלאי',
  cart_help: 'עזרה בעגלה',
  payment_help: 'עזרה בתשלום',
  shipping_info: 'מידע משלוח',
  return_refund: 'החזרה/זיכוי',
  complaint: 'תלונה',
  compliment: 'מחמאה',
  support_request: 'בקשת תמיכה',
  human_agent_request: 'נציג אנושי',
  greeting: 'ברכה',
  farewell: 'פרידה',
  faq: 'שאלות נפוצות',
  general: 'כללי',
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="flex items-center gap-2 bg-gray-100 rounded-2xl px-4 py-3">
        <Bot size={14} className="text-blue-500" />
        <div className="flex gap-1">
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg, onEdit }) {
  const [showDetails, setShowDetails] = useState(false)
  const isUser = msg.role === 'user'

  const sentimentCfg = SENTIMENT_CONFIG[msg.analysis?.sentiment] || null

  return (
    <div className={`flex mb-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xl ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {/* Avatar row */}
        <div className={`flex items-center gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0
            ${isUser ? 'bg-blue-100' : 'bg-slate-200'}`}>
            {isUser
              ? <User size={14} className="text-blue-600" />
              : <Bot size={14} className="text-slate-600" />
            }
          </div>
          <span className="text-xs text-gray-400">
            {isUser ? 'אתה' : `בוט${msg.provider ? ` (${msg.provider})` : ''}`}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={`relative px-4 py-2.5 text-sm shadow-sm
            ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}
        >
          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

          <div className={`flex items-center justify-between gap-3 mt-1.5 text-xs
            ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
            <span>{msg.time}</span>
            {msg.responseTimeMs && (
              <span className="flex items-center gap-0.5">
                <Zap size={10} />
                {msg.responseTimeMs}ms
              </span>
            )}
            {msg.tokensUsed > 0 && (
              <span>{msg.tokensUsed} tokens</span>
            )}
          </div>
        </div>

        {/* Analysis badges (bot messages only) */}
        {!isUser && msg.analysis && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {msg.analysis.intent && (
              <span className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 rounded-full px-2.5 py-0.5 border border-blue-100">
                <Tag size={10} />
                {INTENT_LABELS[msg.analysis.intent] || msg.analysis.intent}
                {msg.analysis.intentConfidence && (
                  <span className="text-blue-400 text-[10px]">
                    {Math.round(msg.analysis.intentConfidence * 100)}%
                  </span>
                )}
              </span>
            )}
            {sentimentCfg && (
              <span className={`inline-flex items-center gap-1 text-xs rounded-full px-2.5 py-0.5 border
                ${sentimentCfg.color} ${sentimentCfg.bg} border-current border-opacity-20`}>
                {sentimentCfg.emoji} {sentimentCfg.label}
              </span>
            )}
            {msg.analysis.emotions?.slice(0, 2).map(e => (
              <span key={e} className="text-xs bg-gray-50 text-gray-500 rounded-full px-2 py-0.5 border border-gray-200">
                {e}
              </span>
            ))}

            {/* Expand details button */}
            <button
              onClick={() => setShowDetails(v => !v)}
              className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-0.5 ml-1"
            >
              {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              {showDetails ? 'פחות' : 'פרטים'}
            </button>
          </div>
        )}

        {/* Expanded analysis */}
        {!isUser && msg.analysis && showDetails && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-gray-600 space-y-1.5 w-full max-w-xs">
            {msg.analysis.entities && Object.entries(msg.analysis.entities).some(([, v]) => Array.isArray(v) && v.length > 0) && (
              <div>
                <span className="font-medium text-gray-700 block mb-1">ישויות שזוהו:</span>
                {Object.entries(msg.analysis.entities)
                  .filter(([, v]) => Array.isArray(v) && v.length > 0)
                  .map(([key, values]) => (
                    <div key={key} className="flex gap-1 flex-wrap">
                      <span className="text-gray-400">{key}:</span>
                      {values.map((v, i) => (
                        <span key={i} className="bg-white border rounded px-1">{v}</span>
                      ))}
                    </div>
                  ))}
              </div>
            )}
            {msg.analysis.provider && (
              <div><span className="font-medium">ספק AI:</span> {msg.analysis.provider}</div>
            )}
          </div>
        )}

        {/* Edit button for user messages */}
        {isUser && onEdit && (
          <button
            onClick={() => onEdit(msg.content)}
            className="text-xs text-gray-400 hover:text-blue-500 flex items-center gap-0.5 self-end"
          >
            <Edit3 size={11} />
            ערוך ושלח
          </button>
        )}
      </div>
    </div>
  )
}

export default function ChatSimulator() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [platform, setPlatform] = useState('whatsapp')
  const [aiProvider, setAiProvider] = useState('')
  const [userProfile, setUserProfile] = useState('standard')
  const [saveName, setSaveName] = useState('')
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading, scrollToBottom])

  const buildHistory = useCallback(() => {
    return messages.map(m => ({ role: m.role, content: m.content }))
  }, [messages])

  const sendMessage = useCallback(async (text) => {
    const trimmed = (text || input).trim()
    if (!trimmed || loading) return

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: trimmed,
      time: new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const { data } = await axios.post('/api/v1/admin/chat/simulate', {
        message: trimmed,
        platform,
        ai_provider: aiProvider || undefined,
        history: buildHistory(),
        user_profile: userProfile,
      })

      const botMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        provider: data.ai_provider,
        tokensUsed: data.tokens_used,
        responseTimeMs: data.response_time_ms,
        time: new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }),
        analysis: {
          intent: data.intent,
          intentConfidence: data.intent_confidence,
          entities: data.entities,
          sentiment: data.sentiment,
          sentimentScore: data.sentiment_score,
          emotions: data.sentiment_emotions,
          provider: data.ai_provider,
        },
      }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'שגיאה בשליחת ההודעה'
      toast.error(errorMsg)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `⚠️ שגיאה: ${errorMsg}`,
        time: new Date().toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }),
        analysis: null,
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, loading, platform, aiProvider, userProfile, buildHistory])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }, [sendMessage])

  const handleEditAndResend = useCallback((text) => {
    setInput(text)
    inputRef.current?.focus()
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    toast.success('שיחה נוקתה')
  }, [])

  const exportChat = useCallback(() => {
    const lines = messages.map(m => {
      const role = m.role === 'user' ? 'אתה' : 'בוט'
      return `[${m.time}] ${role}: ${m.content}`
    })
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('שיחה יוצאה בהצלחה')
  }, [messages])

  const saveChat = useCallback(() => {
    if (!saveName.trim()) {
      toast.error('אנא הזן שם לשיחה')
      return
    }
    const saves = JSON.parse(localStorage.getItem('saved_chats') || '[]')
    saves.push({
      name: saveName.trim(),
      date: new Date().toISOString(),
      messages,
      platform,
    })
    localStorage.setItem('saved_chats', JSON.stringify(saves))
    toast.success(`שיחה "${saveName}" נשמרה`)
    setSaveName('')
    setShowSaveDialog(false)
  }, [saveName, messages, platform])

  const retryLast = useCallback(() => {
    const lastUser = [...messages].reverse().find(m => m.role === 'user')
    if (lastUser) {
      setMessages(prev => {
        const idx = prev.findIndex(m => m.id === lastUser.id)
        return idx >= 0 ? prev.slice(0, idx + 1) : prev
      })
      sendMessage(lastUser.content)
    }
  }, [messages, sendMessage])

  const currentPlatform = PLATFORMS.find(p => p.value === platform)

  return (
    <div className="flex flex-col h-screen" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <MessageSquare size={22} className="text-blue-600" />
            סימולטור צ׳אט
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">בדוק את הבוט ושלח תיקונים בזמן אמת</p>
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-3 flex-wrap justify-end">
          {/* Platform */}
          <div className="flex items-center gap-1.5">
            <Globe size={15} className="text-gray-400" />
            <select
              value={platform}
              onChange={e => setPlatform(e.target.value)}
              className="text-sm border rounded-lg px-2 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PLATFORMS.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          {/* AI Provider */}
          <div className="flex items-center gap-1.5">
            <Bot size={15} className="text-gray-400" />
            <select
              value={aiProvider}
              onChange={e => setAiProvider(e.target.value)}
              className="text-sm border rounded-lg px-2 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {AI_PROVIDERS.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          {/* User Profile */}
          <div className="flex items-center gap-1.5">
            <User size={15} className="text-gray-400" />
            <select
              value={userProfile}
              onChange={e => setUserProfile(e.target.value)}
              className="text-sm border rounded-lg px-2 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {USER_PROFILES.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={retryLast}
              disabled={!messages.some(m => m.role === 'user') || loading}
              title="נסה שוב"
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg disabled:opacity-40 transition-colors"
            >
              <RotateCcw size={16} />
            </button>
            <button
              onClick={exportChat}
              disabled={messages.length === 0}
              title="ייצא שיחה"
              className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg disabled:opacity-40 transition-colors"
            >
              <Download size={16} />
            </button>
            <button
              onClick={() => setShowSaveDialog(v => !v)}
              disabled={messages.length === 0}
              title="שמור שיחה"
              className="p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg disabled:opacity-40 transition-colors"
            >
              <Save size={16} />
            </button>
            <button
              onClick={clearChat}
              disabled={messages.length === 0}
              title="נקה שיחה"
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-40 transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Save dialog */}
      {showSaveDialog && (
        <div className="bg-purple-50 border-b border-purple-100 px-6 py-3 flex items-center gap-3">
          <Save size={16} className="text-purple-600 shrink-0" />
          <input
            type="text"
            value={saveName}
            onChange={e => setSaveName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && saveChat()}
            placeholder="שם לשיחה..."
            className="flex-1 text-sm border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-400 max-w-xs"
            autoFocus
          />
          <button
            onClick={saveChat}
            className="text-sm bg-purple-600 text-white px-3 py-1.5 rounded-lg hover:bg-purple-700"
          >
            שמור
          </button>
          <button
            onClick={() => { setShowSaveDialog(false); setSaveName('') }}
            className="p-1.5 text-gray-400 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Status bar */}
      <div className="bg-slate-50 border-b px-6 py-1.5 flex items-center gap-4 text-xs text-gray-500 shrink-0">
        <span className={`flex items-center gap-1 ${currentPlatform?.color}`}>
          <Activity size={11} />
          {currentPlatform?.label}
        </span>
        <span>{messages.length} הודעות</span>
        {loading && (
          <span className="flex items-center gap-1 text-blue-500">
            <Loader2 size={11} className="animate-spin" />
            הבוט כותב...
          </span>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 gap-3">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center">
              <Bot size={32} className="text-blue-300" />
            </div>
            <div>
              <p className="font-medium text-gray-500 mb-1">התחל שיחה עם הבוט</p>
              <p className="text-sm">שלח הודעה בעברית או באנגלית ובדוק את התגובה</p>
            </div>
            {/* Quick start suggestions */}
            <div className="flex flex-wrap gap-2 justify-center mt-2">
              {[
                'שלום, מה שעות הפעילות?',
                'איפה ההזמנה שלי?',
                'יש לי בעיה עם המוצר',
                'כמה עולה המשלוח?',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  className="text-xs bg-white border border-blue-200 text-blue-600 rounded-full px-3 py-1.5 hover:bg-blue-50 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(msg => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onEdit={msg.role === 'user' ? handleEditAndResend : null}
              />
            ))}
            {loading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <div className="bg-white border-t px-4 py-3 shrink-0">
        <div className="flex items-end gap-2">
          <div className="flex-1 flex items-end bg-gray-50 border rounded-2xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="הקלד הודעה... (Enter לשליחה, Shift+Enter לשורה חדשה)"
              rows={1}
              className="flex-1 bg-transparent px-4 py-3 text-sm resize-none focus:outline-none max-h-36"
              style={{ minHeight: '44px' }}
            />
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className="shrink-0 w-10 h-10 flex items-center justify-center bg-blue-600 text-white
              rounded-full hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {loading
              ? <Loader2 size={18} className="animate-spin" />
              : <Send size={18} />
            }
          </button>
        </div>
        <p className="text-xs text-gray-300 mt-1.5 text-center">
          Enter לשליחה • Shift+Enter לשורה חדשה • לחץ על הודעה לעריכה
        </p>
      </div>
    </div>
  )
}
