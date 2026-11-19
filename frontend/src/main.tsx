import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import './app/styles.css'
import './app/synthwave.css'
import './features/appearance/scenes.css'
import './features/appearance/landscapes.css'
import './app/readability.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode><App /></StrictMode>,
)
