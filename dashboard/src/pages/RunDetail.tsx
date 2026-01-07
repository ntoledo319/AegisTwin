import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Play, RefreshCw } from 'lucide-react'
import EventTimeline from '../components/EventTimeline'
import { api } from '../lib/api'

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()

  const { data: run, isLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.get(`/runs/${runId}`).then((r) => r.data),
    enabled: !!runId,
  })

  const { data: trace } = useQuery({
    queryKey: ['trace', runId],
    queryFn: () => api.get(`/runs/${runId}/trace`).then((r) => r.data),
    enabled: !!runId,
  })

  if (isLoading) {
    return <div className="p-6">Loading...</div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/runs" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Play className="h-6 w-6 text-aegis-500" />
            Run {runId}
          </h1>
        </div>
        <button className="ml-auto flex items-center gap-2 px-4 py-2 bg-aegis-600 text-white rounded-lg hover:bg-aegis-700">
          <RefreshCw className="h-4 w-4" />
          Replay
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <EventTimeline runId={runId} />
        </div>
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold mb-3">Run Info</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Source</dt>
                <dd>{run?.source || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Events</dt>
                <dd>{trace?.length || 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd>{run?.completed_at ? 'Completed' : 'Running'}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
