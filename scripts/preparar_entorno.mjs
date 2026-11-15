/** Alternativa Node al preparador Python; nunca sobrescribe ni imprime secretos. */
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { randomBytes } from 'node:crypto'
import { resolve, join } from 'node:path'
import { fileURLToPath } from 'node:url'

export function prepare(root) {
  const destination=join(root,'.env')
  if(existsSync(destination))return false
  const template=readFileSync(join(root,'.env.example'),'utf8')
  if(!/^POSTGRES_PASSWORD=\r?$/m.test(template))throw new Error('La plantilla debe contener POSTGRES_PASSWORD vacío.')
  const content=template.replace(/^POSTGRES_PASSWORD=\r?$/m,'POSTGRES_PASSWORD='+randomBytes(32).toString('hex'))
  try{writeFileSync(destination,content,{encoding:'utf8',flag:'wx',mode:0o600});return true}
  catch(error){if(error.code==='EEXIST')return false;throw error}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const root=fileURLToPath(new URL('..',import.meta.url))
  process.stdout.write(prepare(root)?'.env creado; no se muestra su contenido.\n':'Se conserva el .env existente.\n')
}
