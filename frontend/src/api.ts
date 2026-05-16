import { Metrics, Commentary, CommentarySection } from './types';

const BASE = '/api';

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchCommentary(): Promise<Commentary> {
  const res = await fetch(`${BASE}/commentary`);
  if (!res.ok) throw new Error('Failed to fetch commentary');
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
  if (!res.ok) throw new Error('Failed to save commentary');
  return res.json();
}

export async function revertCommentary(
  sectionId: string
): Promise<CommentarySection> {
  const res = await fetch(`${BASE}/commentary/${sectionId}/override`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to revert commentary');
  return res.json();
}

export async function refreshData(): Promise<{
  commentary: Commentary;
  metrics: Metrics;
  errors: string[];
}> {
  const res = await fetch(`${BASE}/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error('Refresh failed');
  return res.json();
}
