import React from 'react'
import {
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const PIE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#a855f7']

export function LineMetricChart({ data, dataKey = 'value', stroke = '#3b82f6' }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey={dataKey} stroke={stroke} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function BarMetricChart({ data, dataKey = 'count', fill = '#10b981' }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis />
        <Tooltip />
        <Bar dataKey={dataKey} fill={fill} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PlatformPieChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Tooltip />
        <Pie data={data} dataKey="value" nameKey="name" outerRadius={88}>
          {data.map((entry, index) => (
            <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  )
}
