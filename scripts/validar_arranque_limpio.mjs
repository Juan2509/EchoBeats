/** P28: contenedores nuevos, sin usar .env/BD/medios personales ni consumir IA. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { randomBytes, createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:net'
import { resolve, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { prepare } from './preparar_entorno.mjs'

const root=fileURLToPath(new URL('..',import.meta.url))
const position=process.argv.indexOf('--docker')
const docker=position<0?'docker':process.argv[position+1]
const project='echobeats_p28_'+randomBytes(4).toString('hex')
if(!/^echobeats_p28_[a-f0-9]{8}$/.test(project))throw new Error('Proyecto no aislado')
const directory=join(root,'data',project)
mkdirSync(directory,{recursive:true})
const file=join(directory,'compose.json'), env=join(directory,'.env'), reportFile=join(directory,'resultado.json')
const report={project,directory,scope:'BD/medios vacíos y contenedores nuevos; capas Docker pueden usar caché',stages:[],openai_calls:0}
const persist=()=>writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n')
function run(args,stage){
  process.stdout.write('P28: '+stage+'\n')
  const result=spawnSync(docker,args,{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024,windowsHide:true})
  report.stages.push({stage,exit_code:result.status});persist()
  if(result.status!==0)throw new Error('Falló '+stage+'; salida Docker omitida para no revelar configuración. Revisar el proyecto aislado.')
  return result.stdout
}
const compose=(args,stage)=>run(['compose','--project-name',project,'--env-file',env,'--file',file,...args],stage)
const availablePort=()=>new Promise((yes,no)=>{const server=createServer();server.once('error',no);server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close(()=>yes(port))})})
function check(value,message){if(!value)throw new Error(message)}
async function request(path,options={}){
  report.last_request=path.split('?')[0]
  // Las etapas Docker síncronas pueden superar el keep-alive del servidor.
  const response=await fetch(report.backend_url+path,{...options,headers:{Connection:'close',...options.headers},signal:AbortSignal.timeout(20000)})
  check(response.ok,'HTTP no satisfactorio en el entorno aislado: '+path.split('?')[0])
  return response
}
let prepared=false
try{
  const backendPort=await availablePort();let frontendPort=await availablePort()
  while(frontendPort===backendPort)frontendPort=await availablePort()
  report.backend_url='http://127.0.0.1:'+backendPort;report.frontend_url='http://127.0.0.1:'+frontendPort
  const template=readFileSync(join(root,'.env.example'),'utf8')
    .replace(/^POSTGRES_DB=.*$/m,'POSTGRES_DB=echobeats_demo')
    .replace(/^POSTGRES_USER=.*$/m,'POSTGRES_USER=echobeats_demo')
    .replace(/^POSTGRES_HOST=.*$/m,'POSTGRES_HOST=postgres')
    .replace(/^POSTGRES_PORT=.*$/m,'POSTGRES_PORT=5432')
    .replace(/^MEDIA_ROOT=.*$/m,'MEDIA_ROOT=/app/data/media')
    .replace(/^AI_ENABLED=.*$/m,'AI_ENABLED=false')
    .replace(/^OPENAI_API_KEY=.*$/m,'OPENAI_API_KEY=')
    .replace(/^DATABASE_URL=.*$/m,'DATABASE_URL=')
    .replace(/^ALLOWED_ORIGINS=.*$/m,`ALLOWED_ORIGINS=${report.backend_url},${report.frontend_url},http://localhost:${backendPort},http://localhost:${frontendPort}`)
  writeFileSync(join(directory,'.env.example'),template,{flag:'wx'})
  check(prepare(directory),'No se creó configuración aislada')
  const before=createHash('sha256').update(readFileSync(env)).digest('hex')
  check(prepare(directory)===false&&createHash('sha256').update(readFileSync(env)).digest('hex')===before,'El preparador no conservó un archivo existente')
  report.env_preserved=true
  const backend={build:{context:root,dockerfile:'backend/Dockerfile'},env_file:[env],
    volumes:[{type:'bind',source:join(directory,'appdata'),target:'/app/data'}]}
  mkdirSync(join(directory,'appdata'),{recursive:true})
  const config={name:project,services:{
    postgres:{image:'pgvector/pgvector:pg17@sha256:7d0a41464797aeb9862dfdc0bbf1526b82cfd324cdd8036df19e3545f4a9ccb8',env_file:[env],volumes:['postgres_data:/var/lib/postgresql/data'],
      healthcheck:{test:['CMD-SHELL','pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'],interval:'3s',timeout:'3s',retries:20}},
    migrate:{...backend,depends_on:{postgres:{condition:'service_healthy'}},command:['python','-m','alembic','upgrade','head']},
    backend:{...backend,depends_on:{migrate:{condition:'service_completed_successfully'}},ports:[`127.0.0.1:${backendPort}:8000`],
      command:['python','-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000'],
      healthcheck:{test:['CMD','python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/ready',timeout=8)"],interval:'3s',timeout:'10s',retries:20}},
    frontend:{build:{context:root,dockerfile:'frontend/Dockerfile'},environment:{API_PROXY_TARGET:'http://backend:8000'},ports:[`127.0.0.1:${frontendPort}:5173`],depends_on:{backend:{condition:'service_healthy'}}}
  },volumes:{postgres_data:{}}}
  writeFileSync(file,JSON.stringify(config,null,2)+'\n',{flag:'wx'})
  prepared=true;persist()
  compose(['config','--quiet'],'validar configuración')
  compose(['build'],'construir desde Dockerfiles/locks')
  compose(['up','-d','--wait'],'arrancar con almacenamiento vacío')
  const ready=await (await request('/api/v1/ready')).json();check(ready.status==='ready','Dependencias no listas')
  const page=await (await request('/api/v1/tracks')).json();check(page.total===0,'La biblioteca no estaba vacía')
  const ai=await (await request('/api/v1/ai/status')).json()
  check(ai.enabled===false,'La IA no está desactivada')
  const revision=compose(['exec','-T','backend','python','-m','alembic','current'],'verificar migración')
  check(revision.includes('0009_favorites'),'Revisión inesperada')
  compose(['exec','-T','backend','python','-m','pip','check'],'verificar dependencias Python')
  compose(['exec','-T','backend','python','-m','alembic','check'],'comparar modelo y esquema')
  compose(['exec','-T','frontend','npm','run','build'],'build frontend en contenedor')
  const tests=compose(['exec','-T','frontend','npm','test'],'pruebas frontend en contenedor')
  const total=Number(/\btests\s+(\d+)/.exec(tests)?.[1])
  const passed=Number(/\bpass\s+(\d+)/.exec(tests)?.[1])
  const failed=Number(/\bfail\s+(\d+)/.exec(tests)?.[1])
  check(total>0&&total===passed&&failed===0,'El informe frontend no acredita todas las pruebas aprobadas')
  report.frontend_tests=passed
  const payload=readFileSync(join(root,'pruebas','coleccion','sin_etiquetas.mp3'))
  const form=new FormData();form.append('files',new Blob([payload],{type:'audio/mpeg'}),'sin_etiquetas.mp3')
  const imported=await (await request('/api/v1/imports',{method:'POST',headers:{Origin:report.frontend_url},body:form})).json()
  check(imported.results[0].status==='imported','No se importó fixture')
  const id=imported.results[0].track_id
  const audio=await request(`/api/v1/tracks/${id}/audio`,{headers:{Range:'bytes=100-199'}})
  check(audio.status===206&&Buffer.from(await audio.arrayBuffer()).equals(payload.subarray(100,200)),'Rango distinto del original')
  report.last_request='frontend proxy /api/v1/health'
  const front=await fetch(report.frontend_url+'/api/v1/health',{headers:{Connection:'close'},signal:AbortSignal.timeout(15000)})
  check(front.ok&&(await front.json()).status==='ok','Proxy frontend no disponible')
  compose(['up','-d','--no-deps','--force-recreate','backend'],'recrear contenedor backend aislado')
  compose(['up','-d','--wait'],'esperar tras reinicio')
  const reopened=await (await request(`/api/v1/tracks/${id}`)).json()
  check(reopened.id===id,'Importación no persistente')
  const restoredAudio=await request(`/api/v1/tracks/${id}/audio`)
  check(Buffer.from(await restoredAudio.arrayBuffer()).equals(payload),'El medio no sobrevivió a recrear el contenedor')
  report.result='passed';report.ready=ready;report.initial_tracks=0;report.final_tracks=1;report.revision='0009_favorites'
  report.limits='Sin navegador/escucha, sin OpenAI real, sin instalación sin caché ni máquina externa. Datos de demostración conservados.'
}catch(error){report.result='failed';report.error=error.message;report.error_code=error.cause?.code??error.code??error.name;process.exitCode=1}
finally{
  if(prepared){try{compose(['stop'],'detener solo proyecto aislado; conservar datos')}catch{report.stop_failed=true;process.exitCode=1}}
  persist();process.stdout.write(JSON.stringify(report)+'\n')
}
