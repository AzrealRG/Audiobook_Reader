// Mirrors server/schemas.py
export interface User { id: number; email: string; created_at: string }
export interface Token { access_token: string; token_type: string }

export interface Book {
  id: string
  title: string | null
  original_filename: string | null
  stage: string
  total_chapters: number | null
  completed_chapters: number | null
  error: string | null
  created_at: string
  updated_at: string
}

// TODO: replace once we have a real manifest.json sample
export type Manifest = Record<string, unknown>

// Backend stage strings are inconsistent in casing, so we normalise.
export function stageInfo(stage: string) {
  const s = stage.trim().toLowerCase()
  return {
    ready: s === 'ready',
    failed: s === 'failed',
    working: s !== 'ready' && s !== 'failed',
    label: s === 'queued' ? 'Waiting in queue' : s === 'ready' ? 'Ready to listen' : s === 'failed' ? 'Failed' : stage,
  }
}
