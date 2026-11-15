import test from 'node:test'
import assert from 'node:assert/strict'
import { containsSecret } from '../../scripts/revisar_secretos.mjs'

test('auditoría reconoce clave privada y patrón sin devolver el texto ni incluirlo en el resultado',()=>{
  const synthetic='sk-proj-'+ 'x'.repeat(32)
  assert.equal(containsSecret('contenido normal'),false)
  assert.equal(containsSecret('OPENAI_API_KEY=sin-configurar'),false)
  const result={detected:containsSecret('ejemplo '+synthetic)}
  assert.equal(result.detected,true);assert.equal(JSON.stringify(result).includes(synthetic),false)
  assert.equal(containsSecret('otra-forma-privada','otra-forma-privada'),true)
})
