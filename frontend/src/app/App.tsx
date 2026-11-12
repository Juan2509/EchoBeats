import { useEffect, useState } from 'react'
import { getHealth } from '../shared/api/health'

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
        <p className="eyebrow">Entorno de desarrollo · P03</p>
        <h1 id="title">El primer compás.</h1>
        <p className="intro">La base de EchoBeats está en preparación. Aquí comprobaremos la conexión entre la interfaz y el servidor.</p>
        <div className={`connection ${connection}`} role="status" aria-live="polite">
          <span className="indicator" aria-hidden="true" />
          {connection === 'checking' && 'Comprobando conexión…'}
          {connection === 'connected' && 'Servidor conectado'}
          {connection === 'error' && 'No se pudo conectar con el servidor'}
        </div>
        {connection === 'error' && <button onClick={() => setAttempt(value => value + 1)}>Reintentar conexión</button>}
        <p className="note">La biblioteca, el reproductor y los muros se incorporarán en los siguientes pasos.</p>
      </section>
      <footer>Tu música. Tu espacio.</footer>
    </main>
  )
}
