/** Preparación local: copia compatible, sin modificar el archivo seleccionado. */
export function fittedSize(width:number,height:number,max=2560){
  if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)throw new Error('Dimensiones no válidas.')
  const scale=Math.min(1,max/Math.max(width,height))
  return {width:Math.max(1,Math.round(width*scale)),height:Math.max(1,Math.round(height*scale))}
}
export async function prepareWallpaper(file:File):Promise<Blob>{
  if(!['image/png','image/jpeg','image/webp'].includes(file.type))throw new Error('Elige una imagen PNG, JPEG o WebP.')
  if(file.size>25*1024*1024)throw new Error('La imagen supera 25 MiB. Elige una copia más ligera.')
  let bitmap:ImageBitmap
  try{bitmap=await createImageBitmap(file,{imageOrientation:'from-image'})}catch{throw new Error('No se pudo abrir la imagen. Comprueba que no esté dañada.')}
  try{
    if(bitmap.width*bitmap.height>48_000_000||Math.max(bitmap.width,bitmap.height)>16384)throw new Error('La imagen supera el límite de preparación de 48 megapíxeles/16384 px. Usa una copia reducida.')
    const size=fittedSize(bitmap.width,bitmap.height)
    const canvas=document.createElement('canvas');canvas.width=size.width;canvas.height=size.height
    const context=canvas.getContext('2d');if(!context)throw new Error('No se pudo preparar el fondo en este navegador.')
    context.fillStyle='#090C20';context.fillRect(0,0,size.width,size.height);context.drawImage(bitmap,0,0,size.width,size.height)
    for(const quality of [.9,.8,.65]){
      const result=await new Promise<Blob|null>(resolve=>canvas.toBlob(resolve,'image/jpeg',quality))
      if(result&&result.size<=5*1024*1024)return result
    }
    throw new Error('No se logró preparar una copia menor de 5 MiB. Elige otra imagen.')
  }finally{bitmap.close()}
}
