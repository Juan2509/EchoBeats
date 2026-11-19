import type { CSSProperties } from 'react'
import type { SceneMode } from './theme'
import { LandscapeLayers } from './LandscapeLayers'

// Fixed composition so the full-screen scene and its thumbnail always agree.
const skyline = [
  [38, 64, 26, 79, 42, 58, 30, 69, 53, 37, 76, 55, 39, 64, 46, 82, 49, 58, 37, 61],
  [51, 32, 70, 45, 36, 57, 78, 47, 53, 68, 41, 74, 58, 34, 63, 47, 54, 39, 71, 55],
  [45, 61, 29, 48, 57, 36, 51, 31, 62, 42, 53, 33, 65, 39, 54, 48, 34, 61, 50, 37],
]

const stars = Array.from({ length: 64 }, (_, i) => ({
  left: `${(i * 43.73) % 100}%`,
  top: `${(i * i * 13.31 + i * 4.27) % 78}%`,
  '--star-size': i % 13 === 0 ? '3px' : i % 3 === 0 ? '2px' : '1px',
  '--star-opacity': .28 + (i % 7) * .09,
} as CSSProperties))

function SceneSkyline() {
  return <>{skyline.map((row, layer) => <div className={`scene-skyline scene-skyline-${layer}`} key={layer}>
        {row.map((height, index) => <div className="scene-building" key={index} style={{
          '--building-height': `${height}%`,
          '--building-width': 3 + ((index * 17 + layer) % 6),
          '--light-delay': `-${(index * 3.31) % 17}s`,
        } as CSSProperties} />)}
      </div>)}</>
}

export function SceneArtwork({ mode, animated = false }: { mode: SceneMode; animated?: boolean }) {
  if (mode === 'synthwave') {
    return <div className="scene-art scene-neon" data-animated={animated} />
  }

  if (mode !== 'city' && mode !== 'aurora') {
    return <div className={`scene-art scene-${mode}`} data-animated={animated}>
      <LandscapeLayers mode={mode} animated={animated} />
    </div>
  }

  return <div className={`scene-art scene-${mode}`} data-animated={animated}>
    <div className="scene-stars">{stars.map((style, index) => <i key={index} style={style} />)}</div>
    {mode === 'city' ? <>
      <div className="scene-city-sun" />
      <SceneSkyline />
      <div className="scene-rail">
        <div className="scene-train">{[0, 1, 2, 3].map(car => <i key={car} />)}</div>
      </div>
    </> : <>
      <div className="scene-aurora-ribbon scene-aurora-green" />
      <div className="scene-aurora-ribbon scene-aurora-violet" />
      <div className="scene-aurora-ribbon scene-aurora-cyan" />
      <div className="scene-aurora-water" />
      <div className="scene-aurora-mountains" />
      <div className="scene-aurora-shore" />
    </>}
  </div>
}
