import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

export default function Analytics() {
  const { data: messagesPerDay = [] } = useQuery({
    queryKey: ['messages-per-day'],
    queryFn: () => axios.get('/api/v1/analytics/messages-per-day').then(r => r.data),
  })

  const { data: responseTimes = [] } = useQuery({
    queryKey: ['response-times'],
    queryFn: () => axios.get('/api/v1/analytics/response-times').then(r => r.data),
  })

  const { data: satisfaction } = useQuery({
    queryKey: ['satisfaction'],
    queryFn: () => axios.get('/api/v1/analytics/satisfaction-scores').then(r => r.data),
  })

  const { data: userGrowth = [] } = useQuery({
    queryKey: ['user-growth'],
    queryFn: () => axios.get('/api/v1/analytics/user-growth').then(r => r.data),
  })

  return (
    <div className="p-8" dir="rtl">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">אנליטיקס</h1>
      <p className="text-gray-500 mb-8">סטטיסטיקות וביצועים</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Messages per day */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">הודעות ביום (30 ימים)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={messagesPerDay}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* User growth */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">גידול משתמשים (30 ימים)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={userGrowth}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="new_users" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Response times */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">זמני תגובה AI (ms)</h3>
          {responseTimes.length === 0 ? (
            <p className="text-gray-400 text-center py-8">אין נתונים</p>
          ) : (
            <div className="space-y-3">
              {responseTimes.map(rt => (
                <div key={rt.provider} className="flex items-center gap-3">
                  <span className="w-24 text-sm font-medium text-gray-700 capitalize">{rt.provider}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      className="bg-blue-500 h-3 rounded-full"
                      style={{ width: `${Math.min((rt.avg_response_time_ms / 5000) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 w-20 text-left ltr">
                    {rt.avg_response_time_ms.toFixed(0)}ms
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Satisfaction */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">שביעות רצון לקוחות</h3>
          {satisfaction ? (
            <div className="text-center py-4">
              <div className="text-6xl font-bold text-blue-600 mb-2">
                {satisfaction.average_score.toFixed(1)}
              </div>
              <div className="text-gray-500">מתוך 5</div>
              <div className="text-sm text-gray-400 mt-2">
                {satisfaction.total_rated} שיחות מדורגות ב-{satisfaction.period_days} ימים
              </div>
              {/* Star display */}
              <div className="flex justify-center gap-1 mt-3">
                {[1, 2, 3, 4, 5].map(star => (
                  <span
                    key={star}
                    className={`text-2xl ${star <= Math.round(satisfaction.average_score) ? 'text-yellow-400' : 'text-gray-200'}`}
                  >
                    ★
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">אין נתונים</p>
          )}
        </div>
      </div>
    </div>
  )
}
