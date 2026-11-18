import test from 'node:test'
import assert from 'node:assert/strict'
import {decodeChat,conversationMessages} from '../src/features/explore/chat.ts'
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

test('acepta una banda sonora con artista desconocido y afinidad aproximada',()=>{
  const suggestion={title:'Tema de exploración',artist:null,work:'Banda sonora',match:'approximate',reason:'Coincide la textura, cambia el ritmo.'}
  const reply={reply:'Es una opción cercana.',mode:'ai',recommendations:[],suggestions:[suggestion],warnings:[],context:{favorites:0,recent:0,current:null}}
  assert.deepEqual(decodeChat(reply).suggestions,[suggestion])
  assert.throws(()=>decodeChat({...reply,suggestions:[{...suggestion,match:'exact'}]}))
})
