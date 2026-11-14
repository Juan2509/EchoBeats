import { useEffect, useRef, useState } from 'react'
import { getHealth } from '../shared/api/health'
import { ImportPanel } from '../features/import/ImportPanel'
import { MetadataEditor } from '../features/metadata/MetadataEditor'
import { AlbumView, Library } from '../features/library/Library'
import { PlayerBar, PlayerProvider } from '../features/player/Player'

import { PlaylistView } from '../features/playlists/Playlists'
import { AIStatus } from '../features/descriptions/AIStatus'

type Connection = 'checking' | 'connected' | 'error'
export function App() {
  const [location, setLocation] = useState(() => window.location.pathname + window.location.search)
  const [connection, setConnection] = useState<Connection>('checking')
  const [attempt, setAttempt] = useState(0)
  const [refresh, setRefresh] = useState(0)
  const [configuration, setConfiguration] = useState(false)
  const [playlistDirty, setPlaylistDirty] = useState(false)
  const [wallDirty, setWallDirty] = useState(false)
  const heading = useRef<HTMLElement>(null)
  const path = location.split('?')[0]
  const search = location.includes('?') ? location.slice(location.indexOf('?')) : ''
  const album = /^\/albumes\/([0-9a-f-]{36})$/i.exec(path)
  const playlist = /^\/playlists\/([0-9a-f-]{36})$/i.exec(path)
  function navigate(destination: string) {
    if (destination === location) return
    if (!window.dispatchEvent(new Event('echobeats:before-navigation', { cancelable: true }))) return
    if (wallDirty && !window.confirm('La pared tiene cambios pendientes u operaciones en curso. Puedes cancelar para esperar o guardar. Si sales, se descartan los cambios aún no enviados; un guardado ya enviado puede completarse. ¿Salir?')) return
    if (playlistDirty && !window.confirm('Hay cambios sin guardar en la playlist. ¿Salir y descartarlos?')) return
    window.history.pushState(null, '', destination)
    setLocation(destination)
  }
  useEffect(() => {
    const pop = () => {
      if (!window.dispatchEvent(new Event('echobeats:before-navigation', { cancelable: true }))) { window.history.pushState(null, '', location); return }
      if (wallDirty && !window.confirm('La pared tiene cambios pendientes u operaciones en curso. Puedes cancelar para esperar o guardar. Si sales, se descartan los cambios aún no enviados; un guardado ya enviado puede completarse. ¿Salir?')) { window.history.pushState(null, '', location); return }
      if (playlistDirty && !window.confirm('Hay cambios sin guardar en la playlist. ¿Salir y descartarlos?')) { window.history.pushState(null, '', location); return }
      setLocation(window.location.pathname + window.location.search)
    }
    window.addEventListener('popstate', pop)
    return () => window.removeEventListener('popstate', pop)
  }, [playlistDirty, wallDirty, location])
  useEffect(() => { heading.current?.focus(); window.scrollTo(0, 0) }, [path])
  useEffect(() => {
    const controller = new AbortController()
    let disposed = false
    setConnection('checking')
    const timeout = window.setTimeout(() => controller.abort(), 5000)
    getHealth(controller.signal)
      .then(() => { if (!disposed) setConnection('connected') })
      .catch(() => { if (!disposed) setConnection('error') })
      .finally(() => window.clearTimeout(timeout))
    return () => { disposed = true; controller.abort(); window.clearTimeout(timeout) }
  }, [attempt])
  const changed = () => setRefresh(value => value + 1)
  return <PlayerProvider refresh={refresh}><div className="workspace">
    <a className="skip-link" href="#content">Saltar al contenido</a>
    <header className="site-header"><a className="brand" href="/" onClick={event => { event.preventDefault(); navigate('/') }}><span className="mark" aria-hidden="true">◉</span> EchoBeats</a>
      <nav aria-label="Navegación principal">{[['/', 'Inicio'], ['/biblioteca', 'Biblioteca'], ['/explorar', 'Explorar']].map(([href, label]) => <a key={href} href={href} aria-current={path === href ? 'page' : undefined} onClick={event => { event.preventDefault(); navigate(href) }}>{label}</a>)}<button className="secondary" aria-expanded={configuration} onClick={() => setConfiguration(value => !value)}>Configuración</button></nav>
    </header>
    {configuration && <aside className="settings" aria-label="Configuración local"><h2>Tu instalación local</h2><p>MP3, WAV PCM, FLAC, Ogg Vorbis y Opus · hasta 50 MiB por archivo · 20 archivos y 200 MiB por solicitud.</p><p>La importación y edición de etiquetas no envían tus canciones a servicios de IA.</p><p role="status">{connection === 'connected' ? 'Servidor conectado' : connection === 'checking' ? 'Comprobando conexión…' : 'No se pudo conectar con el servidor'}</p><button onClick={() => setAttempt(value => value + 1)}>Comprobar conexión</button><AIStatus /></aside>}
    <main id="content" ref={heading} tabIndex={-1}>
      {path === '/' && <section className="hero"><p className="eyebrow">Una colección que se siente tuya</p><h1>Tu música.<br /><em>Tu espacio.</em></h1><p className="intro">Redescubre los discos que te acompañan. Reúne tu música y empieza a construir tu propio rincón para escucharla.</p><a className="button-link" href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>Abrir mi biblioteca <span aria-hidden="true">↗</span></a><div className="pillars"><div><span>01</span><h2>Música propia</h2><p>Importa tus archivos de audio y conserva tu colección.</p></div><div><span>02</span><h2>Un lugar por álbum</h2><p>Consulta sus portadas, artistas y canciones.</p></div><div><span>03</span><h2>Nuevas conexiones</h2><p>Más adelante, explora tu música por sensaciones.</p></div></div></section>}
      {path === '/biblioteca' && <Library refresh={refresh} navigate={navigate} search={search} />}
      {playlist && <PlaylistView key={playlist[1]} id={playlist[1]} navigate={navigate} onSaved={changed} onDirty={setPlaylistDirty} />}
      {album && <AlbumView key={album[1]} id={album[1]} refresh={refresh} navigate={navigate} onDirty={setWallDirty} />}
      {path === '/explorar' && <section className="hero"><p className="eyebrow">Próximamente</p><h1>¿A qué suena<br />este momento?</h1><p className="intro">La exploración por sensaciones se incorporará cuando estén conectadas las fichas musicales, la API de IA y la búsqueda vectorial. Puedes seguir organizando tu biblioteca.</p><a href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>Ir a mi música →</a></section>}
      {!['/', '/biblioteca', '/explorar'].includes(path) && !album && !playlist && <section><h1>No encontramos esa página</h1><a href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>Volver a la biblioteca</a></section>}
      <div hidden={path !== '/biblioteca'}>
        <ImportPanel onImported={changed} />
        <details className="metadata-tools"><summary>Editar canciones, álbumes y portadas</summary><MetadataEditor refresh={refresh} onSaved={changed} /></details>
      </div>
    </main>
    <footer>EchoBeats <span>Tu colección personal · Tu música, tu espacio</span></footer>
    <PlayerBar navigate={navigate} />
  </div></PlayerProvider>
}
