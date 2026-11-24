import {useEffect, useState} from 'react'
import type {FormEvent} from 'react'

type OpenAIStatus = {
  enabled: boolean
  configured: boolean
  key_editable: boolean
}

export function OpenAISettings() {
  const [status, setStatus] = useState<OpenAIStatus>()
  const [key, setKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/v1/ai/status', {cache: 'no-store', signal: controller.signal})
      .then(response => {
        if (!response.ok) throw new Error()
        return response.json()
      })
      .then(setStatus)
      .catch(() => {
        if (!controller.signal.aborted) setError('No se pudo consultar la configuración de OpenAI.')
      })
    return () => controller.abort()
  }, [])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving || !key.trim()) return
    setSaving(true)
    setSaved(false)
    setError('')
    try {
      const response = await fetch('/api/v1/ai/key', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key: key.trim()}),
        signal: AbortSignal.timeout(15000),
      })
      if (!response.ok) {
        setError(response.status === 422
          ? 'Revisa que hayas pegado una clave de API de OpenAI completa.'
          : 'No se pudo guardar la clave de OpenAI.')
        return
      }
      setStatus(await response.json())
      setKey('')
      setSaved(true)
    } catch {
      setError('No se pudo confirmar el guardado. Puedes volver a guardar la clave.')
    } finally {
      setSaving(false)
    }
  }

  return <section aria-labelledby="openai-settings-title">
    <h2 id="openai-settings-title">Conexión e IA</h2>
    {!status && !error && <p role="status">Cargando configuración…</p>}
    {status && !status.key_editable && <p>OpenAI se configura desde el servidor en esta instalación.</p>}
    {status && !status.enabled && <p>El servidor tiene la integración con OpenAI desactivada.</p>}
    {status?.key_editable && status.enabled && <form onSubmit={save} autoComplete="off">
      <p>{status.configured ? 'Hay una clave guardada en el servidor.' : 'Pega tu clave de OpenAI para usarla en Explorar.'}</p>
      <label htmlFor="openai-key">Clave API de OpenAI</label>
      <input id="openai-key" type="password" autoComplete="off" spellCheck={false}
        maxLength={512} required value={key} disabled={saving}
        onChange={event => {setKey(event.target.value); setSaved(false)}} />
      <button type="submit" disabled={saving || !key.trim()}>{saving ? 'Guardando…' : 'Guardar clave'}</button>
      {saved && <p role="status">Clave guardada. EchoBeats la usará en la próxima consulta de Explorar.</p>}
    </form>}
    {error && <p role="alert">{error}</p>}
  </section>
}
