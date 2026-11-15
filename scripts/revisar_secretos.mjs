/** Auditoría local acotada: nunca imprime contenidos ni claves encontradas. */
import { readFileSync, readdirSync, existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { execFileSync, spawnSync } from 'node:child_process'
import { resolve, relative, join, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

export function containsSecret(content, privateKey='') {
  return Boolean(privateKey && content.includes(privateKey)) || /\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}/.test(content) || /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(content)
}

function walk(folder) {
  if (!existsSync(folder)) return []
  return readdirSync(folder,{withFileTypes:true}).flatMap(entry=>entry.isSymbolicLink()?[]:entry.isDirectory()?walk(join(folder,entry.name)):[join(folder,entry.name)])
}

export function audit(root, docker) {
  const tracked=execFileSync('git',['ls-files','-z'],{cwd:root,encoding:'utf8'}).split('\0').filter(Boolean)
  const working=execFileSync('git',['ls-files','-z','--cached','--others','--exclude-standard'],{cwd:root,encoding:'utf8'}).split('\0').filter(Boolean)
  const env=existsSync(join(root,'.env'))?readFileSync(join(root,'.env'),'utf8'):''
  function privateValue(name){
    let value=process.env[name] || new RegExp('^\\s*'+name+'\\s*=\\s*(.*)$','m').exec(env)?.[1]?.trim() || ''
    if ((value.startsWith('"')&&value.endsWith('"'))||(value.startsWith("'")&&value.endsWith("'")))value=value.slice(1,-1)
    return value
  }
  const secretFields=['OPENAI_API_KEY','POSTGRES_PASSWORD','DATABASE_URL']
  const secrets=secretFields.map(privateValue).filter(Boolean)
  const key=privateValue('OPENAI_API_KEY')
  const detected=content=>containsSecret(content)||secrets.some(secret=>containsSecret(content,secret))
  const files=[...new Set([...working.map(name=>resolve(root,name)),...walk(join(root,'frontend','dist'))])]
  const suspicious=[]
  for(const file of files){
    if(existsSync(file)&&detected(readFileSync(file).toString('utf8')))suspicious.push(relative(root,file).split(sep).join('/'))
  }
  const privatePaths=tracked.filter(name=>/(^|\/)\.env(?:\..*)?$/.test(name)&&!name.endsWith('.env.example')||/^(data|backups|postgres_data)\//.test(name))
  const history=execFileSync('git',['log','--all','--format=%H','--','.env','.env.local','.env.production'],{cwd:root,encoding:'utf8'}).trim()
  let logs={checked:false,secret_detected:false,scope:'últimas 2000 líneas del backend'}
  if(docker){
    const result=spawnSync(docker,['compose','logs','--no-color','--tail','2000','backend'],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024,windowsHide:true})
    if(result.status===0)logs={...logs,checked:true,secret_detected:detected((result.stdout??'')+(result.stderr??''))}
  }
  return {private_key_configured:!!key,checked_secret_fields:secretFields.filter(name=>!!privateValue(name)),scanned_files:files.length,suspicious_files:suspicious,tracked_private_paths:privatePaths,
    env_history_commits:history?history.split('\n').length:0,logs,
    limits:'Árbol de trabajo no ignorado y dist actual: valores actuales de tres campos privados, patrones OpenAI/PEM. Historial solo de .env/.env.local/.env.production, no todos los blobs históricos. Logs acotados, sin certificar fuentes no examinadas.'}
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const root=resolve(fileURLToPath(new URL('..',import.meta.url)))
  const option=name=>{const i=process.argv.indexOf(name);return i<0?undefined:process.argv[i+1]}
  const result=audit(root,option('--docker'))
  const output=option('--output')
  if(output){const path=resolve(root,output);if(!path.startsWith(root+sep))throw new Error('Salida fuera del proyecto');mkdirSync(resolve(path,'..'),{recursive:true});writeFileSync(path,JSON.stringify(result,null,2)+'\n')}
  process.stdout.write(JSON.stringify(result)+'\n')
  if(result.suspicious_files.length||result.tracked_private_paths.length||result.env_history_commits||result.logs.secret_detected)process.exitCode=1
}
