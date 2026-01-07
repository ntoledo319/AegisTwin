/**
 * AegisTwin TypeScript SDK
 * 
 * Provides client access to AegisTwin API with full type safety.
 * 
 * @example
 * ```typescript
 * import { AegisTwin } from '@aegistwin/sdk';
 * 
 * const client = new AegisTwin({
 *   baseUrl: 'http://localhost:8000',
 *   apiKey: 'aegis_xxx',
 * });
 * 
 * const runId = await client.ingest({ records: [...] });
 * const response = await client.query('What happened?');
 * ```
 */

export { AegisTwin } from './client';
export { EventStream } from './events';
export * from './types';
