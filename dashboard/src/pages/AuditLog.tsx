import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { FileText, Filter } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'

interface AuditEntry {
  id: number
  timestamp: string
  actor: string
  action: string
  resource: string
  outcome: string
}

export default function AuditLog() {
  const [filter, setFilter] = useState({ actor: '', action: '' })

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['audit', filter],
    queryFn: () => api.get<AuditEntry[]>('/audit', { params: filter }).then((r) => r.data),
  })

  const outcomeColors: Record<string, string> = {
    allowed: 'bg-green-100 text-green-800',
    denied: 'bg-red-100 text-red-800',
    error: 'bg-amber-100 text-amber-800',
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Audit Log</h1>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <input
            placeholder="Filter by actor..."
            className="px-3 py-1.5 border rounded-lg text-sm"
            value={filter.actor}
            onChange={(e) => setFilter({ ...filter, actor: e.target.value })}
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Time</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actor</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Action</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Resource</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  <FileText className="h-8 w-8 mx-auto mb-2" />
                  No audit entries
                </td>
              </tr>
            ) : (
              logs.map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {format(new Date(entry.timestamp), 'MMM d, HH:mm:ss')}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono">{entry.actor}</td>
                  <td className="px-4 py-3 text-sm">{entry.action}</td>
                  <td className="px-4 py-3 text-sm font-mono">{entry.resource}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        outcomeColors[entry.outcome] || 'bg-gray-100'
                      }`}
                    >
                      {entry.outcome}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
