import test from 'node:test'
import assert from 'node:assert/strict'
import {decodeChat,conversationMessages,previousRecommendationIds} from '../src/features/explore/chat.ts'
test('conversación solo incluye cuatro turnos confirmados y el mensaje nuevo, sin fallos ni historial ilimitado',()=>{
  const answer={reply:'Respuesta',mode:'local' as const,recommendations:[],warnings:[],context:{favorites:0,recent:0,current:null}}
  const messages=conversationMessages([{question:'cero',answer},{question:'antes',answer},{question:'uno',answer},{question:'falló',error:'red'},{question:'dos',answer},{question:'tres',answer}],'  menos percusión  ')
  assert.deepEqual(messages.map(m=>m.content),['antes','Respuesta','uno','Respuesta','dos','Respuesta','tres','Respuesta','menos percusión']);assert.equal(messages.at(-1)?.role,'user')
})
test('chat rechaza audios externos y recomendaciones duplicadas; acepta alternativa local vacía',()=>{
  const reply={reply:'Hola',mode:'local',recommendations:[],warnings:[],context:{favorites:0,recent:0,current:null}}
  assert.equal(decodeChat(reply).mode,'local')
  const track={id:'a',title:'Pista',audio_url:'https://externo/audio',duration_ms:1000,artists:[],album_id:'b',album_title:'Disco'}
  assert.throws(()=>decodeChat({...reply,recommendations:[{track,reason:'Guardada',evidence:[]}]}))
  track.audio_url='/api/v1/tracks/a/audio';const item={track,reason:'Guardada',evidence:[]};assert.throws(()=>decodeChat({...reply,recommendations:[item,item]}))
})

test('conserva los IDs de las últimas tarjetas aunque después haya texto o fallos', () => {
  const reply = {reply: 'Respuesta', mode: 'local', warnings: [],
    context: {favorites: 0, recent: 0, current: null}}
  const textOnly = decodeChat({...reply, recommendations: []})
  const withTracks = (...ids: string[]) => decodeChat({...reply, recommendations: ids.map(id => ({
    track: {id, title: 'Pista', audio_url: `/api/v1/tracks/${id}/audio`, duration_ms: 1000,
      artists: [], album_id: 'album', album_title: 'Disco'},
    reason: 'Importada', evidence: [],
  }))})

  const turns = [
    {question: 'Lista anterior', answer: withTracks('a')},
    {question: 'Otras pistas', answer: withTracks('b', 'c')},
    {question: '¿Cuál prefieres?', answer: textOnly},
    {question: 'Siguiente pregunta', error: 'red'},
  ]
  assert.deepEqual(previousRecommendationIds(turns), ['b', 'c'])
  assert.deepEqual(previousRecommendationIds([{question: 'Hola', answer: textOnly}]), [])
})

test('acepta una banda sonora con artista desconocido y afinidad aproximada',()=>{
  const suggestion={title:'Tema de exploración',artist:null,work:'Banda sonora',match:'approximate',reason:'Coincide la textura, cambia el ritmo.'}
  const reply={reply:'Es una opción cercana.',mode:'ai',recommendations:[],suggestions:[suggestion],warnings:[],context:{favorites:0,recent:0,current:null}}
  assert.deepEqual(decodeChat(reply).suggestions,[suggestion])
  assert.throws(()=>decodeChat({...reply,suggestions:[{...suggestion,match:'exact'}]}))
})

test('el seguimiento conserva la elección y el motivo en el turno en que se mostraron', () => {
  const makeAnswer = (title: string, id: string, reason: string) => decodeChat({
    reply: 'Empezaría por esta', mode: 'local', warnings: [], context: {favorites: 0, recent: 0, current: null},
    recommendations: [{track: {id, title, audio_url: `/api/v1/tracks/${id}/audio`, duration_ms: 1000,
      artists: [], album_id: 'album', album_title: 'Disco'}, reason, evidence: []}],
  })
  const first = makeAnswer('Tally Screen', 'a', 'En el comienzo predominan las frecuencias graves.')
  const next = makeAnswer('Exothermic', 'b', 'La marcaste como favorita.')
  const history = conversationMessages([
    {question: '¿Cuál escogerías?', answer: first},
    {question: '¿Qué otra elegirías?', answer: next},
  ], '¿Por qué te gusta más la primera?')
  assert.match(history[1].content, /\[a\] Tally Screen — En el comienzo predominan las frecuencias graves\./)
  assert.match(history[3].content, /\[b\] Exothermic — La marcaste como favorita\./)
  assert.doesNotMatch(history[1].content, /Exothermic|api\/v1/)
})

test('el historial largo respeta el límite y conserva las cinco tarjetas en orden', () => {
  const ids = ['1','2','3','4','5'].map(suffix => `00000000-0000-4000-a000-00000000000${suffix}`)
  const answer = decodeChat({reply:'🎶'.repeat(950), mode:'local', warnings:[], context:{favorites:0,recent:0,current:null},
    recommendations: ids.map(id => ({track:{id, title:'🎵'.repeat(100), audio_url:`/api/v1/tracks/${id}/audio`,
      duration_ms:1000, artists:[], album_id:'album', album_title:'Disco'}, reason:'Graves '.repeat(80), evidence:[]}))})
  const history = conversationMessages([{question:'Mis opciones',answer}], '¿Y la segunda?')[1].content
  assert.ok(Array.from(history).length <= 1000)
  assert.deepEqual([...history.matchAll(/\[([^\]]+)\]/g)].map(match => match[1]), ids)
  assert.ok((history.match(/Graves/g) ?? []).length >= 5)
  assert.ok(history.isWellFormed())
})
