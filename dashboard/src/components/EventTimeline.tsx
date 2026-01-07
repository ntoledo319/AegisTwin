import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { ArrowRight, Zap } from 'lucide-react'
import { clsx } from 'clsx'

interface Event {
  event_id: string
  event_type: string
  timestamp: string
  run_id: string
  payload_hash: string
}

interface EventTimelineProps {
  runId?: string
  maxEvents?: number
}

const eventTypeColors: Record<string, string> = {
  'ingest.requested': 'bg-blue-500',
  'ingest.completed': 'bg-green-500',
  'data.normalized': 'bg-purple-500',
  'analysis.completed': 'bg-indigo-500',
  'graph.updated': 'bg-cyan-500',
  'memory.updated': 'bg-teal-500',
  'query.requested': 'bg-amber-500',
  'query.responded': 'bg-amber-600',
  'policy.denied': 'bg-red-500',
  'audit.logged': 'bg-gray-500',
}

export default function EventTimeline({ runId, maxEvents = 50 }: EventTimelineProps) {
  const [events, setEvents] = useState<Event[]>([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const wsUrl = runId 
      ? `ws://localhost:8000/ws/events?run_id=${runId}`
      : 'ws://localhost:8000/ws/events'
    
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data)
      if (event.type === 'connected' || event.type === 'ping') return
      
      setEvents((prev) => [event, ...prev].slice(0, maxEvents))
    }
    
    return () => ws.close()
  }, [runId, maxEvents])

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <h3 className="font-semibold">Event Timeline</h3>
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              'h-2 w-2 rounded-full',
              connected ? 'bg-green-500' : 'bg-red-500'
            )}
          />
          <span className="text-sm text-gray-500">
            {connected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      <div className="divide-y max-h-96 overflow-auto">
        {events.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <Zap className="h-8 w-8 mx-auto mb-2" />
            <p>Waiting for events...</p>
          </div>
        ) : (
          events.map((event) => (
            <div key={event.event_id} className="p-3 hover:bg-gray-50">
              <div className="flex items-center gap-3">
                <span
                  className={clsx(
                    'h-3 w-3 rounded-full',
                    eventTypeColors[event.event_type] || 'bg-gray-400'
                  )}
                />
                <span className="font-mono text-sm">{event.event_type}</span>
                <ArrowRight className="h-4 w-4 text-gray-300" />
                <span className="text-xs text-gray-500 font-mono">
                  {event.event_id.slice(0, 8)}
                </span>
                <span className="ml-auto text-xs text-gray-400">
                  {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
