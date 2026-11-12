export async function getHealth(signal: AbortSignal): Promise<void> {
  const response = await fetch('/api/v1/health', { signal, cache: 'no-store' })
  if (!response.ok) throw new Error('El servidor no respondió correctamente.')
  const result: unknown = await response.json()
  if (typeof result !== 'object' || result === null || !('status' in result) || result.status !== 'ok') {
    throw new Error('La respuesta del servidor no es válida.')
  }
}
