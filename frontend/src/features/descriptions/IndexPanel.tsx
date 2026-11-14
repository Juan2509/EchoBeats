import { useEffect, useRef, useState } from 'react'

type State = { status: string; description_version?: number; job?: { id: string; attempts: number; error_message?: string } | null }
const labels: Record<string,string> = { missing_description:'Sin ficha', incomplete_description:'Ficha incompleta', not_indexed:'Sin indexar', pending:'Pendiente', processing:'Indexando', ready:'Vector vigente', stale:'Desactualizado', error:'Error de indexación' }
export function IndexPanel({ trackId, version, locked }: { trackId: string; version: number; locked: boolean }) {
  const [state,setState]=useState<State|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0)
  const action=useRef<string|null>(null)
  useEffect(()=>{
    let alive=true,timer:ReturnType<typeof setTimeout>|undefined,abort:AbortController|undefined
    const command=action.current;action.current=null
    async function request(path:string,method='GET') {
      abort=new AbortController();const timeout=setTimeout(()=>abort?.abort(),15000)
      try {
        const response=await fetch(`/api/v1${path}`,{method,signal:abort.signal,cache:'no-store'})
        const data=await response.json();if(!response.ok)throw new Error(data.error?.message??'No se pudo consultar la indexación.')
        return data
      }finally{clearTimeout(timeout)}
    }
    async function load(first=false) {
      if(!alive)return
      setBusy(true);setError('')
      try {
        if(first&&command)await request(command,'POST')
        if(!alive)return
        const data=await request(`/tracks/${encodeURIComponent(trackId)}/index-status`)
        if(!alive)return
        if(!Object.hasOwn(labels,data.status))throw new Error('Estado de indexación no válido.')
        setState(data)
        if(['pending','processing'].includes(data.status))timer=setTimeout(()=>void load(),2000)
      }catch(cause){if(alive)setError(cause instanceof Error&&!(cause instanceof TypeError)&&!(cause instanceof SyntaxError)&&cause.name!=='AbortError'?cause.message:'No se pudo confirmar la operación. Actualiza el estado antes de reintentar.')}
      finally{if(alive)setBusy(false)}
    }
    void load(true)
    return()=>{alive=false;abort?.abort();clearTimeout(timer)}
  },[trackId,version,refresh])
  function send(path:string){action.current=path;setRefresh(value=>value+1)}
  return <section aria-label="Indexación de la ficha"><h3>Índice semántico</h3>
    <p role="status">{busy?'Consultando indexación…':state?labels[state.status]:'Sin comprobar'}</p>
    {error&&<p role="alert">{error}</p>}{state?.job?.error_message&&<p>{state.job.error_message}</p>}
    <p className="note">Indexar envía el texto, atributos y evidencias guardados de esta ficha a OpenAI y puede consumir créditos API. No envía audio. Guarda tus cambios antes de indexar.</p>
    <button type="button" disabled={locked||busy||!state||['ready','pending','processing','missing_description','incomplete_description','error'].includes(state.status)} onClick={()=>send(`/tracks/${encodeURIComponent(trackId)}/index-jobs`)}>Indexar ficha guardada</button>
    {state?.status==='error'&&state.job&&<button type="button" className="secondary" disabled={locked||busy||state.job.attempts>=3} onClick={()=>send(`/jobs/${encodeURIComponent(state.job!.id)}/retry`)}>Reintentar indexación</button>}
    <button type="button" className="secondary" disabled={busy} onClick={()=>setRefresh(value=>value+1)}>Actualizar índice</button>
  </section>
}
