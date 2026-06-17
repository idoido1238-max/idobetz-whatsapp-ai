import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'
import { Package, RefreshCw, Search } from 'lucide-react'

export default function Products() {
  const [search, setSearch] = useState('')
  const [inStock, setInStock] = useState('')
  const queryClient = useQueryClient()

  const { data: products = [], isLoading } = useQuery({
    queryKey: ['products', search, inStock],
    queryFn: () =>
      axios.get('/api/v1/products', {
        params: {
          search: search || undefined,
          in_stock: inStock !== '' ? inStock === 'true' : undefined,
        },
      }).then(r => r.data),
  })

  const syncMutation = useMutation({
    mutationFn: () => axios.post('/api/v1/products/sync'),
    onSuccess: () => {
      toast.success('סנכרון מוצרים הופעל')
      setTimeout(() => queryClient.invalidateQueries(['products']), 5000)
    },
    onError: () => toast.error('שגיאה בסנכרון'),
  })

  return (
    <div className="p-8" dir="rtl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">מוצרים</h1>
          <p className="text-gray-500 mt-1">מוצרים מסונכרנים מהאתר</p>
        </div>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          <RefreshCw size={18} className={syncMutation.isPending ? 'animate-spin' : ''} />
          סנכרן עכשיו
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="חיפוש מוצרים..."
            className="w-full border rounded-lg px-3 py-2 pr-9 text-sm"
          />
        </div>
        <select
          value={inStock}
          onChange={e => setInStock(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">כל המוצרים</option>
          <option value="true">במלאי</option>
          <option value="false">אזל מהמלאי</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">טוען מוצרים...</div>
      ) : products.length === 0 ? (
        <div className="text-center py-12">
          <Package size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 mb-2">אין מוצרים מסונכרנים</p>
          <p className="text-sm text-gray-400">
            חבר את אתר idobetz.co.il כדי לטעון מוצרים אוטומטית
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {products.map(product => (
            <div key={product.id} className="bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100">
              {product.thumbnail_url ? (
                <img
                  src={product.thumbnail_url}
                  alt={product.name_he || product.name}
                  className="w-full h-48 object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-48 bg-gray-100 flex items-center justify-center">
                  <Package size={32} className="text-gray-300" />
                </div>
              )}
              <div className="p-4">
                <h3 className="font-medium text-gray-800 text-sm mb-1">
                  {product.name_he || product.name}
                </h3>
                {product.sku && (
                  <p className="text-xs text-gray-400 mb-2 ltr">SKU: {product.sku}</p>
                )}
                <div className="flex items-center justify-between">
                  <div>
                    {product.is_on_sale ? (
                      <div>
                        <span className="text-red-600 font-bold text-sm">₪{product.effective_price?.toFixed(2)}</span>
                        <span className="text-gray-400 text-xs line-through mr-1">₪{product.original_price?.toFixed(2)}</span>
                      </div>
                    ) : (
                      <span className="font-bold text-gray-800 text-sm">₪{product.effective_price?.toFixed(2)}</span>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    product.in_stock ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {product.in_stock ? 'במלאי' : 'אזל'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
