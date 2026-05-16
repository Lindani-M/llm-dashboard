import { Metrics, Commentary, CommentarySection } from './types';

const BASE = '/api';

// Never log or expose response bodies — only safe status info goes to console.
function logApiError(action: string, status: number) {
  console.error(`[Dashboard] ${action} failed (HTTP ${status})`);
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    // Use only the server's friendly message — never expose stack traces or internals
    return body?.detail || body?.error || 'An unexpected error occurred.';
  } catch {
    return 'An unexpected error occurred.';
  }
}

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${BASE}/metrics`);
  if (!res.ok) {
    logApiError('fetchMetrics', res.status);
    throw new Error(await parseError(res));
  }
  return res.json();
}

export async function fetchCommentary(): Promise<Commentary> {
  const res = await fetch(`${BASE}/commentary`);
  if (!res.ok) {
    logApiError('fetchCommentary', res.status);
    throw new Error(await parseError(res));
  }
  return res.json();
}

export async function saveCommentary(
  sectionId: string,
  content: string
): Promise<CommentarySection> {
  const res = await fetch(`${BASE}/commentary/${sectionId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    logApiError('saveCommentary', res.status);
    throw new Error(await parseError(res));
  }
  return res.json();
}

export async function revertCommentary(
  sectionId: string
): Promise<CommentarySection> {
  const res = await fetch(`${BASE}/commentary/${sectionId}/override`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    logApiError('revertCommentary', res.status);
    throw new Error(await parseError(res));
  }
  return res.json();
}

export async function checkDataStatus(): Promise<{ needs_refresh: boolean }> {
  try {
    const res = await fetch(`${BASE}/data-status`);
    if (!res.ok) return { needs_refresh: false };
    return res.json();
  } catch {
    return { needs_refresh: false };
  }
}

export async function refreshData(): Promise<{
  commentary: Commentary;
  metrics: Metrics;
  errors: string[];
}> {
  const res = await fetch(`${BASE}/refresh`, { method: 'POST' });
  if (!res.ok) {
    logApiError('refreshData', res.status);
    throw new Error(await parseError(res));
  }
  return res.json();
}
