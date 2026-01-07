/**
 * AegisTwin Client
 */

import axios, { AxiosInstance } from 'axios';
import {
  AegisTwinConfig,
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
  Run,
  Event,
  Policy,
  PolicyCheckRequest,
  PolicyCheckResponse,
  ReplayRequest,
  ReplayResponse,
  HealthResponse,
  AuditEntry,
} from './types';
import { EventStream } from './events';

export class AegisTwin {
  private client: AxiosInstance;
  private config: AegisTwinConfig;

  constructor(config: AegisTwinConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout ?? 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(config.apiKey && { 'Authorization': `Bearer ${config.apiKey}` }),
      },
    });
  }

  async health(): Promise<HealthResponse> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async ingest(request: IngestRequest): Promise<IngestResponse> {
    const response = await this.client.post('/ingest', request);
    return response.data;
  }

  async query(query: string | QueryRequest): Promise<QueryResponse> {
    const request = typeof query === 'string' ? { query } : query;
    const response = await this.client.post('/query', request);
    return response.data;
  }

  async listRuns(limit = 100, offset = 0): Promise<Run[]> {
    const response = await this.client.get('/runs', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getRun(runId: string): Promise<Run> {
    const response = await this.client.get(`/runs/${runId}`);
    return response.data;
  }

  async getRunTrace(runId: string): Promise<Event[]> {
    const response = await this.client.get(`/runs/${runId}/trace`);
    return response.data;
  }

  async deleteRun(runId: string): Promise<void> {
    await this.client.delete(`/runs/${runId}`);
  }

  async replay(request: ReplayRequest): Promise<ReplayResponse> {
    const response = await this.client.post('/replay', request);
    return response.data;
  }

  async listPolicies(): Promise<Policy[]> {
    const response = await this.client.get('/policies');
    return response.data;
  }

  async createPolicy(policy: Omit<Policy, 'id'>): Promise<Policy> {
    const response = await this.client.post('/policies', policy);
    return response.data;
  }

  async deletePolicy(policyId: string): Promise<void> {
    await this.client.delete(`/policies/${policyId}`);
  }

  async checkPolicy(request: PolicyCheckRequest): Promise<PolicyCheckResponse> {
    const response = await this.client.post('/policies/check', request);
    return response.data;
  }

  async queryAudit(params?: {
    actor?: string;
    action?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }): Promise<AuditEntry[]> {
    const response = await this.client.get('/audit', { params });
    return response.data;
  }

  streamEvents(options?: {
    runId?: string;
    eventTypes?: string[];
  }): EventStream {
    const wsUrl = this.config.baseUrl
      .replace('http://', 'ws://')
      .replace('https://', 'wss://');
    
    return new EventStream(wsUrl, options);
  }
}
