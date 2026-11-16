import type {WallElement} from './controller'

export const resizeHandles=['nw','n','ne','e','se','s','sw','w'] as const
export type ResizeHandle=typeof resizeHandles[number]
/** Deltas en unidades del muro 1000x700. Ancla la esquina/lado opuesto. */
export function resizeWithinWall(item:WallElement,handle:ResizeHandle,dx:number,dy:number,proportional:boolean):WallElement{
  if(!resizeHandles.includes(handle)||!Number.isFinite(dx)||!Number.isFinite(dy)||(dx===0&&dy===0))return item
  const sx=handle.includes('e')?1:handle.includes('w')?-1:0,sy=handle.includes('s')?1:handle.includes('n')?-1:0
  const a=item.rotation_deg*Math.PI/180,c=Math.cos(a),s=Math.sin(a),x=dx*c+dy*s,y=-dx*s+dy*c
  const w=item.width*1000,h=item.height*700
  let width=sx?w+x*sx:w,height=sy?h+y*sy:h
  if(proportional){
    const fx=width/w,fy=height/h
    const requested=!sx?fy:!sy?fx:Math.abs(fx-1)>=Math.abs(fy-1)?fx:fy
    const scale=Math.max(Math.max(.03/item.width,.03/item.height),Math.min(Math.min(.6/item.width,.6/item.height),requested))
    width=w*scale;height=h*scale
  }else{width=Math.max(30,Math.min(600,width));height=Math.max(21,Math.min(420,height))}
  function at(t:number){const dw=(width-w)*t,dh=(height-h)*t;return {...item,width:(w+dw)/1000,height:(h+dh)/700,cx:item.cx+(dw*sx*c-dh*sy*s)/2000,cy:item.cy+(dw*sx*s+dh*sy*c)/1400}}
  function inside(v:WallElement){const bx=(Math.abs(v.width*1000*c)+Math.abs(v.height*700*s))/2,by=(Math.abs(v.width*1000*s)+Math.abs(v.height*700*c))/2;return v.cx*1000>=bx-1e-8&&v.cx*1000<=1000-bx+1e-8&&v.cy*700>=by-1e-8&&v.cy*700<=700-by+1e-8}
  const wanted=at(1);if(inside(wanted))return wanted
  let low=0,high=1;for(let i=0;i<48;i++){const mid=(low+high)/2;if(inside(at(mid)))low=mid;else high=mid}
  return at(low)
}
