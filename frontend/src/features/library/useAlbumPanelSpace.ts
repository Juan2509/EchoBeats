import { useEffect, useRef } from 'react'

/** Reserva al álbum el alto que queda entre su barra de acciones y el reproductor. */
export function useAlbumPanelSpace(loadedId: string | undefined) {
  const panel = useRef<HTMLElement>(null)

  useEffect(() => {
    const room = panel.current?.closest<HTMLElement>('.album-room')
    const workspace = room?.closest<HTMLElement>('.workspace')
    if (!loadedId || !room || !workspace) return

    const header = workspace.querySelector('.site-header')
    const toolbar = workspace.querySelector('.album-toolbar')
    const player = workspace.querySelector('.player-bar')
    let frame = 0

    function schedule() {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(measure)
    }

    const measure = () => {
      const style = getComputedStyle(workspace)
      const scale = parseFloat(style.zoom) || 1
      const roomTop = room.getBoundingClientRect().top + window.scrollY
      const playerHeight = player?.getBoundingClientRect().height ?? 0
      // El viewport y los rectángulos ya reflejan el zoom del navegador.
      // Las longitudes que aplicamos dentro del workspace usan su escala CSS local.
      const freeHeight = (document.documentElement.clientHeight - roomTop - playerHeight) / scale
      const height = freeHeight - parseFloat(style.paddingBottom) - parseFloat(style.rowGap)
      workspace.style.setProperty('--album-room-height', `${Math.max(120, height)}px`)
    }

    const observer = new ResizeObserver(schedule)
    for (const control of [header, toolbar, player]) {
      if (control) observer.observe(control)
    }
    window.addEventListener('resize', schedule)
    schedule()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      window.removeEventListener('resize', schedule)
      workspace.style.removeProperty('--album-room-height')
    }
  }, [loadedId])

  return panel
}
