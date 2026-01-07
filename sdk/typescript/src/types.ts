/**
 * AegisTwin TypeScript Types
 */

export interface AegisTwinConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface IngestRequest {
  records: Record<string, unknown>[];
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface IngestResponse {
  run_id: string;
  event_count: number;
}

export interface QueryRequest {
  query: string;
  context?: Record<string, unknown>;
  max_results?: number;
}

export interface QueryResponse {
  answer: string;
  confidence: number;
  sources: string[];
  run_id: string;
}

export interface Run {
  run_id: string;
  created_at: string;
  completed_at: string | null;
  source: string | null;
  event_count: number;
  metadata: Record<string, unknown>;
}

export interface Event {
  event_id: string;
  event_type: string;
  timestamp: string;
  run_id: string | null;
  parent_event_id: string | null;
  payload_hash: string;
  [key: string]: unknown;
}

export interface Policy {
  id: string;
  action: string;
  resource: string;
  actor: string;
  effect: 'allow' | 'deny' | 'require_approval';
  reason?: string;
  priority: number;
}

export interface PolicyCheckRequest {
  action: string;
  resource: string;
  actor: string;
}

export interface PolicyCheckResponse {
  allowed: boolean;
  reason?: string;
  policy_id?: string;
}

export interface ReplayRequest {
  run_id: string;
  verify_hashes?: boolean;
}

export interface ReplayResponse {
  success: boolean;
  events_replayed: number;
  divergences: Array<{
    event_id: string;
    expected_hash: string;
    actual_hash: string;
  }>;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  components: Record<string, string>;
}

export interface AuditEntry {
  id: number;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  outcome: string;
  metadata: Record<string, unknown>;
}
