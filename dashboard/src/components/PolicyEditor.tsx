import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Save, Shield } from 'lucide-react'
import { clsx } from 'clsx'
import { api } from '../lib/api'

interface Policy {
  id: string
  action: string
  resource: string
  actor: string
  effect: 'allow' | 'deny' | 'require_approval'
  reason?: string
  priority: number
}

export default function PolicyEditor() {
  const queryClient = useQueryClient()
  const [editingPolicy, setEditingPolicy] = useState<Partial<Policy> | null>(null)

  const { data: policies = [], isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => api.get<Policy[]>('/policies').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (policy: Partial<Policy>) => api.post('/policies', policy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      setEditingPolicy(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/policies/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['policies'] }),
  })

  const effectColors = {
    allow: 'bg-green-100 text-green-800',
    deny: 'bg-red-100 text-red-800',
    require_approval: 'bg-amber-100 text-amber-800',
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Policy Rules
        </h3>
        <button
          onClick={() => setEditingPolicy({ effect: 'deny', priority: 100 })}
          className="flex items-center gap-1 px-3 py-1.5 bg-aegis-600 text-white rounded-lg text-sm hover:bg-aegis-700"
        >
          <Plus className="h-4 w-4" />
          Add Policy
        </button>
      </div>

      {editingPolicy && (
        <div className="p-4 bg-gray-50 border-b">
          <div className="grid grid-cols-2 gap-4">
            <input
              placeholder="Action (e.g., ingest, query, *)"
              className="px-3 py-2 border rounded-lg"
              value={editingPolicy.action || ''}
              onChange={(e) => setEditingPolicy({ ...editingPolicy, action: e.target.value })}
            />
            <input
              placeholder="Resource (e.g., emails, *)"
              className="px-3 py-2 border rounded-lg"
              value={editingPolicy.resource || ''}
              onChange={(e) => setEditingPolicy({ ...editingPolicy, resource: e.target.value })}
            />
            <input
              placeholder="Actor (e.g., user:*, *)"
              className="px-3 py-2 border rounded-lg"
              value={editingPolicy.actor || ''}
              onChange={(e) => setEditingPolicy({ ...editingPolicy, actor: e.target.value })}
            />
            <select
              className="px-3 py-2 border rounded-lg"
              value={editingPolicy.effect}
              onChange={(e) => setEditingPolicy({ ...editingPolicy, effect: e.target.value as Policy['effect'] })}
            >
              <option value="allow">Allow</option>
              <option value="deny">Deny</option>
              <option value="require_approval">Require Approval</option>
            </select>
            <input
              placeholder="Reason"
              className="px-3 py-2 border rounded-lg col-span-2"
              value={editingPolicy.reason || ''}
              onChange={(e) => setEditingPolicy({ ...editingPolicy, reason: e.target.value })}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => createMutation.mutate(editingPolicy)}
              className="flex items-center gap-1 px-4 py-2 bg-aegis-600 text-white rounded-lg hover:bg-aegis-700"
            >
              <Save className="h-4 w-4" />
              Save
            </button>
            <button
              onClick={() => setEditingPolicy(null)}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="divide-y">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : policies.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No policies configured
          </div>
        ) : (
          policies.map((policy) => (
            <div key={policy.id} className="p-4 flex items-center gap-4">
              <span
                className={clsx(
                  'px-2 py-1 rounded text-xs font-medium',
                  effectColors[policy.effect]
                )}
              >
                {policy.effect.toUpperCase()}
              </span>
              <div className="flex-1">
                <div className="font-mono text-sm">
                  {policy.actor} → {policy.action} → {policy.resource}
                </div>
                {policy.reason && (
                  <div className="text-xs text-gray-500">{policy.reason}</div>
                )}
              </div>
              <span className="text-xs text-gray-400">P{policy.priority}</span>
              <button
                onClick={() => deleteMutation.mutate(policy.id)}
                className="p-1 text-red-500 hover:bg-red-50 rounded"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
