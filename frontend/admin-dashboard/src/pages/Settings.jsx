import React from 'react'
import { Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  return (
    <div className="p-8" dir="rtl">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">הגדרות</h1>
      <p className="text-gray-500 mb-8">תצורת המערכת</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Status */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">סטטוס חיבורים</h3>
          <div className="space-y-3">
            {[
              { name: 'OpenAI GPT-4o', status: 'active' },
              { name: 'Anthropic Claude', status: 'active' },
              { name: 'WhatsApp Business API', status: 'check' },
              { name: 'Meta Messenger API', status: 'check' },
              { name: 'Instagram API', status: 'check' },
              { name: 'Website API', status: 'check' },
              { name: 'PostgreSQL', status: 'active' },
              { name: 'Redis', status: 'active' },
            ].map(item => (
              <div key={item.name} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-sm text-gray-700">{item.name}</span>
                <span className={`flex items-center gap-1 text-xs ${
                  item.status === 'active' ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${
                    item.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  {item.status === 'active' ? 'פעיל' : 'בדוק הגדרות'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">פיצ׳רים פעילים</h3>
          <div className="space-y-3">
            {[
              { name: 'תמלול הקלטות קוליות (Whisper)', enabled: true },
              { name: 'ניתוח סנטימנט', enabled: true },
              { name: 'זיהוי כוונות', enabled: true },
              { name: 'המלצות מוצרים', enabled: true },
              { name: 'מעקב הזמנות עם כתובת מלאה', enabled: true },
              { name: 'קמפיינים אוטומטיים', enabled: true },
              { name: 'ניקוד נאמנות', enabled: true },
              { name: 'מצב פרטיות (Ollama)', enabled: false },
            ].map(feature => (
              <div key={feature.name} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-sm text-gray-700">{feature.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  feature.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {feature.enabled ? 'פעיל' : 'כבוי'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Environment note */}
        <div className="bg-blue-50 rounded-xl p-6 border border-blue-100 lg:col-span-2">
          <div className="flex items-start gap-3">
            <SettingsIcon size={20} className="text-blue-600 mt-0.5 shrink-0" />
            <div>
              <h4 className="font-semibold text-blue-800 mb-1">הגדרת משתני סביבה</h4>
              <p className="text-sm text-blue-700">
                כל ההגדרות מנוהלות דרך קובץ <code className="bg-blue-100 px-1 rounded">.env</code>.
                ראה <code className="bg-blue-100 px-1 rounded">.env.example</code> לדוגמת הגדרות מלאה.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
