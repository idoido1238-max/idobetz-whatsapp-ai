import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import {
  ShoppingBag, Search, Download, MapPin, Truck,
  ChevronDown, ChevronUp, X,
} from 'lucide-react'

const STATUS_CONFIG = {
  pending: { label: 'ממתין', color: 'bg-yellow-100 text-yellow-700' },
  confirmed: { label: 'אושר', color: 'bg-blue-100 text-blue-700' },
  processing: { label: 'בעיבוד', color: 'bg-indigo-100 text-indigo-700' },
  shipped: { label: 'נשלח', color: 'bg-cyan-100 text-cyan-700' },
  delivered: { label: 'נמסר', color: 'bg-green-100 text-green-700' },
  cancelled: { label: 'בוטל', color: 'bg-red-100 text-red-700' },
  refunded: { label: 'הוחזר', color: 'bg-gray-100 text-gray-600' },
}

function OrderRow({ order }) {
  const [expanded, setExpanded] = useState(false)
  const statusCfg = STATUS_CONFIG[order.status] || { label: order.status, color: 'bg-gray-100 text-gray-600' }
  const formattedDate = order.created_at
    ? new Date(order.created_at).toLocaleString('he-IL')
    : '—'
  const formattedDelivery = order.estimated_delivery
    ? new Date(order.estimated_delivery).toLocaleDateString('he-IL')
    : null

  return (
    <>
      <tr
        className="border-b hover:bg-gray-50 cursor-pointer transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-1">
            <span className="font-mono text-sm text-blue-600">
              {order.external_order_id || order.id?.slice(0, 8)}
            </span>
            <span className="text-gray-300">{expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
          </div>
        </td>
        <td className="px-4 py-3">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusCfg.color}`}>
            {statusCfg.label}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-700">
          {order.total_amount != null
            ? `${Number(order.total_amount).toFixed(2)} ${order.currency || '₪'}`
            : '—'}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {order.shipping_city || '—'}
        </td>
        <td className="px-4 py-3 text-sm text-gray-400">
          {formattedDate}
        </td>
        <td className="px-4 py-3 text-sm">
          {order.tracking_number ? (
            <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">
              {order.tracking_number}
            </span>
          ) : '—'}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-slate-50 border-b">
          <td colSpan={6} className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
                  <MapPin size={14} className="text-blue-500" />
                  כתובת משלוח
                </h4>
                {order.full_address ? (
                  <p className="text-gray-600 bg-white border rounded-lg px-3 py-2 text-sm leading-relaxed">
                    {order.full_address}
                  </p>
                ) : (
                  <p className="text-gray-400 text-xs">אין כתובת מלאה</p>
                )}
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-700 flex items-center gap-1.5">
                  <Truck size={14} className="text-green-500" />
                  מעקב משלוח
                </h4>
                <div className="space-y-1 text-gray-600">
                  {order.carrier && (
                    <div><span className="text-gray-400">חברת שליחויות: </span>{order.carrier}</div>
                  )}
                  {order.tracking_number && (
                    <div><span className="text-gray-400">מספר מעקב: </span>
                      <span className="font-mono">{order.tracking_number}</span>
                    </div>
                  )}
                  {formattedDelivery && (
                    <div><span className="text-gray-400">משלוח משוער: </span>{formattedDelivery}</div>
                  )}
                  {!order.carrier && !order.tracking_number && !formattedDelivery && (
                    <p className="text-gray-400 text-xs">אין מידע מעקב</p>
                  )}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function Orders() {
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['orders', statusFilter],
    queryFn: () =>
      axios.get('/api/v1/orders', {
        params: { status: statusFilter || undefined, limit: 100 },
      }).then(r => r.data),
    refetchInterval: 30000,
  })

  const filtered = orders.filter(o => {
    if (!search) return true
    const id = (o.external_order_id || o.id || '').toLowerCase()
    const city = (o.shipping_city || '').toLowerCase()
    return id.includes(search.toLowerCase()) || city.includes(search.toLowerCase())
  })

  const exportOrders = () => {
    const csvField = (val) => {
      const str = String(val ?? '')
      return str.includes(',') || str.includes('"') || str.includes('\n')
        ? `"${str.replace(/"/g, '""')}"`
        : str
    }
    const header = 'מספר הזמנה,סטטוס,סכום,עיר,כתובת,מספר מעקב,תאריך'
    const rows = filtered.map(o => [
      csvField(o.external_order_id || o.id?.slice(0, 8)),
      csvField(STATUS_CONFIG[o.status]?.label || o.status),
      csvField(o.total_amount != null ? `${Number(o.total_amount).toFixed(2)} ${o.currency || '₪'}` : ''),
      csvField(o.shipping_city || ''),
      csvField(o.full_address || ''),
      csvField(o.tracking_number || ''),
      csvField(o.created_at ? new Date(o.created_at).toLocaleString('he-IL') : ''),
    ].join(','))
    const csv = [header, ...rows].join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `orders-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('הזמנות יוצאו לקובץ CSV')
  }

  const statusCounts = orders.reduce((acc, o) => {
    acc[o.status] = (acc[o.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="p-8" dir="rtl">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <ShoppingBag className="text-blue-600" size={28} />
            ניהול הזמנות
          </h1>
          <p className="text-gray-500 mt-1">
            {isLoading ? 'טוען...' : `${orders.length} הזמנות סה״כ`}
          </p>
        </div>
        <button
          onClick={exportOrders}
          disabled={filtered.length === 0}
          className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700
            px-4 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm font-medium shadow-sm"
        >
          <Download size={16} />
          ייצוא CSV
        </button>
      </div>

      {/* Status summary cards */}
      {!isLoading && orders.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => setStatusFilter(statusFilter === key ? '' : key)}
              className={`rounded-xl p-3 text-center border transition-all shadow-sm
                ${statusFilter === key
                  ? 'ring-2 ring-blue-500 border-blue-300 bg-blue-50'
                  : 'bg-white border-gray-100 hover:border-gray-200'
                }`}
            >
              <div className={`text-xl font-bold ${statusFilter === key ? 'text-blue-700' : 'text-gray-800'}`}>
                {statusCounts[key] || 0}
              </div>
              <div className={`text-xs mt-0.5 ${cfg.color} rounded-full px-1.5 py-0.5 inline-block`}>
                {cfg.label}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Search + filter bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-4 p-4 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 flex-1 min-w-48 bg-gray-50 border rounded-lg px-3 py-2">
          <Search size={15} className="text-gray-400 shrink-0" />
          <input
            type="text"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && setSearch(searchInput)}
            placeholder="חפש לפי מספר הזמנה או עיר..."
            className="bg-transparent text-sm flex-1 focus:outline-none"
          />
          {searchInput && (
            <button onClick={() => { setSearchInput(''); setSearch('') }}>
              <X size={14} className="text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
        <button
          onClick={() => setSearch(searchInput)}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          חפש
        </button>
        {statusFilter && (
          <button
            onClick={() => setStatusFilter('')}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 border rounded-lg px-3 py-2 bg-gray-50"
          >
            <X size={14} />
            נקה סינון
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3" />
            טוען הזמנות...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <ShoppingBag size={48} className="mx-auto text-gray-200 mb-3" />
            <p className="text-gray-400">
              {orders.length === 0 ? 'אין הזמנות במערכת' : 'לא נמצאו תוצאות לחיפוש'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">מספר הזמנה</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">סטטוס</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">סכום</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">עיר</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">תאריך</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">מספר מעקב</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(order => (
                  <OrderRow key={order.id} order={order} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {filtered.length > 0 && (
        <p className="text-xs text-gray-400 mt-3 text-center">
          מציג {filtered.length} מתוך {orders.length} הזמנות • לחץ על שורה לפרטים מלאים
        </p>
      )}
    </div>
  )
}
