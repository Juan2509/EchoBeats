import type {Track} from '../../shared/api/metadata'
export type Message={role:'user'|'assistant';content:string}
export type Recommendation={track:Track;reason:string;evidence:{source_id:string;version:number;quote:string}[]}
export type MusicSuggestion={title:string;artist:string|null;work:string|null;match:'direct'|'approximate';reason:string;source_url?:string}
export type ChatReply={reply:string;mode:'local'|'ai';provider?:'openai'|null;recommendations:Recommendation[];suggestions?:MusicSuggestion[];warnings:string[];context:{favorites:number;recent:number;current:string|null}}
export type ChatTurn={question:string;answer?:ChatReply;error?:string}
export function decodeChat(value:unknown):ChatReply{
  const d=value as ChatReply
  if(!d||typeof d.reply!=='string'||!d.reply||d.reply.length>2000||!['local','ai'].includes(d.mode)||!Array.isArray(d.recommendations)||d.recommendations.length>20||!Array.isArray(d.warnings)||d.warnings.some(w=>typeof w!=='string')||!d.context||!Number.isInteger(d.context.favorites)||!Number.isInteger(d.context.recent))throw Error('Respuesta de conversación no válida.')
  const ids=new Set<string>()
  for(const r of d.recommendations){const t=r?.track;if(!t||typeof t.id!=='string'||ids.has(t.id)||typeof t.title!=='string'||t.audio_url!==`/api/v1/tracks/${encodeURIComponent(t.id)}/audio`||!Number.isFinite(t.duration_ms)||t.duration_ms<=0||!Array.isArray(t.artists)||t.artists.some(a=>typeof a.name!=='string')||typeof t.album_id!=='string'||typeof t.album_title!=='string'||typeof r.reason!=='string'||!Array.isArray(r.evidence)||r.evidence.some(e=>typeof e.quote!=='string'||typeof e.source_id!=='string'||!Number.isInteger(e.version)))throw Error('La recomendación recibida no es válida.');ids.add(t.id)}
  if(d.suggestions!==undefined&&(!Array.isArray(d.suggestions)||d.suggestions.length>4||
    d.suggestions.some(item=>!item||!validText(item.title,160)||(item.artist!==null&&!validText(item.artist,160))||(item.work!==null&&!validText(item.work,160))||!['direct','approximate'].includes(item.match)||!validText(item.reason,240)||(item.source_url!==undefined&&!validSource(item.source_url)))))
    throw Error('La sugerencia recibida no es válida.')
  return d
}
function validSource(value:unknown):boolean{
  if(typeof value!=='string')return false
  try{return new URL(value).protocol==='https:'}catch{return false}
}
function validText(value:unknown,max:number):boolean{
  return typeof value==='string'&&!!value.trim()&&Array.from(value).length<=max
}
export function conversationMessages(turns:ChatTurn[],question:string):Message[]{return [...turns.filter(t=>t.answer).slice(-4).flatMap(t=>[{role:'user' as const,content:t.question},{role:'assistant' as const,content:[t.answer!.reply,...(t.answer!.suggestions??[]).map(item=>[item.title,item.artist,item.work].filter(Boolean).join(' — '))].join('\n').slice(0,1000)}]),{role:'user' as const,content:question.trim()}]}
