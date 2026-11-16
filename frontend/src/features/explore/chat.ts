import type {Track} from '../../shared/api/metadata'
export type Message={role:'user'|'assistant';content:string}
export type Recommendation={track:Track;reason:string;evidence:{source_id:string;version:number;quote:string}[]}
export type ChatReply={reply:string;mode:'local'|'ai';recommendations:Recommendation[];warnings:string[];context:{favorites:number;recent:number;current:string|null}}
export type ChatTurn={question:string;answer?:ChatReply;error?:string}
export function decodeChat(value:unknown):ChatReply{
  const d=value as ChatReply
  if(!d||typeof d.reply!=='string'||!d.reply||d.reply.length>2000||!['local','ai'].includes(d.mode)||!Array.isArray(d.recommendations)||d.recommendations.length>20||!Array.isArray(d.warnings)||d.warnings.some(w=>typeof w!=='string')||!d.context||!Number.isInteger(d.context.favorites)||!Number.isInteger(d.context.recent))throw Error('Respuesta de conversación no válida.')
  const ids=new Set<string>()
  for(const r of d.recommendations){const t=r?.track;if(!t||typeof t.id!=='string'||ids.has(t.id)||typeof t.title!=='string'||t.audio_url!==`/api/v1/tracks/${encodeURIComponent(t.id)}/audio`||!Number.isFinite(t.duration_ms)||t.duration_ms<=0||!Array.isArray(t.artists)||t.artists.some(a=>typeof a.name!=='string')||typeof t.album_id!=='string'||typeof t.album_title!=='string'||typeof r.reason!=='string'||!Array.isArray(r.evidence)||r.evidence.some(e=>typeof e.quote!=='string'||typeof e.source_id!=='string'||!Number.isInteger(e.version)))throw Error('La recomendación recibida no es válida.');ids.add(t.id)}
  return d
}
export function conversationMessages(turns:ChatTurn[],question:string):Message[]{return [...turns.filter(t=>t.answer).slice(-2).flatMap(t=>[{role:'user' as const,content:t.question},{role:'assistant' as const,content:t.answer!.reply.slice(0,1000)}]),{role:'user' as const,content:question.trim()}]}
