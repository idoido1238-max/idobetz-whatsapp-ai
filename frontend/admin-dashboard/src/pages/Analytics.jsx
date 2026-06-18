import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { BarMetricChart, LineMetricChart, PlatformPieChart } from '../components/ChartComponents.jsx'

function MetricCard({ title, value, suffix = '' }) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
      <div className="text-sm text-gray-500 dark:text-gray-400">{title}</div>
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}{suffix}</div>
    </div>
  )
}

export default function Analytics() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['admin-analytics-overview'],
    queryFn: () => axios.get('/api/v1/admin/analytics/overview').then(r => r.data),
  })

  const { data: metrics, isLoading: loadingMetrics } = useQuery({
    queryKey: ['admin-analytics-metrics'],
    queryFn: () => axios.get('/api/v1/admin/analytics/metrics').then(r => r.data),
  })

  const { data: topQuestions = [] } = useQuery({
    queryKey: ['admin-top-questions'],
    queryFn: () => axios.get('/api/v1/admin/analytics/top-questions').then(r => r.data),
  })

  const loading = loadingOverview || loadingMetrics

  return (
    <div className="p-4 md:p-8" dir="rtl">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">Analytics</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">מדדי שימוש, הכנסות וביצועים</p>

      {loading ? (
        <div className="py-10 text-center text-gray-400">טוען נתונים...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <MetricCard title="Response time avg" value={Math.round(overview?.avg_response_time_ms || 0)} suffix="ms" />
            <MetricCard title="User satisfaction" value={Math.round(overview?.user_satisfaction_score || 0)} suffix="/100" />
            <MetricCard title="Conversion rate" value={overview?.conversion_rate || 0} suffix="%" />
            <MetricCard title="Average order value" value={`₪${(overview?.average_order_value || 0).toFixed(2)}`} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3 dark:text-gray-100">Daily Active Users (7 days)</h3>
              <LineMetricChart data={overview?.daily_active_users || []} dataKey="count" />
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3 dark:text-gray-100">Revenue chart</h3>
              <LineMetricChart data={metrics?.revenue || []} dataKey="value" stroke="#10b981" />
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3 dark:text-gray-100">Message volume</h3>
              <BarMetricChart data={metrics?.message_volume || []} dataKey="count" fill="#3b82f6" />
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3 dark:text-gray-100">Platform breakdown</h3>
              <PlatformPieChart data={metrics?.platform_breakdown || []} />
              <div className="text-xs text-gray-500 mt-2">WhatsApp / Messenger / Instagram</div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-100 dark:border-slate-700 p-4">
            <h3 className="font-semibold mb-3 dark:text-gray-100">Top 10 questions asked</h3>
            <div className="space-y-2 text-sm">
              {topQuestions.map((item, idx) => (
                <div key={`${item.question}-${idx}`} className="flex justify-between gap-3 border-b border-gray-100 dark:border-slate-700 pb-2">
                  <span className="text-gray-700 dark:text-gray-200 truncate">{item.question}</span>
                  <span className="text-gray-500 dark:text-gray-400">{item.count}</span>
                </div>
              ))}
              {topQuestions.length === 0 && <div className="text-gray-400">אין נתונים</div>}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
