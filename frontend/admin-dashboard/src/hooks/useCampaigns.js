import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

export function useCampaigns(filters = {}) {
  return useQuery({
    queryKey: ['admin-campaigns', filters],
    queryFn: () => axios.get('/api/v1/admin/campaigns', { params: filters }).then(r => r.data),
  })
}

export function useCampaignActions() {
  const queryClient = useQueryClient()

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-campaigns'] })

  const createCampaign = useMutation({
    mutationFn: payload => axios.post('/api/v1/admin/campaigns', payload),
    onSuccess: () => {
      toast.success('קמפיין נוצר בהצלחה')
      invalidate()
    },
    onError: () => toast.error('שגיאה ביצירת קמפיין'),
  })

  const updateCampaign = useMutation({
    mutationFn: ({ id, payload }) => axios.put(`/api/v1/admin/campaigns/${id}`, payload),
    onSuccess: () => {
      toast.success('קמפיין עודכן')
      invalidate()
    },
    onError: () => toast.error('שגיאה בעדכון קמפיין'),
  })

  const deleteCampaign = useMutation({
    mutationFn: id => axios.delete(`/api/v1/admin/campaigns/${id}`),
    onSuccess: () => {
      toast.success('קמפיין נמחק')
      invalidate()
    },
    onError: () => toast.error('שגיאה במחיקת קמפיין'),
  })

  return {
    createCampaign,
    updateCampaign,
    deleteCampaign,
  }
}
