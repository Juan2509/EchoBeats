import { useEffect, useRef, useState } from 'react'
import { ExploreController } from './controller'
import { usePlayer } from '../player/Player'
import { Cover, useRead, artists } from '../library/Library'
import type { Track } from '../../shared/api/metadata'
import { DescriptionEditor } from '../descriptions/DescriptionEditor'

type Options = { items: { id: string; title?: string; name?: string }[]; total: number }
const sourceLabels: Record<string,string> = { manual:'Manual',verified:'Verificada con fuente',metadata:'Metadatos existentes' }
const featureLabels: Record<string,string> = { tempo_bpm:'Tempo (BPM)',timbre:'Timbre',instruments:'Instrumentos',energy:'Energía',mood:'Emoción',genre:'Género',context:'Contexto',mode:'Modo',percussion:'Percusión',voice:'Voz',note_density:'Densidad de notas' }
export function ExploreView({ search, navigate }: { search: string; navigate: (path:string)=>void }) {
  const rawReference=new URLSearchParams(search).get('similar')
  const referenceId=rawReference&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(rawReference)?rawReference:undefined
  const invalidReference=!!rawReference&&!referenceId
  const reference=useRead<Track>(`/tracks/${referenceId}`,0,!!referenceId)
  const albums=useRead<Options>('/albums?limit=100&include_empty_system=false',0)
  const playlists=useRead<Options>('/playlists?limit=100',0)
  const controller=useRef<ExploreController|null>(null)
  const [state,setState]=useState(()=>new ExploreController().state)
  const [query,setQuery]=useState(''),[mode,setMode]=useState<'lexical'|'semantic'|'hybrid'>('lexical'),[limit,setLimit]=useState('5')
  const [album,setAlbum]=useState(''),[playlist,setPlaylist]=useState(''),[explain,setExplain]=useState(false)
  const player=usePlayer()
  useEffect(()=>{
    const instance=new ExploreController();controller.current=instance
    const unsubscribe=instance.subscribe(()=>setState(instance.state));setState(instance.state)
    return()=>{unsubscribe();instance.dispose();controller.current=null}
  },[])
  const data=state.data
  const queue=data?.results.map(item=>item.track)??[]
  return <section className="explore-view" aria-labelledby="explore-title">
    <p className="eyebrow">Redescubre tu colección</p><h1 id="explore-title">¿A qué suena este momento?</h1>
    <p className="intro">Consulta las fichas de tu biblioteca y escucha posibles candidatos. Las citas muestran lo registrado; no son una garantía de coincidencia con tus gustos.</p>
    {invalidReference&&<p role="alert">La referencia no es válida. <a href="/explorar" onClick={e=>{e.preventDefault();navigate('/explorar')}}>Volver a la consulta</a></p>}
    {referenceId&&<div className="explore-reference"><h2>Similitud desde una canción</h2><p>{reference.loading?'Cargando referencia…':reference.error||reference.data?.title}</p><p>Se usa su vector guardado; no se recomienda la misma pista.</p><a href="/explorar" onClick={e=>{e.preventDefault();navigate('/explorar')}}>Consultar por texto</a></div>}
    <form className="explore-form" onSubmit={event=>{
      event.preventDefault()
      void controller.current?.search({query,mode,limit:Number(limit),explain,album_id:album||undefined,playlist_id:playlist||undefined,track_id:referenceId})
    }}>
      <fieldset disabled={state.loading||invalidReference||!!referenceId&&(reference.loading||!!reference.error)}>
        {!referenceId&&<><label htmlFor="explore-query">¿Qué quieres encontrar?</label><textarea id="explore-query" required maxLength={1000} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Por ejemplo: campanas sintetizadas sin percusión" />
          <label htmlFor="explore-mode">Tipo de búsqueda</label><select id="explore-mode" value={mode} onChange={e=>setMode(e.target.value as typeof mode)}><option value="lexical">Textual · sin consumo API</option><option value="hybrid">Híbrida · consulta OpenAI</option><option value="semantic">Semántica · consulta OpenAI</option></select></>}
        <div className="explore-filters"><label>Álbum<select value={album} onChange={e=>setAlbum(e.target.value)}><option value="">Todos los álbumes</option>{albums.data?.items.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
          <label>Playlist<select value={playlist} onChange={e=>setPlaylist(e.target.value)}><option value="">Toda la biblioteca</option>{playlists.data?.items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label>Máximo de resultados<input type="number" min={1} max={20} step={1} value={limit} required onChange={e=>setLimit(e.target.value)} /></label></div>
        {(albums.error||playlists.error)&&<p className="note">No se pudieron cargar algunos filtros. Puedes consultar toda la biblioteca o volver a abrir esta vista.</p>}
        {((albums.data?.total??0)>100||(playlists.data?.total??0)>100)&&<p className="note">Los selectores muestran las primeras 100 colecciones.</p>}
        <label className="explore-checkbox"><input type="checkbox" checked={explain} onChange={e=>setExplain(e.target.checked)} /> Seleccionar citas con IA</label>
        <p className="note">Textual y similitud por referencia usan el índice guardado. Semántica e híbrida envían tu consulta a OpenAI. La selección de citas envía también extractos de hasta cinco fichas y puede consumir créditos. Nunca se envía audio. No se consulta automáticamente al abrir esta pantalla.</p>
        <button>{referenceId?'Buscar similares':'Buscar en mi música'}</button>
      </fieldset>
      {state.loading&&<button type="button" className="secondary" onClick={()=>controller.current?.cancel()}>Cancelar espera</button>}
    </form>
    <p role="status">{state.loading?'Consultando tu biblioteca…':state.notice||data&&`${data.results.length} candidatos recuperados`||'Prepara una consulta para empezar.'}</p>
    {state.error&&<div role="alert"><p>{state.error}</p><p>Tu biblioteca y el reproductor siguen disponibles. No se repitió la consulta automáticamente.</p></div>}
    {data&&<>
      <h2>{state.request?.track_id?'Candidatos similares':`Resultados de «${state.request?.query.trim()}»`}</h2>
      {data.status==='no_library'&&<div className="empty-state">Tu biblioteca está vacía. Importa música para preparar fichas e índice.</div>}
      {data.status==='no_indexed_tracks'&&<div className="empty-state">No hay fichas con un vector vigente para esta consulta y sus filtros. Puedes preparar fichas desde la biblioteca; la indexación requiere el proveedor habilitado y créditos API.</div>}
      {data.status==='no_matches'&&<div className="empty-state">No se recuperaron candidatos con estas condiciones. Revisa filtros e índice o consulta de nuevo si los datos cambiaron.</div>}
      {data.warnings.map((warning,index)=><p className="note" key={index}>{warning}</p>)}
      {!!data.results.length&&<p className="note">Esta lista corresponde al momento de la consulta. Volver a buscar puede consumir API si eliges un modo que la utiliza. Cambiar de pantalla no detiene la música.</p>}
      <ol className="explore-results">{data.results.map(item=><li key={item.track.id}><article className="explore-result">
        <div className="explore-result-heading"><Cover url={item.track.cover_url} title={item.track.title} /><div><h3>{item.track.title}</h3><p>{artists(item.track)}</p><a href={`/albumes/${item.track.album_id}`} onClick={e=>{e.preventDefault();navigate(`/albumes/${item.track.album_id}`)}}>{item.track.album_title}</a></div>
          <button aria-label={`Reproducir ${item.track.title}`} onClick={()=>player.selectSnapshot(item.track,queue,'Resultados de Explorar')}>Escuchar</button></div>
        <h4>Qué dice su ficha</h4><p className="note">{item.explanation_source==='generated_selection'?'Fragmentos seleccionados por IA y comprobados contra la ficha':'Descripción registrada · alternativa sin generación'} · versión {item.description.version}</p>
        {item.evidence.map((citation,index)=><blockquote key={index}><p>{citation.quote}</p><cite>Ficha de {item.track.title}, versión {citation.version}</cite></blockquote>)}
        <details><summary>Ver ficha, atributos y procedencia</summary><p>Fuente: {sourceLabels[item.description.source]??item.description.source}</p><p>{item.description.text}</p><p>{item.description.source_details}</p>
          <ul>{item.description.features.map((feature,index)=><li key={index}><strong>{featureLabels[feature.name]??feature.name}: {feature.value}</strong><p>{feature.interpretation?'Interpretación subjetiva':'Dato registrado'} · {sourceLabels[feature.source]??feature.source}</p><p>{feature.evidence}</p></li>)}</ul>
          <DescriptionEditor trackId={item.track.id} title={item.track.title} />
        </details>
        <a href={`/explorar?similar=${item.track.id}`} onClick={e=>{e.preventDefault();navigate(`/explorar?similar=${item.track.id}`)}}>Buscar similares a esta pista</a>
      </article></li>)}</ol>
      {data.status!=='ok'&&<a href="/biblioteca" onClick={e=>{e.preventDefault();navigate('/biblioteca')}}>Ir a mi biblioteca</a>}
    </>}
  </section>
}
