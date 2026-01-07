import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Play, ChevronRight, Search } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'

interface Run {
  run_id: string
  created_at: string
  completed_at: string | null
  source: string
  event_count: number
}

export default function Runs() {
  const [search, setSearch] = useState('')

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: () => api.get<Run[]>('/runs').then((r) => r.data),
  })

  const filteredRuns = runs.filter(
    (run) =>
      run.run_id.includes(search) ||
      run.source?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Runs</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search runs..."
            className="pl-10 pr-4 py-2 border rounded-lg"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Run ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Source</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Created</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Events</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : filteredRuns.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  No runs found
                </td>
              </tr>
            ) : (
              filteredRuns.map((run) => (
                <tr key={run.run_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Play className="h-4 w-4 text-aegis-500" />
                      <span className="font-mono text-sm">{run.run_id}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">{run.source || '—'}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {format(new Date(run.created_at), 'MMM d, HH:mm')}
                  </td>
                  <td className="px-4 py-3 text-sm">{run.event_count}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        run.completed_at
                          ? 'bg-green-100 text-green-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {run.completed_at ? 'Completed' : 'Running'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/runs/${run.run_id}`}
                      className="text-aegis-600 hover:text-aegis-700"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Link>
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
