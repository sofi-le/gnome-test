import { Platform } from 'react-native';
import { ParseResult, ReportResult } from './types';
import { API_BASE_URL } from './config';

async function readErrorBody(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === 'string') return data.detail;
    return JSON.stringify(data);
  } catch {
    try {
      return await res.text();
    } catch {
      return res.statusText;
    }
  }
}

function guessMimeType(fileName: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'txt': return 'text/plain';
    case 'csv': return 'text/csv';
    case 'zip': return 'application/zip';
    default:    return 'application/octet-stream';
  }
}

export async function parseFile(fileUri: string, fileName: string): Promise<ParseResult> {
  console.log(`[api] parseFile name=${fileName} uri=${fileUri} base=${API_BASE_URL}`);

  const form = new FormData();
  // React Native FormData accepts a {uri, name, type} object; cast to any for TS.
  form.append('file', {
    uri: Platform.OS === 'ios' ? fileUri.replace('file://', '') : fileUri,
    name: fileName,
    type: guessMimeType(fileName),
  } as any);

  const res = await fetch(`${API_BASE_URL}/api/parse`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    throw new Error(`Parse failed (${res.status}): ${await readErrorBody(res)}`);
  }
  return (await res.json()) as ParseResult;
}

export async function getReport(sessionId: string): Promise<ReportResult> {
  console.log(`[api] getReport session_id=${sessionId} base=${API_BASE_URL}`);

  const url = `${API_BASE_URL}/api/report?session_id=${encodeURIComponent(sessionId)}`;
  const res = await fetch(url, { method: 'POST' });

  if (!res.ok) {
    throw new Error(`Report failed (${res.status}): ${await readErrorBody(res)}`);
  }
  return (await res.json()) as ReportResult;
}

export function getPdfUrl(sessionId: string): string {
  if (!sessionId) return '';
  return `${API_BASE_URL}/api/pdf/${encodeURIComponent(sessionId)}`;
}

export async function checkHealth(): Promise<{ status: string; sessions: number }> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}
