export function stripYamlFrontMatter(text: string): { meta: Record<string, string>; body: string } {
  if (!text.startsWith('---')) {
    return { meta: {}, body: text }
  }

  const endIndex = text.indexOf('\n---', 3)
  if (endIndex === -1) {
    return { meta: {}, body: text }
  }

  const yamlBlock = text.slice(4, endIndex)
  const body = text.slice(endIndex + 4).replace(/^\s*\n/, '')
  const meta: Record<string, string> = {}

  for (const line of yamlBlock.split('\n')) {
    const match = line.match(/^([\w-]+):\s*"(.*)"\s*$/)
    if (!match) continue
    meta[match[1]] = match[2].replace(/\\"/g, '"').replace(/\\\\/g, '\\')
  }

  return { meta, body }
}
