import { useEffect, useState } from 'react'
import { Activity, Circle } from 'lucide-react'

interface Event {
  event_id: string
  event_type: string
  timestamp: string
  run_id: string
  payload_hash?: string
}

interface EventStreamProps {
  runId?: string
  eventTypes?: string[]
}

export default function EventStream({ runId, eventTypes }: EventStreamProps) {
  const [events, setEvents] = useState<Event[]>([])
  const [connected, setConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    const wsUrl = runId 
      ? `ws://localhost:8000/ws/events/${runId}`
      : `ws://localhost:8000/ws/events${eventTypes ? `?event_types=${eventTypes.join(',')}` : ''}`

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      setConnected(true)
    }

    websocket.onmessage = (event) => {
      const newEvent = JSON.parse(event.data)
      setEvents((prev) => [newEvent, ...prev].slice(0, 100)) // Keep last 100
    }

    websocket.onerror = () => {
      setConnected(false)
    }

    websocket.onclose = () => {
      setConnected(false)
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [runId, eventTypes])

  const getEventColor = (eventType: string) => {
    if (eventType.includes('denied') || eventType.includes('error')) return 'text-red-500'
    if (eventType.includes('completed') || eventType.includes('success')) return 'text-green-500'
    if (eventType.includes('requested') || eventType.includes('started')) return 'text-blue-500'
    return 'text-gray-500'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Live Event Stream
        </h3>
        <div className="flex items-center gap-2">
          <Circle className={`w-3 h-3 ${connected ? 'fill-green-500 text-green-500' : 'fill-gray-400 text-gray-400'}`} />
          <span className="text-sm text-gray-600">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Waiting for events...
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.event_id}
              className="border-l-4 border-blue-500 bg-gray-50 p-3 rounded text-sm"
            >
              <div className="flex items-center justify-between">
                <span className={`font-mono font-semibold ${getEventColor(event.event_type)}`}>
                  {event.event_type}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-600">
                Run: {event.run_id} • ID: {event.event_id.slice(0, 8)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
