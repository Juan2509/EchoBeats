import { useEffect, useRef, useState } from 'react'
import { ImportPanel } from '../features/import/ImportPanel'
import { MetadataEditor } from '../features/metadata/MetadataEditor'
import { AlbumView, Library } from '../features/library/Library'
import { PlayerBar, PlayerProvider } from '../features/player/Player'

import { PlaylistView } from '../features/playlists/Playlists'
import { DocumentsPage } from '../features/documents/DocumentsPage'
import { ExploreView } from '../features/explore/ExploreView'
import { FavoritesProvider } from '../features/favorites/Favorites'
import { AppearanceProvider } from '../features/appearance/Appearance'
import {SettingsPage} from '../features/appearance/SettingsPage'
import {CreateAlbumDialog} from '../features/library/CreateAlbumDialog'

export function App() {
  const [location, setLocation] = useState(() => window.location.pathname + window.location.search)
  const [refresh, setRefresh] = useState(0)
  const [creatingAlbum,setCreatingAlbum]=useState(false)
  useEffect(()=>{const changed=()=>setRefresh(value=>value+1);window.addEventListener('echobeats:library-changed',changed);window.addEventListener('echobeats:track-deleted',changed);return()=>{window.removeEventListener('echobeats:library-changed',changed);window.removeEventListener('echobeats:track-deleted',changed)}},[])
  const [metadataActivated, setMetadataActivated] = useState(false)
  const [exploreVisited, setExploreVisited] = useState(false)
  const [playlistDirty, setPlaylistDirty] = useState(false)
  const [wallDirty, setWallDirty] = useState(false)
  const heading = useRef<HTMLElement>(null)
  const path = location.split('?')[0]
  const exploring = path === '/explorar'
  useEffect(() => { if (exploring) setExploreVisited(true) }, [exploring])
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
  useEffect(()=>{const header=document.querySelector<HTMLElement>('.site-header');if(!header)return
    const measure=()=>document.documentElement.style.setProperty('--navigation-height',`${header.offsetHeight}px`)
    const observer=new ResizeObserver(measure);observer.observe(header);measure()
    return()=>observer.disconnect()
  },[])
  useEffect(() => {
    const reveal = (event: FocusEvent) => {
      const target = event.target
      if (!(target instanceof HTMLElement) || target.matches('main') || !target.matches(':focus-visible') || target.closest('.wall-panel, .player-bar, dialog, .skip-link')) return
      requestAnimationFrame(() => {
        if (!target.isConnected || document.activeElement !== target) return
        const control = target.getBoundingClientRect(), player = document.querySelector('.player-bar')?.getBoundingClientRect()
        if (player && control.bottom > player.top - 16 && control.top < player.bottom) window.scrollBy(0, control.bottom - player.top + 24)
      })
    }
    document.addEventListener('focusin', reveal)
    return () => document.removeEventListener('focusin', reveal)
  }, [])
  const changed = () => setRefresh(value => value + 1)
  return <AppearanceProvider albumId={album?.[1]}><FavoritesProvider><PlayerProvider refresh={refresh}><div className="workspace" data-view={album?'album':'collection'}>
    <a className="skip-link" href="#content">Saltar al contenido</a>
    <header className="site-header"><a className="brand" href="/" onClick={event => { event.preventDefault(); navigate('/') }}><span className="mark" aria-hidden="true">◉</span> EchoBeats</a>
      <nav aria-label="Navegación principal">{[['/', 'Inicio'], ['/biblioteca', 'Biblioteca'], ['/explorar', 'Explorar'], ['/documentos', 'Documentos'], ['/configuracion','Configuración']].map(([href, label]) => <a key={href} href={href} aria-current={path === href ? 'page' : undefined} onClick={event => { event.preventDefault(); navigate(href) }}>{label}</a>)}</nav>
    </header>
    {creatingAlbum&&<CreateAlbumDialog close={()=>setCreatingAlbum(false)} created={id=>{setCreatingAlbum(false);changed();navigate(`/albumes/${id}`)}}/>}
    <main id="content" ref={heading} tabIndex={-1}>
      {path === '/' && <section className="hero"><p className="eyebrow">Una colección que se siente tuya</p><h1>Tu música.<br /><em>Tu espacio.</em></h1><p className="intro">Redescubre los discos que te acompañan. Reúne tu música y empieza a construir tu propio rincón para escucharla.</p><a className="button-link" href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>Abrir mi biblioteca <span aria-hidden="true">↗</span></a><div className="pillars"><div><span>01</span><h2>Música propia</h2><p>Importa tus archivos de audio y conserva tu colección.</p></div><div><span>02</span><h2>Un lugar por álbum</h2><p>Consulta sus portadas, artistas y canciones.</p></div><div><span>03</span><h2>Nuevas conexiones</h2><p>Explora fichas y posibles coincidencias de tu colección.</p></div></div></section>}
      {path === '/biblioteca' && <Library refresh={refresh} navigate={navigate} search={search} createAlbum={()=>setCreatingAlbum(true)} />}
      {playlist && <PlaylistView key={playlist[1]} id={playlist[1]} navigate={navigate} onSaved={changed} onDirty={setPlaylistDirty} />}
      {album && <AlbumView key={album[1]} id={album[1]} refresh={refresh} navigate={navigate} onDirty={setWallDirty} />}
      {(exploring || exploreVisited) && <ExploreView active={exploring} search={exploring ? search : ''} navigate={navigate} />}
      {path==='/documentos' && <DocumentsPage />}
      {path==='/configuracion'&&<SettingsPage search={search} navigate={navigate}/>}
      {!['/', '/biblioteca', '/explorar', '/documentos','/configuracion'].includes(path) && !album && !playlist && <section><h1>No encontramos esa página</h1><a href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>Volver a la biblioteca</a></section>}
      <div hidden={path !== '/biblioteca'}>
        {path==='/biblioteca'&&<ImportPanel onImported={changed} />}
        <details className="metadata-tools" onToggle={event => { if (event.currentTarget.open) setMetadataActivated(true) }}><summary>Editar canciones, álbumes y portadas</summary>{metadataActivated && <MetadataEditor refresh={refresh} onSaved={changed} />}</details>
      </div>
    </main>
    <PlayerBar navigate={navigate} />
  </div></PlayerProvider></FavoritesProvider></AppearanceProvider>
}
