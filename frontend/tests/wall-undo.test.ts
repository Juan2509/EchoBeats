import test from 'node:test'
import assert from 'node:assert/strict'
import {WallController,WallRequestError,isDirty} from '../src/features/walls/controller.ts'
import type {WallElement,WallResult,WallGateway} from '../src/features/walls/controller.ts'
const item:WallElement={id:'image',asset_id:'asset',kind:'image',cx:.5,cy:.5,width:.2,height:.2,rotation_deg:0,z_index:0,content_url:'/image'}
const initial=():WallResult=>({wall:{id:'wall',album_id:'album',schema_version:1,revision:1,background_color:'#242038',updated_at:'',elements:[{...item}]},etag:'1'})
function store(){let stored=initial();const gateway:WallGateway=async(_id,_signal,write)=>{if(write)stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/image'}))},etag:String(Number(stored.etag)+1)};return stored};return gateway}
test('rehacer recupera posición/giro/tamaño en orden y se conserva tras guardar',async()=>{
 const c=new WallController('album',store());await c.load();await c.toggleEditing();c.nudge('image',.03,0);const moved={...c.state.elements[0]};c.transform('image',{rotation_deg:35});const rotated={...c.state.elements[0]};c.beginMove('image');c.resizeGesture('image','se',30,20,true);c.finishMove();const resized={...c.state.elements[0]};c.undo();c.undo();c.undo();assert.deepEqual(c.state.elements[0],item);await c.save();assert.equal(c.canRedo,true);c.redo();assert.deepEqual(c.state.elements[0],moved);c.redo();assert.deepEqual(c.state.elements[0],rotated);c.redo();assert.deepEqual(c.state.elements[0],resized);assert.equal(c.canRedo,false);assert.equal(c.redo(),false);c.undo();assert.deepEqual(c.state.elements[0],rotated);c.dispose()
})
test('nuevo cambio geométrico descarta rehacer; clic o gesto cancelado no lo descarta',async()=>{
 const c=new WallController('album',store());await c.load();await c.toggleEditing();c.nudge('image',.02,0);c.undo();c.beginMove('image');assert.equal(c.redo(),false);c.finishMove();assert.equal(c.canRedo,true);c.beginMove('image');c.move('image',.7,.5);c.cancelMove();assert.equal(c.canRedo,true);c.nudge('image',0,.02);assert.equal(c.canRedo,false);c.undo();assert.equal(c.canRedo,true);await c.save();await c.load();await c.toggleEditing();assert.equal(c.canRedo,false);c.dispose()
})
test('rehacer durante guardado en vuelo conserva borrador y persiste después sin perder revisión',async()=>{
 let stored=initial(),release!:()=>void,writes=0
 const c=new WallController('album',async(_id,_signal,write)=>{if(write){if(++writes===1)await new Promise<void>(r=>{release=r});stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/image'}))},etag:String(writes+1)}}return stored},undefined,{autosaveMs:60000})
 await c.load();await c.toggleEditing();c.nudge('image',.04,0);c.undo();c.transform('image',{rotation_deg:10});c.transform('image',{rotation_deg:20});c.undo();const saving=c.save();assert.equal(c.redo(),true);release();await saving;assert.equal(c.state.elements[0].rotation_deg,20);await c.save();assert.equal(stored.wall.elements[0].rotation_deg,20);c.dispose()
})
test('un arrastre completo es una entrada; deshacer mantiene recurso, apariencia y capa actuales',async()=>{
 const c=new WallController('album',store());await c.load();await c.toggleEditing();c.beginMove('image');for(let i=1;i<=10;i++)c.move('image',.5+i*.01,.5);c.finishMove();c.setKind('image','sticker');assert.equal(c.canUndo,true);assert.equal(c.undo(),true);assert.deepEqual(c.state.elements[0],{...item,kind:'sticker'});assert.equal(c.canUndo,false);assert.equal(c.undo(),false);c.dispose()
})
test('posición, giro y tamaño se deshacen por pasos; Ctrl+Z durante gesto solo cancela ese gesto',async()=>{
 const c=new WallController('album',store());await c.load();await c.toggleEditing();c.nudge('image',.02,0);const moved={...c.state.elements[0]};c.beginMove('image');c.rotateGesture('image',35);c.finishMove();const rotated={...c.state.elements[0]};c.beginMove('image');c.resizeGesture('image','se',30,20,true);c.finishMove();assert.equal(c.undo(),true);assert.deepEqual(c.state.elements[0],rotated);assert.equal(c.undo(),true);assert.deepEqual(c.state.elements[0],moved)
 c.beginMove('image');c.move('image',.7,.6);assert.equal(c.undo(),true);assert.equal(c.state.moving,false);assert.deepEqual(c.state.elements[0],moved);assert.equal(c.undo(),true);assert.deepEqual(c.state.elements[0],item);c.dispose()
})
test('undo sobre autoguardado en vuelo no se pierde y se persiste con la siguiente revisión',async()=>{
 let stored=initial(),release!:()=>void,writes=0
 const c=new WallController('album',async(_id,_signal,write)=>{if(write){if(++writes===1)await new Promise<void>(r=>{release=r});stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/image'}))},etag:String(writes+1)}}return stored},undefined,{autosaveMs:60000})
 await c.load();await c.toggleEditing();c.nudge('image',.05,0);const saving=c.save();assert.equal(c.state.saving,true);assert.equal(c.undo(),true);release();await saving;assert.deepEqual(c.state.elements[0],item);assert.equal(isDirty(c.state),true);await c.save();assert.equal(writes,2);assert.deepEqual(stored.wall.elements[0],item);assert.equal(isDirty(c.state),false);c.dispose()
})
test('historial acotado, sin entradas por clic/cancelación; recarga y bloqueo protegen undo',async()=>{
 const c=new WallController('album',store());await c.load();assert.equal(c.undo(),false);await c.toggleEditing();c.beginMove('image');c.finishMove();assert.equal(c.canUndo,false);c.beginMove('image');c.move('image',.6,.5);c.cancelMove();assert.equal(c.canUndo,false)
 for(let i=0;i<60;i++)c.nudge('image',i%2?.001:-.001,0);let count=0;while(c.undo())count++;assert.equal(count,50);c.nudge('image',.01,0);await c.save();assert.equal(c.canUndo,true);await c.toggleEditing();assert.equal(c.undo(),false);await c.load();await c.toggleEditing();assert.equal(c.canUndo,false);c.dispose()
})
test('conflicto bloquea deshacer hasta recargar; historial no resucita imágenes quitadas',async()=>{
 const c=new WallController('album',async(_id,_signal,write)=>{if(write)throw new WallRequestError('conflicto',412);return initial()});await c.load();await c.toggleEditing();c.nudge('image',.01,0);await c.save();assert.equal(c.state.needsReload,true);assert.equal(c.undo(),false);await c.load();await c.toggleEditing();c.nudge('image',.01,0);c.remove('image');assert.equal(c.undo(),false);assert.deepEqual(c.state.elements,[]);c.dispose()
})
