import test from 'node:test'
import assert from 'node:assert/strict'
import {resizeWithinWall,resizeHandles} from '../src/features/walls/resize.ts'
import {WallController} from '../src/features/walls/controller.ts'
import type {WallElement,WallResult} from '../src/features/walls/controller.ts'
const item:WallElement={id:'image',asset_id:'asset',kind:'image',cx:.5,cy:.5,width:.2,height:.2,rotation_deg:0,z_index:2,content_url:'/image'}
const near=(a:number,b:number)=>assert.ok(Math.abs(a-b)<1e-7,`${a} ≠ ${b}`)
function anchor(v:WallElement,handle:string){const sx=handle.includes('e')?1:handle.includes('w')?-1:0,sy=handle.includes('s')?1:handle.includes('n')?-1:0,a=v.rotation_deg*Math.PI/180;return [v.cx*1000-v.width*1000*sx/2*Math.cos(a)+v.height*700*sy/2*Math.sin(a),v.cy*700-v.width*1000*sx/2*Math.sin(a)-v.height*700*sy/2*Math.cos(a)]}
function inside(v:WallElement){const a=v.rotation_deg*Math.PI/180,bx=(Math.abs(v.width*1000*Math.cos(a))+Math.abs(v.height*700*Math.sin(a)))/2,by=(Math.abs(v.width*1000*Math.sin(a))+Math.abs(v.height*700*Math.cos(a)))/2;assert.ok(v.cx*1000>=bx-1e-7&&v.cx*1000<=1000-bx+1e-7);assert.ok(v.cy*700>=by-1e-7&&v.cy*700<=700-by+1e-7);assert.ok(v.width>=.03-1e-8&&v.width<=.6+1e-8&&v.height>=.03-1e-8&&v.height<=.6+1e-8)}
test('ocho tiradores conservan ancla opuesta y límites incluso con giro y Shift',()=>{
 for(const rotation_deg of [-135,-90,-30,0,30,90,145])for(const handle of resizeHandles)for(const proportional of [false,true])for(const [dx,dy] of [[40,60],[-40,-60],[5000,5000],[-5000,-5000]]){
  const original={...item,rotation_deg},v=resizeWithinWall(original,handle,dx,dy,proportional),before=anchor(original,handle),after=anchor(v,handle);near(before[0],after[0]);near(before[1],after[1]);inside(v);assert.equal(v.rotation_deg,rotation_deg);assert.equal(v.asset_id,item.asset_id);if(proportional)near(v.width/v.height,item.width/item.height)
 }
})
test('laterales cambian solo su eje sin Shift y esquina libre permite deformar',()=>{
 const east=resizeWithinWall(item,'e',50,60,false);near(east.width,.25);near(east.height,.2);near(east.cx,.525);near(east.cy,.5)
 const north=resizeWithinWall(item,'n',50,-35,false);near(north.width,.2);near(north.height,.25);near(north.cy,.475)
 const corner=resizeWithinWall(item,'se',50,10,false);assert.notEqual(corner.width/corner.height,item.width/item.height)
 assert.equal(resizeWithinWall(item,'se',0,0,false),item);assert.equal(resizeWithinWall(item,'se',NaN,5,true),item)
})
test('Shift preserva relación original no cuadrada y el cursor usa ejes de la imagen girada',()=>{
 const v={...item,width:.3,height:.1,rotation_deg:90};const a=resizeWithinWall(v,'e',0,50,false);near(a.width,.35);near(a.height,.1)
 for(const handle of resizeHandles){const n=resizeWithinWall(v,handle,100,-80,true);near(n.width/n.height,3);inside(n)}
})
test('redimensionado por gesto no guarda hasta soltar, cancela y persiste sin perder el recurso',async()=>{
 let writes=0,stored:WallResult={wall:{id:'wall',album_id:'album',schema_version:1,revision:1,background_color:'#242038',updated_at:'',elements:[item]},etag:'1'}
 const c=new WallController('album',async(_id,_signal,write)=>{if(write){writes++;stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/image'}))},etag:String(writes+1)}}return stored},undefined,{autosaveMs:5})
 await c.load();c.resizeGesture('image','se',50,50,true);assert.deepEqual(c.state.elements[0],item);await c.toggleEditing();c.beginMove('image');c.resizeGesture('other','se',50,50,true);assert.deepEqual(c.state.elements[0],item);c.resizeGesture('image','se',50,50,true);await new Promise(r=>setTimeout(r,20));assert.equal(writes,0);c.cancelMove();assert.deepEqual(c.state.elements[0],item)
 c.beginMove('image');c.resizeGesture('image','e',50,0,false);c.finishMove();await c.save();assert.equal(writes,1);await c.load();near(c.state.elements[0].width,.25);near(c.state.elements[0].height,.2);assert.equal(c.state.elements[0].asset_id,'asset');c.dispose()
})
