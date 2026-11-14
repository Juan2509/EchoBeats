import { useEffect, useState } from 'react'

export function AIStatus() {
  const [state, setState] = useState<{ enabled: boolean; configured: boolean } | null>(null)
  const [error, setError] = useState(false), [attempt, retry] = useState(0)
  useEffect(() => {
    let alive = true
    const abort = new AbortController(), timeout = setTimeout(() => abort.abort(), 10000)
    setState(null); setError(false)
    fetch('/api/v1/ai/status', { signal: abort.signal, cache: 'no-store' }).then(async response => {
      const value = await response.json()
      if (!response.ok || typeof value.enabled !== 'boolean' || typeof value.configured !== 'boolean') throw new Error('invalid_status')
      if (alive) setState({ enabled: value.enabled, configured: value.configured })
    }).catch(() => { if (alive) setError(true) }).finally(() => clearTimeout(timeout))
    return () => { alive = false; abort.abort(); clearTimeout(timeout) }
  }, [attempt])
  return <section aria-label="Estado de IA"><h3>Integración de IA</h3>
    <p role="status">{error ? 'No se pudo consultar la configuración de IA.' : !state ? 'Consultando configuración…' : !state.configured ? 'Falta configurar el proveedor en el servidor.' : !state.enabled ? 'Proveedor configurado; integración desactivada.' : 'Integración habilitada en la configuración.'}</p>
    <p className="note">Esta consulta no llama al proveedor ni comprueba saldo o acceso. La búsqueda semántica aún no está implementada. Tus audios no se envían en el flujo de fichas de texto.</p>
    <button className="secondary" onClick={() => retry(value => value + 1)}>Actualizar estado de IA</button>
  </section>
}
