import { useQuery } from '@tanstack/react-query'
import { Activity, Play, Shield, Clock } from 'lucide-react'
import EventTimeline from '../components/EventTimeline'
import SystemHealth from '../components/SystemHealth'
import { api } from '../lib/api'

interface Stats {
  total_runs: number
  events_today: number
  policy_denials: number
  avg_run_duration_ms: number
}

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.get<Stats>('/stats').then((r) => r.data),
  })

  const statCards = [
    { label: 'Total Runs', value: stats?.total_runs ?? 0, icon: Play, color: 'bg-blue-500' },
    { label: 'Events Today', value: stats?.events_today ?? 0, icon: Activity, color: 'bg-green-500' },
    { label: 'Policy Denials', value: stats?.policy_denials ?? 0, icon: Shield, color: 'bg-red-500' },
    { label: 'Avg Duration', value: `${stats?.avg_run_duration_ms ?? 0}ms`, icon: Clock, color: 'bg-purple-500' },
  ]

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className={`${color} p-2 rounded-lg`}>
                <Icon className="h-5 w-5 text-white" />
              </div>
              <div>
                <div className="text-2xl font-bold">{value}</div>
                <div className="text-sm text-gray-500">{label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <EventTimeline />
        <SystemHealth />
      </div>
    </div>
  )
}
