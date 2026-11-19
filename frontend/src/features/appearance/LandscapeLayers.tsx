import type { CSSProperties } from 'react'
import type { SceneMode } from './theme'
import winter from '../../shared/assets/landscapes/winter.webp'
import rain from '../../shared/assets/landscapes/rain.webp'

type Landscape = Exclude<SceneMode, 'synthwave' | 'city' | 'aurora'>

const illustrations = { winter, rain }

// Window centers measured on the rain illustration, in percent of the artwork.
const litWindows = [
  [27.3, 57], [29.3, 57], [34.2, 61.5], [35.8, 65.5],
  [37.2, 53.7], [40.5, 56.9], [42.1, 62.3], [43.6, 69.1],
  [44.1, 57.9], [46.3, 66.2], [46.4, 72.2], [48.0, 69.1],
  [55.9, 58.4], [56.4, 61], [57.1, 71.7], [59.1, 56.3],
  [59.3, 58.8], [61.4, 67.8], [63.9, 67.5], [63.9, 71.6],
  [66.5, 60.8], [70.7, 62.7], [74.7, 60.5], [75.9, 65.4],
  [77.7, 65.3], [76.2, 75], [80, 53.6], [80, 65.2], [83.2, 65.4],
]

const particles = Array.from({ length: 112 }, (_, index) => ({
  left: `${(index * 37.73) % 100}%`,
  top: `${(index * 43.91) % 100}%`,
  '--particle-size': `${1.5 + (index * 7 % 13) / 4}px`,
  '--particle-opacity': .36 + (index % 7) * .085,
  '--particle-phase': `-${(index * 1.73) % 22}s`,
  '--particle-depth': index % 5,
} as CSSProperties))

function Weather({ mode }: { mode: 'winter' | 'rain' }) {
  return <div className="landscape-weather">
    {(mode === 'winter' ? particles : particles.slice(0, 66)).map((style, index) => <i key={index} style={style} />)}
  </div>
}

export function LandscapeLayers({ mode, animated }: { mode: Landscape; animated: boolean }) {
  const image = illustrations[mode]
  return <>
    <div className="landscape-artwork">
      <img src={image} alt="" draggable={false} decoding="async" loading={animated ? 'eager' : 'lazy'} />
      {animated && mode === 'rain' && <div className="landscape-city-lights">
        {litWindows.map(([left, top], index) => <i key={index} style={{
          left: `${left}%`,
          top: `${top}%`,
          '--light-phase': `-${index * 1.37 % 18}s`,
        } as CSSProperties} />)}
      </div>}
      <div className="landscape-palette" />
      {mode === 'rain' && <Weather mode="rain" />}
    </div>
    {mode === 'winter' && <Weather mode="winter" />}
  </>
}
