import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  Users, MessageCircle, TrendingUp, Activity,
  ShoppingBag, Star, AlertCircle
} from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

function StatCard({ title, value, subtitle, icon: Icon, color = 'blue' }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
  }
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorMap[color]}`}>
          <Icon size={24} />
        </div>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm font-medium text-gray-600">{title}</div>
      {subtitle && <div className="text-xs text-gray-400 mt-1">{subtitle}</div>}
    </div>
  )
}

export default function Dashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => axios.get('/api/v1/admin/overview').then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: topIntents } = useQuery({
    queryKey: ['top-intents'],
    queryFn: () => axios.get('/api/v1/analytics/top-intents').then(r => r.data),
  })

  const { data: sentimentData } = useQuery({
    queryKey: ['sentiment'],
    queryFn: () => axios.get('/api/v1/analytics/sentiment').then(r => r.data),
  })

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    )
  }

  const platformData = overview?.platform_breakdown
    ? Object.entries(overview.platform_breakdown).map(([name, value]) => ({ name, value }))
    : []

  const sentimentChartData = sentimentData
    ? Object.entries(sentimentData).map(([name, value]) => ({
        name: name === 'positive' ? 'חיובי' : name === 'negative' ? 'שלילי' : 'ניטרלי',
        value,
      }))
    : []

  return (
    <div className="p-8" dir="rtl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">לוח בקרה</h1>
        <p className="text-gray-500 mt-1">סקירה כללית של הפעילות</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="סה״כ משתמשים"
          value={overview?.total_users?.toLocaleString() || '0'}
          subtitle={`${overview?.new_users_today || 0} חדשים היום`}
          icon={Users}
          color="blue"
        />
        <StatCard
          title="שיחות פעילות"
          value={overview?.active_conversations?.toLocaleString() || '0'}
          subtitle={`${overview?.total_conversations || 0} סה״כ`}
          icon={MessageCircle}
          color="green"
        />
        <StatCard
          title="הודעות"
          value={overview?.total_messages?.toLocaleString() || '0'}
          subtitle="סה״כ"
          icon={Activity}
          color="yellow"
        />
        <StatCard
          title="פלטפורמות"
          value={Object.keys(overview?.platform_breakdown || {}).length}
          subtitle="פעילות"
          icon={Star}
          color="red"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Platform breakdown */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">פלטפורמות</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={platformData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
              >
                {platformData.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {platformData.map((item, index) => (
              <span key={item.name} className="flex items-center gap-1 text-xs text-gray-600">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                {item.name}: {item.value}
              </span>
            ))}
          </div>
        </div>

        {/* Sentiment */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">סנטימנט שיחות</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sentimentChartData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
              >
                {sentimentChartData.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={
                      entry.name === 'חיובי' ? '#10b981'
                        : entry.name === 'שלילי' ? '#ef4444'
                        : '#94a3b8'
                    }
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Intents */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-4">כוונות נפוצות</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={(topIntents || []).slice(0, 5)} layout="vertical">
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="intent" width={120} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Last updated */}
      <p className="text-xs text-gray-400 text-center">
        עודכן: {overview?.timestamp ? new Date(overview.timestamp).toLocaleString('he-IL') : 'לא ידוע'}
      </p>
    </div>
  )
}
