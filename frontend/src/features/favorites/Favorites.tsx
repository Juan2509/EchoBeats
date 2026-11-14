import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { FavoritesController } from './controller'

const Context = createContext<{ store: FavoritesController; revision: number; render: number } | null>(null)
export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [value, setValue] = useState<{ store: FavoritesController; revision: number; render: number } | null>(null)
  useEffect(() => {
    const store = new FavoritesController()
    let render = 0
    const update = () => setValue({ store, revision: store.revision, render: ++render })
    const unsubscribe = store.subscribe(update)
    const focus = () => store.invalidate()
    window.addEventListener('focus', focus)
    update()
    return () => { window.removeEventListener('focus', focus); unsubscribe(); store.dispose() }
  }, [])
  return <Context.Provider value={value}>{children}</Context.Provider>
}
export function useFavoritesRevision() { return useContext(Context)?.revision ?? 0 }
export function FavoriteButton({ trackId, title }: { trackId: string; title: string }) {
  const context = useContext(Context), store = context?.store
  const state = store?.get(trackId)
  useEffect(() => { if (store && state?.status === 'idle') void store.load(trackId) }, [store, trackId, state?.status])
  const ready = state?.status === 'ready', failed = state?.status === 'error'
  return <span className="favorite-control">
    <button type="button" className="secondary favorite-button" disabled={!ready && !failed}
      aria-pressed={ready ? state.favorite : undefined}
      aria-label={failed ? `Consultar favorito de ${title}` : `${state?.favorite ? 'Quitar' : 'Guardar'} ${title} ${state?.favorite ? 'de' : 'en'} favoritos`}
      onClick={() => { if (failed) void store?.load(trackId); else if (ready) void store?.set(trackId, !state.favorite) }}>
      {failed ? 'Consultar estado' : state?.status === 'saving' ? 'Guardando…' : ready ? state.favorite ? '♥ Favorita' : '♡ Favorito' : 'Consultando favorito…'}
    </button>
    {failed && <small role="alert">{state.error}</small>}
  </span>
}
