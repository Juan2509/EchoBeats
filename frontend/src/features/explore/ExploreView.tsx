import {useEffect,useRef,useState} from 'react'
import {AdvancedExploreView} from './AdvancedExploreView'
import {decodeChat,conversationMessages} from './chat'
import type {ChatTurn} from './chat'
import {usePlayer} from '../player/Player'
import {FavoriteButton} from '../favorites/Favorites'
import {Cover,artists,useRead} from '../library/Library'
import type {Track} from '../../shared/api/metadata'

type ChatMode = 'basic'|'ollama'|'openai'
type ChatAvailability = {local_enabled:boolean;local_ready:boolean;cloud_enabled:boolean;cloud_ready:boolean}

export function ExploreView({search,navigate}:{search:string;navigate:(path:string)=>void}){
  const player=usePlayer(),referenceId=new URLSearchParams(search).get('similar')
  const valid=referenceId&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(referenceId)?referenceId:null
  const reference=useRead<Track>(`/tracks/${valid}`,0,!!valid)
  const [turns,setTurns]=useState<ChatTurn[]>([]),[query,setQuery]=useState(''),[busy,setBusy]=useState(false),[advanced,setAdvanced]=useState(false),[mode,setMode]=useState<ChatMode>('basic'),[availability,setAvailability]=useState<ChatAvailability|null>(null),[statusFailed,setStatusFailed]=useState(false)
  const checking=availability===null&&!statusFailed
  const useAI=mode!=='basic'
  const pending=useRef<AbortController|null>(null),alive=useRef(true),generation=useRef(0),conversation=useRef<HTMLDivElement>(null)
  const running=useRef(false)
  useEffect(()=>{
    alive.current=true
    const controller=new AbortController()
    fetch('/api/v1/explore/chat/status',{signal:controller.signal,cache:'no-store'})
      .then(response=>{if(!response.ok)throw Error();return response.json()})
      .then(status=>{
        if(controller.signal.aborted)return
        setAvailability(status)
        if(status.local_ready===true)setMode('ollama')
      })
      .catch(()=>{if(!controller.signal.aborted)setStatusFailed(true)})
    return()=>{alive.current=false;generation.current++;controller.abort();pending.current?.abort()}
  },[])
  useEffect(()=>{if(turns.length)conversation.current?.lastElementChild?.scrollIntoView({block:'nearest',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})},[turns,busy])
  async function send(text:string){if(checking||running.current||!text.trim()||text.trim().length>1000||referenceId&&!valid)return
    running.current=true
    const ticket=++generation.current,question=text.trim(),messages=conversationMessages(turns,question),abort=new AbortController();pending.current=abort
    setTurns(current=>[...current,{question}].slice(-20));setQuery('');setBusy(true)
    const timer=setTimeout(()=>abort.abort(),130000)
    try{const response=await fetch('/api/v1/explore/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages,current_track_id:player.state.track?.id??null,recent_track_ids:player.state.recentTrackIds,previous_track_ids:turns.filter(t=>t.answer).at(-1)?.answer?.recommendations.map(r=>r.track.id)??[],reference_track_id:valid,use_ai:useAI,provider:mode==='basic'?null:mode}),signal:abort.signal,cache:'no-store'}),data=await response.json()
      if(!response.ok)throw Error(data.error?.message??'No pude responder en el chat.')
      const answer=decodeChat(data);if(alive.current&&ticket===generation.current&&!abort.signal.aborted)setTurns(current=>current.map((t,i)=>i===current.length-1?{...t,answer}:t))
    }catch(cause){if(alive.current&&ticket===generation.current)setTurns(current=>current.map((t,i)=>i===current.length-1?{...t,error:cause instanceof Error&&!(cause instanceof TypeError)&&cause.name!=='AbortError'?cause.message:'No pude confirmar la respuesta. Tu música sigue disponible; no repetí la consulta.'}:t))}
    finally{clearTimeout(timer);if(alive.current&&ticket===generation.current){running.current=false;setBusy(false)}}
  }
  function cancel(){generation.current++;pending.current?.abort();running.current=false;setBusy(false);setTurns(current=>current.map((t,i)=>i===current.length-1?{...t,error:mode==='openai'?'Se canceló la espera. Una solicitud a OpenAI puede completarse y consumir créditos.':'Se canceló la espera.'}:t))}
  return <section className="explore-chat" aria-labelledby="explore-title"><header className="chat-heading"><div><p className="eyebrow">Tu compañía musical</p><h1 id="explore-title">¿Qué te apetece escuchar?</h1><p>Hablemos de música, de lo que te gusta o de lo que tengas en mente.</p></div>{turns.length>0&&<button className="secondary" disabled={busy} onClick={()=>setTurns([])}>Nueva conversación</button>}</header>
    <div className="chat-context">
      <label>Proveedor del chat <select value={mode} disabled={busy||checking} aria-describedby="chat-ai-context" onChange={event=>setMode(event.target.value as ChatMode)}>
        <option value="basic">Modo básico</option>
        <option value="ollama" disabled={!availability?.local_ready}>Ollama · IA local{availability&&!availability.local_ready?' (no disponible)':''}</option>
        <option value="openai" disabled={!availability?.cloud_ready}>OpenAI · API de ChatGPT{availability&&!availability.cloud_ready?' (sin configurar)':''}</option>
      </select></label>
      {player.state.track&&<span>Ahora: {player.state.track.title}</span>}
      <span>Favoritos y {player.state.recentTrackIds.length} reproducciones de esta sesión como referencia</span>
    </div>
    <p id="chat-ai-context" className="note">{checking?'Comprobando proveedores…':statusFailed?'No pude comprobar los proveedores. Puedes usar el modo básico.':mode==='openai'?'Al enviar, OpenAI recibe tu mensaje, el historial reciente de este chat y el contexto musical. Puede consumir créditos.':mode==='ollama'?'Ollama procesa la conversación en este equipo.':'El modo básico responde con ejemplos y búsqueda local.'}</p>
    {referenceId&&<p className="chat-reference">{!valid?'La referencia no es válida.':reference.loading?'Cargando referencia…':reference.error?'No pude cargar la referencia.':`Tomaré como punto de partida «${reference.data?.title}».`} <a href="/explorar" onClick={e=>{e.preventDefault();navigate('/explorar')}}>Quitar referencia</a></p>}
    {!turns.length&&<div className="chat-welcome"><p>Puedes hablarme con tus palabras.</p><div className="chat-suggestions">{['¿Qué distingue al trip hop del downtempo?','Me gustan los discos que cuentan una historia','Recomiéndame algo que aún no conozca'].map(text=><button type="button" className="secondary" key={text} onClick={()=>setQuery(text)}>{text}</button>)}</div><p className="note">Los corazones me orientan. Las reproducciones recientes se usan solo durante esta sesión; no escucho ni envío tus archivos de audio.</p></div>}
    <div ref={conversation} className="chat-conversation" aria-live="polite" aria-busy={busy}>{turns.map((turn,index)=><article className="chat-turn" key={index}><div className="chat-user"><strong>Tú</strong><p>{turn.question}</p></div>{turn.answer&&<div className="chat-assistant"><strong>EchoBeats · {turn.answer.provider==='ollama'?'Ollama':turn.answer.provider==='openai'?'OpenAI':turn.answer.mode==='ai'?'IA':'Modo básico'}</strong><p>{turn.answer.reply}</p>{!!turn.answer.suggestions?.length&&<section aria-label="Sugerencias para explorar"><p className="note">{turn.answer.suggestions.every(item=>item.source_url)?'Referencias con fuente.' : turn.answer.mode==='ai'?'Sugerencias de IA basadas en conocimiento general. EchoBeats no consultó un catálogo externo ni verificó su disponibilidad.':'Ejemplos de EchoBeats incluidos en el modo local.'}</p>{turn.answer.suggestions.every(item=>item.match==='approximate')&&<p>Estas son las opciones más cercanas. Cada una explica dónde encaja y dónde difiere.</p>}<ul>{turn.answer.suggestions.map(item=><li key={JSON.stringify([item.title,item.artist,item.work])}><strong>{[item.title,item.artist,item.work].filter(Boolean).join(' — ')}</strong><p className="note">{item.match==='approximate'?'Opción cercana':'Afinidad con tu petición'}{item.artist===null?' · Artista sin confirmar':''}</p><p>{item.reason}</p>{item.source_url&&<a href={item.source_url} target="_blank" rel="noopener noreferrer">Ver fuente</a>}{!item.source_url&&<a href={`https://www.youtube.com/results?search_query=${encodeURIComponent([item.title,item.artist,item.work].filter(Boolean).join(' '))}`} target="_blank" rel="noopener noreferrer">Buscar en YouTube<span className="visually-hidden"> {item.title}</span></a>}</li>)}</ul></section>}<div className="chat-recommendations">{turn.answer.recommendations.map(item=><article key={item.track.id} className="chat-track"><Cover url={item.track.cover_url} title={item.track.title}/><div><div className="track-title-row"><strong>{item.track.title}</strong><FavoriteButton iconOnly trackId={item.track.id} title={item.track.title}/></div><p>{artists(item.track)}</p><p>{item.reason}</p><button type="button" onClick={()=>player.selectSnapshot(item.track,turn.answer!.recommendations.map(r=>r.track),'Recomendaciones de Explorar')}>Escuchar</button><a href={`/albumes/${item.track.album_id}`} onClick={e=>{e.preventDefault();navigate(`/albumes/${item.track.album_id}`)}}>Abrir álbum</a>{item.evidence.length>0&&<details><summary>Por qué aparece</summary>{item.evidence.map((e,i)=><blockquote key={i}>{e.quote}<small>Ficha v{e.version}</small></blockquote>)}</details>}</div></article>)}</div>{turn.answer.warnings.length>0&&<div className="chat-notices">{turn.answer.warnings.map((warning,i)=><p key={i}>{warning}</p>)}</div>}</div>}{turn.error&&<p role="alert">{turn.error}</p>}</article>)}</div>
    {busy&&<p className="note" role="status">{useAI?'Esperando la respuesta de la IA…':'Buscando una respuesta local…'}</p>}
    <form className="chat-composer" onSubmit={event=>{event.preventDefault();void send(query)}}><label htmlFor="music-chat-message">Habla con EchoBeats</label><div><textarea id="music-chat-message" maxLength={1000} required rows={2} placeholder="Algo tranquilo para esta tarde…" value={query} disabled={busy} onChange={event=>setQuery(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.nativeEvent.isComposing){event.preventDefault();if(query.trim())void send(query)}}}/>{busy?<button type="button" className="secondary" onClick={cancel}>Cancelar espera</button>:<button disabled={checking||!query.trim()||!!referenceId&&(!valid||reference.loading||!!reference.error)}>Enviar</button>}</div><small>Enter para enviar · Shift+Enter para otra línea</small></form>
    <details className="chat-options"><summary>Opciones</summary>{(availability&&!availability.cloud_ready)&&<p>Para habilitar la charla con IA, configura AI_ENABLED y OPENAI_API_KEY en el servidor.</p>}<p>No hay historial permanente ni aprendizaje automático de tus gustos. Las recomendaciones pueden no coincidir con lo que buscas.</p><button type="button" className="secondary" disabled={busy||!player.state.recentTrackIds.length} onClick={()=>player.control()?.clearRecent()}>Olvidar reproducciones recientes</button><button type="button" className="secondary" disabled={busy} onClick={()=>setAdvanced(value=>!value)}>{advanced?'Cerrar búsqueda avanzada':'Búsqueda avanzada'}</button></details>
    {advanced&&<div className="chat-advanced"><AdvancedExploreView search={search} navigate={navigate}/></div>}
  </section>
}
