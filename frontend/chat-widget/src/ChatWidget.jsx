import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const API_URL = window.IDOBETZ_API_URL || 'http://localhost:8000'

const styles = `
  .idobetz-widget * { box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
  .idobetz-widget { position: fixed; bottom: 24px; left: 24px; z-index: 9999; direction: rtl; }
  .idobetz-toggle {
    width: 60px; height: 60px; border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border: none; cursor: pointer; box-shadow: 0 4px 20px rgba(37,99,235,0.4);
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.2s; font-size: 28px;
  }
  .idobetz-toggle:hover { transform: scale(1.1); }
  .idobetz-window {
    position: absolute; bottom: 72px; left: 0;
    width: 360px; background: white; border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    display: flex; flex-direction: column; overflow: hidden;
    max-height: 520px;
    animation: slideUp 0.3s ease;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .idobetz-header {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    padding: 16px; color: white; display: flex; align-items: center; gap: 12px;
  }
  .idobetz-header-text { margin-right: 12px; }
  .idobetz-header h3 { margin: 0; font-size: 16px; font-weight: 600; }
  .idobetz-header p { margin: 2px 0 0; font-size: 12px; opacity: 0.8; }
  .idobetz-messages {
    flex: 1; overflow-y: auto; padding: 16px;
    display: flex; flex-direction: column; gap: 8px;
    background: #f8fafc;
  }
  .idobetz-msg { max-width: 80%; padding: 10px 14px; border-radius: 16px; font-size: 14px; line-height: 1.5; }
  .idobetz-msg.user { align-self: flex-end; background: #2563eb; color: white; border-radius: 16px 16px 4px 16px; }
  .idobetz-msg.assistant { align-self: flex-start; background: white; color: #1e293b; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-radius: 16px 16px 16px 4px; }
  .idobetz-msg.typing { background: white; }
  .typing-dots span { animation: blink 1.4s infinite; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #94a3b8; margin: 0 2px; }
  .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
  .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes blink { 0%, 80%, 100% { transform: scale(1); opacity: 0.3; } 40% { transform: scale(1.2); opacity: 1; } }
  .idobetz-input-area { padding: 12px 16px; background: white; border-top: 1px solid #e2e8f0; display: flex; gap: 8px; }
  .idobetz-input {
    flex: 1; border: 1px solid #e2e8f0; border-radius: 24px;
    padding: 10px 16px; font-size: 14px; outline: none; background: #f8fafc;
    direction: rtl;
  }
  .idobetz-input:focus { border-color: #2563eb; background: white; }
  .idobetz-send {
    width: 40px; height: 40px; border-radius: 50%;
    background: #2563eb; border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; transition: background 0.2s;
  }
  .idobetz-send:hover { background: #1d4ed8; }
  .idobetz-send:disabled { background: #94a3b8; cursor: not-allowed; }
  .idobetz-collect { padding: 16px; background: white; border-top: 1px solid #e2e8f0; }
  .idobetz-collect input {
    width: 100%; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; margin-bottom: 8px; direction: rtl;
  }
  .idobetz-collect button {
    width: 100%; background: #2563eb; color: white;
    border: none; border-radius: 8px; padding: 10px;
    font-size: 14px; font-weight: 500; cursor: pointer;
  }
  .idobetz-close { margin-right: auto; background: none; border: none; color: rgba(255,255,255,0.7); cursor: pointer; font-size: 20px; padding: 0; }
  .idobetz-close:hover { color: white; }
`

function TypingIndicator() {
  return (
    <div className="idobetz-msg assistant typing">
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  )
}

export default function ChatWidget({
  apiUrl = API_URL,
  botName = 'Idobetz AI',
  welcomeMessage = 'שלום! 👋 איך אוכל לעזור לך היום?',
  primaryColor = '#2563eb',
  collectEmail = false,
  sessionId = null,
}) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [userInfo, setUserInfo] = useState({ name: '', email: '' })
  const [infoCollected, setInfoCollected] = useState(!collectEmail)
  const messagesEndRef = useRef(null)
  const widgetSessionId = useRef(sessionId || `web_${Date.now()}_${crypto.randomUUID().replace(/-/g, '').slice(0, 9)}`)

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{ role: 'assistant', content: welcomeMessage }])
    }
  }, [open])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await axios.post(`${apiUrl}/api/v1/webhooks/website`, {
        session_id: widgetSessionId.current,
        message: userMessage,
        user_info: infoCollected ? userInfo : null,
      })
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.reply }])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'מצטער, אירעה שגיאה. אנא נסה שוב.' }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleCollect = () => {
    if (!userInfo.name.trim()) return
    setInfoCollected(true)
    setMessages([{ role: 'assistant', content: `שלום ${userInfo.name}! 👋 ${welcomeMessage}` }])
  }

  return (
    <>
      <style>{styles}</style>
      <div className="idobetz-widget">
        {open && (
          <div className="idobetz-window">
            {/* Header */}
            <div className="idobetz-header">
              <span style={{ fontSize: 28 }}>🤖</span>
              <div className="idobetz-header-text">
                <h3>{botName}</h3>
                <p>⚡ תגובה מיידית</p>
              </div>
              <button className="idobetz-close" onClick={() => setOpen(false)}>✕</button>
            </div>

            {/* Messages */}
            {infoCollected ? (
              <>
                <div className="idobetz-messages">
                  {messages.map((msg, i) => (
                    <div key={i} className={`idobetz-msg ${msg.role}`}>
                      {msg.content}
                    </div>
                  ))}
                  {loading && <TypingIndicator />}
                  <div ref={messagesEndRef} />
                </div>
                <div className="idobetz-input-area">
                  <input
                    className="idobetz-input"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="כתוב הודעה..."
                    disabled={loading}
                  />
                  <button
                    className="idobetz-send"
                    onClick={sendMessage}
                    disabled={!input.trim() || loading}
                  >
                    ➤
                  </button>
                </div>
              </>
            ) : (
              <div className="idobetz-collect">
                <p style={{ fontSize: 14, color: '#475569', marginBottom: 12 }}>
                  {welcomeMessage}
                </p>
                <input
                  placeholder="שם מלא *"
                  value={userInfo.name}
                  onChange={e => setUserInfo(p => ({ ...p, name: e.target.value }))}
                />
                {collectEmail && (
                  <input
                    type="email"
                    placeholder="אימייל (אופציונלי)"
                    value={userInfo.email}
                    onChange={e => setUserInfo(p => ({ ...p, email: e.target.value }))}
                  />
                )}
                <button onClick={handleCollect} disabled={!userInfo.name.trim()}>
                  התחל שיחה 💬
                </button>
              </div>
            )}
          </div>
        )}

        {/* Toggle button */}
        <button className="idobetz-toggle" onClick={() => setOpen(!open)}>
          {open ? '✕' : '💬'}
        </button>
      </div>
    </>
  )
}
