import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, Users, MessageSquare, DollarSign, HelpCircle } from 'lucide-react'

const PLATFORM_COLORS = {
  whatsapp: '#25D366',
  messenger: '#0099FF',
  instagram: '#E1306C',
  unknown: '#9CA3AF',
}
const PIE_COLORS = ['#25D366', '#0099FF', '#E1306C', '#9CA3AF']

export default function Analytics() {
  const [days, setDays] = useState(7)

  const { data: overview } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => axios.get('/api/v1/admin/analytics/overview').then(r => r.data),
    refetchInterval: 60000,
  })

  const { data: metrics } = useQuery({
    queryKey: ['analytics-metrics', days],
    queryFn: () => axios.get(`/api/v1/admin/analytics/metrics?days=${days}`).then(r => r.data),
  })

  const { data: topQuestions = [] } = useQuery({
    queryKey: ['analytics-top-questions'],
    queryFn: () => axios.get('/api/v1/admin/analytics/top-questions').then(r => r.data),
  })

  const { data: messagesPerDay = [] } = useQuery({
    queryKey: ['messages-per-day', days],
    queryFn: () => axios.get(`/api/v1/analytics/messages-per-day?days=${days}`).then(r => r.data),
  })

  const { data: userGrowth = [] } = useQuery({
    queryKey: ['user-growth', days],
    queryFn: () => axios.get(`/api/v1/analytics/user-growth?days=${days}`).then(r => r.data),
  })

  const { data: responseTimes = [] } = useQuery({
    queryKey: ['response-times'],
    queryFn: () => axios.get('/api/v1/analytics/response-times').then(r => r.data),
  })

  const platformPieData = overview?.platform_breakdown
    ? Object.entries(overview.platform_breakdown).map(([name, value]) => ({ name, value }))
    : []

  const revenueData = metrics?.revenue_by_day || []
  const dailyUsersData = metrics?.daily_active_users || []

  const statCards = [
    {
      label: 'סה״כ משתמשים',
      value: overview?.total_users?.toLocaleString() ?? '—',
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'הכנסות (30 ימים)',
      value: overview?.revenue_30d != null ? `₪${overview.revenue_30d.toLocaleString()}` : '—',
      icon: DollarSign,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'הודעות היום',
      value: overview?.messages_today?.toLocaleString() ?? '—',
      icon: MessageSquare,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
    {
      label: 'משתמשים פעילים היום',
      value: overview?.active_users_today?.toLocaleString() ?? '—',
      icon: TrendingUp,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
  ]

  return (
    <div className="p-8" dir="rtl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">אנליטיקס</h1>
          <p className="text-gray-500 mt-1">סטטיסטיקות וביצועים</p>
        </div>
        <select
          value={days}
          onChange={e => setDays(Number(e.target.value))}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value={7}>7 ימים</option>
          <option value={14}>14 ימים</option>
          <option value={30}>30 ימים</option>
          <option value={90}>90 ימים</option>
        </select>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map(card => (
          <div key={card.label} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500">{card.label}</span>
              <div className={`${card.bg} p-2 rounded-lg`}>
                <card.icon size={18} className={card.color} />
              </div>
            </div>
            <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Daily Active Users - Area Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">משתמשים פעילים יומיים</h3>
          {dailyUsersData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={dailyUsersData}>
                <defs>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="users" stroke="#3b82f6" fill="url(#colorUsers)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center">
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={userGrowth.map(d => ({ date: d.date, users: d.new_users }))}>
                  <defs>
                    <linearGradient id="colorUsers2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="users" stroke="#3b82f6" fill="url(#colorUsers2)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Revenue - Line Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">הכנסות לפי יום (₪)</h3>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip formatter={(v) => [`₪${v}`, 'הכנסות']} />
                <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-400 text-sm">
              אין נתוני הכנסות עדיין
            </div>
          )}
        </div>

        {/* Messages - Bar Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">נפח הודעות ביום</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={messagesPerDay.slice(-14)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="הודעות" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Pie */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">פילוח לפי פלטפורמה</h3>
          {platformPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={platformPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {platformPieData.map((entry, idx) => (
                    <Cell key={entry.name} fill={PLATFORM_COLORS[entry.name] || PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-400 text-sm">
              אין נתונים
            </div>
          )}
        </div>
      </div>

      {/* Response Times */}
      {responseTimes.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4">זמני תגובה AI (ms)</h3>
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
                  {rt.avg_response_time_ms?.toFixed(0)}ms
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top 10 Questions */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <HelpCircle size={18} className="text-blue-600" />
          <h3 className="font-semibold text-gray-800">10 השאלות הנפוצות ביותר</h3>
        </div>
        {topQuestions.length > 0 ? (
          <div className="space-y-3">
            {topQuestions.map((q, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <span className="flex-1 text-sm text-gray-700">{q.question || q.intent}</span>
                <span className="text-sm font-semibold text-gray-500 ltr">{q.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm text-center py-4">אין נתונים עדיין</p>
        )}
      </div>
    </div>
  )
}
