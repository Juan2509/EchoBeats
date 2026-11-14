import type { Track } from '../../shared/api/metadata'

export type PreferenceMode = 'off' | 'favorites' | 'discovery'
export type SearchInput = { query: string; mode: 'lexical' | 'semantic' | 'hybrid'; limit: number; explain: boolean; preferences?: PreferenceMode; album_id?: string; playlist_id?: string; track_id?: string }
export type Citation = { source_id: string; version: number; field: 'text'; quote: string }
export type SearchResult = { track: Track; description: { id: string; version: number; text: string; source: string; source_details: string; features: { name: string; value: string; source: string; evidence: string; interpretation: boolean }[] }; evidence: Citation[]; explanation_source: 'recorded' | 'generated_selection'; preference?: { favorite: boolean; base_rank: number; rank: number; reason: string } }
export type SearchResponse = { status: 'ok' | 'no_library' | 'no_indexed_tracks' | 'no_matches'; query: string | null; mode: string; warnings: string[]; results: SearchResult[]; preferences?: { mode: PreferenceMode; policy: string; baseline_order: string[]; result_order: string[]; reordered: boolean } }
export type Gateway = (input: SearchInput, signal: AbortSignal) => Promise<SearchResponse>

export function decode(value: unknown): SearchResponse {
  const data = value as SearchResponse
  if (!data || !['ok','no_library','no_indexed_tracks','no_matches'].includes(data.status) || !Array.isArray(data.results) || data.results.length>20 || !Array.isArray(data.warnings) || data.warnings.some(w=>typeof w!=='string')) throw new Error('Respuesta de exploración no válida.')
  const ids = new Set<string>()
  for (const item of data.results) {
    const track=item?.track, desc=item?.description
    if (!track || typeof track.id!=='string' || !track.id || ids.has(track.id) || typeof track.title!=='string' || track.audio_url!==`/api/v1/tracks/${encodeURIComponent(track.id)}/audio` || !Number.isFinite(track.duration_ms) || track.duration_ms<=0 || !Array.isArray(track.artists) || track.artists.some(a=>!a||typeof a.name!=='string') || typeof track.album_id!=='string' || typeof track.album_title!=='string') throw new Error('La pista recuperada no es válida.')
    ids.add(track.id)
    if (!desc || typeof desc.id!=='string' || !Number.isInteger(desc.version) || desc.version<1 || typeof desc.text!=='string' || typeof desc.source!=='string' || typeof desc.source_details!=='string' || !Array.isArray(desc.features) || desc.features.some(f=>!f||typeof f.name!=='string'||typeof f.value!=='string'||typeof f.evidence!=='string'||typeof f.source!=='string'||typeof f.interpretation!=='boolean')) throw new Error('La ficha recuperada no es válida.')
    if (!['recorded','generated_selection'].includes(item.explanation_source) || !Array.isArray(item.evidence) || !item.evidence.length || item.evidence.some(c=>!c||c.source_id!==desc.id||c.version!==desc.version||c.field!=='text'||typeof c.quote!=='string'||!c.quote||!desc.text.includes(c.quote))) throw new Error('La evidencia no corresponde a la ficha recuperada.')
  }
  if ((data.status==='ok') !== (data.results.length>0)) throw new Error('Estado de resultados incoherente.')
  const prefs=data.preferences
  if(prefs){
    const order=data.results.map(item=>item.track.id)
    if(!['off','favorites','discovery'].includes(prefs.mode)||prefs.policy!=='adjacent_pairs_v1'||!Array.isArray(prefs.baseline_order)||!Array.isArray(prefs.result_order)||prefs.baseline_order.length!==order.length||new Set(prefs.baseline_order).size!==order.length||prefs.baseline_order.some(id=>!ids.has(id))||JSON.stringify(prefs.result_order)!==JSON.stringify(order)||typeof prefs.reordered!=='boolean'||prefs.reordered!==(JSON.stringify(prefs.baseline_order)!==JSON.stringify(order)))throw new Error('Comparación de preferencias no válida.')
    data.results.forEach((item,index)=>{
      const p=item.preference
      if(!p||typeof p.favorite!=='boolean'||p.rank!==index+1||p.base_rank!==prefs.baseline_order.indexOf(item.track.id)+1||typeof p.reason!=='string'||!p.reason||p.reason.length>300||prefs.mode==='favorites'&&Math.abs(p.rank-p.base_rank)>1||prefs.mode!=='favorites'&&p.rank!==p.base_rank||prefs.mode==='discovery'&&p.favorite)throw new Error('Señal de preferencia no válida.')
    })
  }else if(data.results.some(item=>item.preference))throw new Error('Falta la comparación de preferencias.')
  return data
}

export const requestSearch: Gateway = async (input,signal) => {
  const body = input.track_id ? { track_id:input.track_id,limit:input.limit,explain:input.explain,preferences:input.preferences??'off',album_id:input.album_id,playlist_id:input.playlist_id } : { query:input.query.trim(),mode:input.mode,limit:input.limit,explain:input.explain,preferences:input.preferences??'off',album_id:input.album_id,playlist_id:input.playlist_id }
  const response=await fetch(`/api/v1/explore/${input.track_id?'similar':'search'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal,cache:'no-store'})
  const value=await response.json()
  if(!response.ok)throw new Error(value.error?.message??'No se pudo completar la exploración.')
  return decode(value)
}

export class ExploreController {
  state={ loading:false,data:null as SearchResponse|null,error:'',notice:'',request:null as SearchInput|null }
  private alive=true
  private generation=0
  private pending:AbortController|null=null
  private listeners=new Set<()=>void>()
  private gateway:Gateway
  constructor(gateway:Gateway=requestSearch){this.gateway=gateway}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener)}}
  private update(changes:Partial<typeof this.state>){if(this.alive){this.state={...this.state,...changes};this.listeners.forEach(f=>f())}}
  async search(input:SearchInput){
    if(!this.alive)return
    this.pending?.abort();const abort=new AbortController();this.pending=abort;const token=++this.generation
    const request=structuredClone(input)
    if(!request.track_id&&(!request.query.trim()||request.query.trim().length>1000)){this.update({loading:false,data:null,error:'Escribe una consulta de 1 a 1000 caracteres.',notice:''});return}
    this.update({loading:true,data:null,error:'',notice:'',request})
    const timeout=setTimeout(()=>abort.abort(),55000)
    try{
      const data=await this.gateway(request,abort.signal)
      if(!this.alive||token!==this.generation)return
      if(abort.signal.aborted)throw new Error('No se pudo confirmar la respuesta. La solicitud ya enviada podría consumir créditos; no se reintentó.')
      this.update({data:decode(data),loading:false})
    }catch(cause){if(this.alive&&token===this.generation)this.update({loading:false,error:cause instanceof Error&&!(cause instanceof TypeError)&&!(cause instanceof SyntaxError)&&cause.name!=='AbortError'?cause.message:'No se pudo confirmar la exploración. Comprueba la conexión antes de volver a consultar; no se reintentó.'})}
    finally{clearTimeout(timeout)}
  }
  cancel(){this.generation++;this.pending?.abort();this.update({loading:false,data:null,error:'',notice:'Se canceló la espera. Una solicitud ya enviada puede completarse y consumir créditos.'})}
  dispose(){this.alive=false;this.generation++;this.pending?.abort();this.listeners.clear()}
}
