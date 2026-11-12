import { useEffect, useState } from 'react'
import { getHealth } from '../shared/api/health'
import { ImportPanel } from '../features/import/ImportPanel'

type Connection = 'checking' | 'connected' | 'error'

export function App() {
  const [connection, setConnection] = useState<Connection>('checking')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let disposed = false
    setConnection('checking')
    const timeout = window.setTimeout(() => controller.abort(), 5000)
    getHealth(controller.signal)
      .then(() => { if (!disposed) setConnection('connected') })
      .catch(() => { if (!disposed) setConnection('error') })
      .finally(() => window.clearTimeout(timeout))
    return () => {
      disposed = true
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [attempt])

  return (
    <main className="workspace">
      <header><span className="mark" aria-hidden="true">◉</span> EchoBeats</header>
      <section className="card" aria-labelledby="title">
        <p className="eyebrow">Tu colección personal</p>
        <h1 id="title">El primer compás.</h1>
        <p className="intro">Empieza por tu música. Importa tus archivos para dar forma a tu biblioteca personal.</p>
        <div className={`connection ${connection}`} role="status" aria-live="polite">
          <span className="indicator" aria-hidden="true" />
          {connection === 'checking' && 'Comprobando conexión…'}
          {connection === 'connected' && 'Servidor conectado'}
          {connection === 'error' && 'No se pudo conectar con el servidor'}
        </div>
        {connection === 'error' && <button onClick={() => setAttempt(value => value + 1)}>Reintentar conexión</button>}
        <ImportPanel />
        <p className="note">La vista de biblioteca, la edición de metadatos y el reproductor estarán disponibles en los próximos pasos.</p>
      </section>
      <footer>Tu música. Tu espacio.</footer>
    </main>
  )
}
