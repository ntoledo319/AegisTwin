import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'
import { api } from '../lib/api'

interface HealthStatus {
  status: string
  version: string
  uptime_seconds: number
  components: {
    event_bus: string
    policy_engine: string
    memory_store: string
    graph_manager: string
  }
}

export default function SystemHealth() {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health').then((r) => r.data),
    refetchInterval: 10000,
  })

  const statusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-amber-500" />
      default:
        return <XCircle className="h-5 w-5 text-red-500" />
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${days}d ${hours}h ${mins}m`
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse flex items-center gap-4">
          <div className="h-10 w-10 bg-gray-200 rounded-full" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/4" />
            <div className="h-3 bg-gray-200 rounded w-1/2" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <XCircle className="h-8 w-8 text-red-500" />
          <div>
            <h3 className="font-semibold text-red-800">System Unreachable</h3>
            <p className="text-sm text-red-600">Cannot connect to AegisTwin API</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-3">
          {statusIcon(health.status)}
          <div>
            <h3 className="font-semibold">System Status</h3>
            <p className="text-sm text-gray-500">v{health.version}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Uptime</div>
          <div className="font-mono">{formatUptime(health.uptime_seconds)}</div>
        </div>
      </div>

      <div className="p-4 grid grid-cols-2 gap-4">
        {Object.entries(health.components).map(([name, status]) => (
          <div
            key={name}
            className={clsx(
              'p-3 rounded-lg flex items-center gap-2',
              status === 'healthy' ? 'bg-green-50' : 'bg-amber-50'
            )}
          >
            {statusIcon(status)}
            <span className="capitalize">{name.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
