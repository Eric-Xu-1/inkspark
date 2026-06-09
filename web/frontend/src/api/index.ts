export interface Step {
  step_id: string
  phase: string
  title: string
  status: string
  agent: string
  detail: string
  artifact_key: string | null
  created_at: number
}

export interface Artifact {
  content: string
  format: string
  meta?: Record<string, string>
}

export interface Conversation {
  id: string
  status: string
  topic: string
  requirements: string
  mode: string
  category: string
}

import { stripYamlFrontMatter } from '../utils/markdown'

const API = '/api/conversations'

export async function createConversation(): Promise<string> {
  const res = await fetch(API, { method: 'POST' })
  const data = await res.json()
  return data.id
}

export async function startConversation(id: string, body: Record<string, unknown>) {
  await fetch(`${API}/${id}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function fetchConversation(id: string): Promise<Conversation> {
  const res = await fetch(`${API}/${id}`)
  return res.json()
}

export async function fetchSteps(id: string): Promise<Step[]> {
  const res = await fetch(`${API}/${id}/steps`)
  const data = await res.json()
  return data.steps
}

export async function fetchArtifact(id: string, stepId: string): Promise<Artifact> {
  const res = await fetch(`${API}/${id}/artifacts/${stepId}`)
  return res.json()
}

export async function submitAction(id: string, stepId: string, action: string, payload?: Record<string, unknown>) {
  await fetch(`${API}/${id}/actions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, step_id: stepId, payload }),
  })
}

export function streamUrl(id: string) {
  return `${API}/${id}/stream`
}

export function exportUrl(id: string) {
  return `${API}/${id}/export`
}

function parseExportFilename(disposition: string): string {
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) return decodeURIComponent(utf8Match[1])
  const plainMatch = disposition.match(/filename="([^"]+)"/i)
  if (plainMatch) return plainMatch[1]
  return 'article.md'
}

async function fetchExportResponse(id: string): Promise<Response> {
  const res = await fetch(exportUrl(id))
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(detail || `导出失败 (${res.status})`)
  }
  return res
}

export async function fetchExportContent(id: string): Promise<Artifact> {
  const res = await fetchExportResponse(id)
  const raw = await res.text()
  const { meta, body } = stripYamlFrontMatter(raw)
  return { content: body, format: 'markdown', meta }
}

export async function downloadMarkdown(id: string): Promise<void> {
  const res = await fetchExportResponse(id)
  const blob = await res.blob()
  const filename = parseExportFilename(res.headers.get('Content-Disposition') || '')
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
