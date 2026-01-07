/**
 * Event Streaming
 */

import WebSocket from 'ws';
import { Event } from './types';

export type EventHandler = (event: Event) => void;
export type ErrorHandler = (error: Error) => void;

export class EventStream {
  private ws: WebSocket | null = null;
  private handlers: EventHandler[] = [];
  private errorHandlers: ErrorHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseUrl: string;
  private options: { runId?: string; eventTypes?: string[] };

  constructor(
    baseUrl: string,
    options?: { runId?: string; eventTypes?: string[] }
  ) {
    this.baseUrl = baseUrl;
    this.options = options ?? {};
  }

  connect(): void {
    let url = `${this.baseUrl}/ws/events`;
    const params: string[] = [];
    
    if (this.options.runId) {
      params.push(`run_id=${this.options.runId}`);
    }
    if (this.options.eventTypes?.length) {
      params.push(`event_types=${this.options.eventTypes.join(',')}`);
    }
    
    if (params.length) {
      url += `?${params.join('&')}`;
    }

    this.ws = new WebSocket(url);

    this.ws.on('open', () => {
      this.reconnectAttempts = 0;
    });

    this.ws.on('message', (data: WebSocket.Data) => {
      try {
        const event = JSON.parse(data.toString()) as Event;
        
        if ((event as any).type === 'connected' || (event as any).type === 'ping') {
          return;
        }
        
        this.handlers.forEach(handler => handler(event));
      } catch (error) {
        // Ignore parse errors
      }
    });

    this.ws.on('error', (error) => {
      this.errorHandlers.forEach(handler => handler(error));
    });

    this.ws.on('close', () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
      }
    });
  }

  onEvent(handler: EventHandler): void {
    this.handlers.push(handler);
  }

  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  disconnect(): void {
    this.maxReconnectAttempts = 0;
    this.ws?.close();
    this.ws = null;
  }

  subscribe(eventTypes: string[]): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        event_types: eventTypes,
      }));
    }
  }
}
