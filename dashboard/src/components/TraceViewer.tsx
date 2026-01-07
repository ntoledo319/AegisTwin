import { useState } from 'react'
import { ChevronRight, ChevronDown, Clock, Hash } from 'lucide-react'

interface Event {
  event_id: string
  event_type: string
  timestamp: string
  run_id: string
  parent_event_id?: string
  payload_hash: string
}

interface TraceViewerProps {
  events: Event[]
}

export default function TraceViewer({ events }: TraceViewerProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set())

  const toggleEvent = (eventId: string) => {
    const newExpanded = new Set(expandedEvents)
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId)
    } else {
      newExpanded.add(eventId)
    }
    setExpandedEvents(newExpanded)
  }

  // Build event hierarchy
  const rootEvents = events.filter(e => !e.parent_event_id)
  
  const getChildren = (parentId: string) => {
    return events.filter(e => e.parent_event_id === parentId)
  }

  const renderEvent = (event: Event, depth: number = 0) => {
    const children = getChildren(event.event_id)
    const hasChildren = children.length > 0
    const isExpanded = expandedEvents.has(event.event_id)

    return (
      <div key={event.event_id} style={{ marginLeft: `${depth * 24}px` }}>
        <div
          className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer border-l-2 border-blue-500"
          onClick={() => hasChildren && toggleEvent(event.event_id)}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )
          ) : (
            <div className="w-4" />
          )}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-semibold text-blue-600">
                {event.event_type}
              </span>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(event.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
              <span className="flex items-center gap-1">
                <Hash className="w-3 h-3" />
                {event.payload_hash}
              </span>
              <span>ID: {event.event_id.slice(0, 8)}</span>
            </div>
          </div>
        </div>

        {isExpanded && children.map(child => renderEvent(child, depth + 1))}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Event Trace Timeline</h3>
      
      {events.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No events to display
        </div>
      ) : (
        <div className="space-y-1 max-h-[600px] overflow-y-auto">
          {rootEvents.map(event => renderEvent(event))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t text-sm text-gray-600">
        <p>Total Events: {events.length}</p>
        <p className="mt-1">
          Click events with children to expand/collapse the trace tree
        </p>
      </div>
    </div>
  )
}
