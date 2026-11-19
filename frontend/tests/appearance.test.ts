import test from 'node:test'
import assert from 'node:assert/strict'
import {defaults,presets,decodeAppearance,cssVariables,assetUrl,backgroundFor,replaceBackground,wallSurfaceFor,decodeWallpaper,replaceWallBackground,presentationFor,removeCustomBackground,stickerOutlineFor,changeStickerOutline,defaultStickerOutline} from '../src/features/appearance/theme.ts'
import {fittedSize} from '../src/features/appearance/image.ts'

test('tema neón y presets válidos conservan ajustes serializados sin modificar valores originales',()=>{
  for(const preset of Object.values(presets)){
    const theme=decodeAppearance({...defaults,...preset,animateBackgrounds:false,grid:false,wallSurface:'album'})
    assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(theme))),theme)
    assert.equal(theme.animateBackgrounds,false);assert.equal(theme.wallSurface,'album');assert.equal(theme.grid,false)
  }
  assert.equal(defaults.animateBackgrounds,true);assert.equal(defaults.wallSurface,'scene')
})

test('preferencias corruptas o CSS/URLs arbitrarios no se convierten en estilos ni solicitudes externas',()=>{
  for(const input of [null,[],{version:999},'texto'])assert.deepEqual(decodeAppearance(input),defaults)
  const bad=decodeAppearance({...defaults,pink:'red; background:url(https://example.com)',skyTop:'var(--x)',angle:Infinity,
    backgroundImage:'https://example.com/privado',grid:'true',wallSurface:'invalid'})
  assert.deepEqual(bad,defaults)
  assert.equal(assetUrl('data:image/png;base64,xx'),false)
  assert.equal(assetUrl('javascript:alert(1)'),false)
  assert.equal(cssVariables(bad)['--scene-image'],'none')
})

test('el fondo solo admite recurso gestionado y permite quitarlo sin eliminar su archivo',()=>{
  const url='/api/v1/assets/12345678-1234-1234-1234-123456789abc/content'
  const {background:_,...legacy}=defaults
  const theme=decodeAppearance({...legacy,backgroundImage:url,skyTop:'#abcdef'})
  assert.equal(theme.skyTop,'#ABCDEF');assert.equal(theme.background.image,url)
  assert.equal(theme.background.mode,'image');assert.equal(cssVariables(theme)['--grid-opacity'],'0')
  const changed=replaceBackground(theme,undefined,{...theme.background,mode:'city'})
  assert.equal(changed.background.image,url);assert.equal(changed.background.mode,'city')
  assert.equal(theme.background.mode,'image')
})

const albumA='11111111-1111-1111-1111-111111111111',albumB='22222222-2222-2222-2222-222222222222'
const stickerA='33333333-3333-3333-3333-333333333333',stickerB='44444444-4444-4444-4444-444444444444'
test('contorno por sticker conserva color/grosor al serializar y aísla objeto/álbum',()=>{
  const a=changeStickerOutline(defaults,albumA,stickerA,{color:'#aabbcc',thickness:7.5})
  assert.deepEqual(stickerOutlineFor(a,albumA,stickerA),{color:'#AABBCC',thickness:7.5})
  assert.deepEqual(stickerOutlineFor(a,albumB,stickerA),defaultStickerOutline);assert.deepEqual(stickerOutlineFor(a,albumA,stickerB),defaultStickerOutline)
  const b=changeStickerOutline(a,albumA,stickerA,{thickness:0});assert.deepEqual(stickerOutlineFor(b,albumA,stickerA),{color:'#AABBCC',thickness:0});assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(b))),b);assert.deepEqual(defaults.stickerOutlines,{})
})
test('encuadre conserva desplazamiento y rotación al recargar y rechaza transformaciones inválidas',()=>{
  const a=replaceBackground(defaults,undefined,{...defaults.background,mode:'image',image:'/api/v1/assets/12345678-1234-1234-1234-123456789abc/content',panX:.2,panY:-.15,rotation:45})
  assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(a))),a)
  const b=decodeWallpaper({...a.background,panX:3,panY:NaN,rotation:Infinity});assert.equal(b.panX,0);assert.equal(b.panY,0);assert.equal(b.rotation,0)
})
test('contornos migran preferencias antiguas y rechazan color/CSS/grosor o identificadores inválidos',()=>{
  const {stickerOutlines:_,...legacy}=defaults;assert.deepEqual(decodeAppearance(legacy),defaults)
  const a=decodeAppearance({...defaults,stickerOutlines:{[`${albumA}:${stickerA}`]:{color:'url(https://example.com)',thickness:Infinity},invalid:{color:'#000000',thickness:12},[`${albumA}:${stickerB}`]:{color:'#123456',thickness:13}}})
  assert.equal(Object.keys(a.stickerOutlines).length,2);assert.deepEqual(stickerOutlineFor(a,albumA,stickerA),defaultStickerOutline);assert.deepEqual(stickerOutlineFor(a,albumA,stickerB),{color:'#123456',thickness:2})
  for(const thickness of [-1,'8',NaN])assert.equal(stickerOutlineFor(changeStickerOutline(defaults,albumA,stickerA,{thickness:thickness as number}),albumA,stickerA).thickness,2)
})
test('fondo de álbum independiente, herencia y retorno al principal sin afectar otros álbumes',()=>{
  let a=replaceBackground(defaults,albumA,{...defaults.background,mode:'city',x:20,zoom:2})
  assert.equal(backgroundFor(a,albumA).mode,'city');assert.deepEqual(backgroundFor(a,albumB),defaults.background)
  a=replaceBackground(a,undefined,{...defaults.background,x:70})
  assert.equal(backgroundFor(a,albumA).x,20);assert.equal(backgroundFor(a,albumB).x,70)
  a=replaceBackground(a,albumA,null)
  assert.equal(backgroundFor(a,albumA).x,70);assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(a))),a)
  assert.deepEqual(defaults.albumBackgrounds,{})
})
test('transparencia reversible por álbum conserva el resto de las preferencias',()=>{
  const colored=decodeAppearance({...defaults,wallSurfaces:{[albumA]:'album',[albumB]:'album'}})
  const clear=decodeAppearance({...colored,wallSurfaces:{...colored.wallSurfaces,[albumA]:'scene'}})
  assert.equal(wallSurfaceFor(clear,albumA),'scene');assert.equal(wallSurfaceFor(clear,albumB),'album')
  assert.equal(wallSurfaceFor(colored,albumA),'album');assert.deepEqual(clear.background,colored.background)
})
test('encuadre malformado y claves no válidas no se conservan',()=>{
  assert.deepEqual(decodeWallpaper({mode:'image',image:'https://example.com/a.png',x:-1,y:101,zoom:Infinity}),defaults.background)
  const a=decodeAppearance({...defaults,albumBackgrounds:{invalid:{mode:'city'}},wallSurfaces:{[albumA]:'transparent',invalid:'album'}})
  assert.deepEqual(a.albumBackgrounds,{});assert.deepEqual(a.wallSurfaces,{})
})
test('preparación conserva proporciones sin ampliar imágenes pequeñas',()=>{
  assert.deepEqual(fittedSize(6000,4000),{width:2560,height:1707})
  assert.deepEqual(fittedSize(1000,6000),{width:427,height:2560})
  assert.deepEqual(fittedSize(320,200),{width:320,height:200})
  assert.throws(()=>fittedSize(0,200));assert.throws(()=>fittedSize(Infinity,200))
})

test('imagen del muro se guarda independiente del fondo del álbum y mantiene encuadre',()=>{
  const url='/api/v1/assets/12345678-1234-1234-1234-123456789abc/content'
  const before=replaceBackground(defaults,albumA,{...defaults.background,mode:'city'})
  const a=replaceWallBackground(before,albumA,{...defaults.background,mode:'image',image:url,fit:'contain',x:15,y:80,zoom:1.7})
  assert.equal(wallSurfaceFor(a,albumA),'image');assert.equal(wallSurfaceFor(a,albumB),'scene')
  assert.deepEqual(a.albumBackgrounds,before.albumBackgrounds);assert.deepEqual(a.background,before.background)
  assert.equal(a.wallBackgrounds[albumA].zoom,1.7);assert.equal(a.wallBackgrounds[albumA].fit,'contain')
  const clear=decodeAppearance({...a,wallSurfaces:{...a.wallSurfaces,[albumA]:'scene'}})
  assert.equal(clear.wallBackgrounds[albumA].image,url);assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(a))),a)
  const invalid=decodeAppearance({...defaults,wallBackgrounds:{[albumA]:{image:'https://example.com/a'}},wallSurfaces:{[albumA]:'image'}})
  assert.equal(wallSurfaceFor(invalid,albumA),'scene');assert.deepEqual(invalid.wallBackgrounds,{})
})

test('vinilos y portadas conservan selección por álbum, valor global y migración de preferencias',()=>{
  assert.equal(presentationFor(defaults,albumA),'vinyl')
  const a=decodeAppearance({...defaults,albumPresentation:'image',albumPresentations:{[albumA]:'vinyl',[albumB]:'invalid',invalid:'image'}})
  assert.equal(presentationFor(a,albumA),'vinyl');assert.equal(presentationFor(a,albumB),'image')
  assert.deepEqual(a.albumPresentations,{[albumA]:'vinyl'});assert.deepEqual(decodeAppearance(JSON.parse(JSON.stringify(a))),a)
  const {wallBackgrounds:_,albumPresentation:__,albumPresentations:___,...legacy}=defaults
  assert.deepEqual(decodeAppearance(legacy),defaults)
})

test('eliminar imagen personalizada respeta ámbito, recursos compartidos y estilos predeterminados',()=>{
  const image={...defaults.background,mode:'image' as const,image:'/api/v1/assets/12345678-1234-1234-1234-123456789abc/content'}
  const a=replaceWallBackground(replaceBackground(replaceBackground(defaults,undefined,image),albumA,image),albumA,image)
  const main=removeCustomBackground(a,'main');assert.equal(main.background.image,null);assert.equal(main.background.mode,'synthwave');assert.equal(main.albumBackgrounds[albumA].image,image.image)
  const album=removeCustomBackground(a,'album',albumA);assert.equal(album.albumBackgrounds[albumA].image,null);assert.deepEqual(album.background,a.background);assert.deepEqual(album.wallBackgrounds,a.wallBackgrounds)
  const wall=removeCustomBackground(a,'wall',albumA);assert.equal(wall.wallBackgrounds[albumA],undefined);assert.equal(wallSurfaceFor(wall,albumA),'scene');assert.deepEqual(wall.albumBackgrounds,a.albumBackgrounds)
  assert.deepEqual(removeCustomBackground(defaults,'main'),defaults)
  const city=replaceBackground(defaults,undefined,{...image,mode:'city'});assert.equal(removeCustomBackground(city,'main').background.mode,'city')
  assert.equal(removeCustomBackground(defaults,'album',albumB),defaults)
})

test('los paisajes nuevos se conservan por álbum y respetan la animación desactivada',()=>{
  const theme=decodeAppearance({...defaults,angle:40,animateBackgrounds:false,
    background:{...defaults.background,mode:'city'},
    albumBackgrounds:{[albumA]:{...defaults.background,mode:'aurora'}}})
  assert.equal(theme.background.mode,'city')
  assert.equal(backgroundFor(theme,albumA).mode,'aurora')
  assert.equal(cssVariables(theme,albumA)['--grid-opacity'],'0')
  assert.equal(decodeAppearance(JSON.parse(JSON.stringify(theme))).animateBackgrounds,false)
  assert.equal('angle' in theme,false)
  assert.equal(decodeWallpaper({mode:'constructor'}).mode,'synthwave')
})

test('los colores personalizados del cielo se aplican a todos los fondos',()=>{
  const theme=decodeAppearance({...defaults,skyTop:'#134E4A',skyBottom:'#F5D0FE'})
  const colors=cssVariables(theme)
  for(const prefix of ['synth','city','aurora','winter','rain']){
    assert.equal(colors[`--${prefix}-top` as keyof typeof colors],'#134E4A')
    assert.equal(colors[`--${prefix}-bottom` as keyof typeof colors],'#F5D0FE')
  }
  assert.equal(colors['--landscape-tint-top'],'#134E4A')
  assert.equal(colors['--landscape-tint-bottom'],'#F5D0FE')
  assert.equal(cssVariables(defaults)['--landscape-tint-top'],'transparent')
  assert.equal(cssVariables(defaults)['--city-top'],'#8B5A95')
  assert.equal(cssVariables(defaults)['--aurora-top'],'#071837')
})


test('los fondos retirados pasan a Synthwave y conservan la imagen guardada',()=>{
  const image='/api/v1/assets/12345678-1234-1234-1234-123456789abc/content'
  for (const mode of ['vaporwave', 'ocean', 'lake']) {
    const oldBackground={...defaults.background,mode,image,zoom:2}
    const theme=decodeAppearance({...defaults,background:oldBackground,albumBackgrounds:{[albumA]:oldBackground}})
    const expected={...oldBackground,mode:'synthwave'}
    assert.deepEqual(theme.background,expected)
    assert.deepEqual(backgroundFor(theme,albumA),expected)
  }
})
