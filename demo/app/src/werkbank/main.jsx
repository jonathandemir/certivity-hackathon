import React from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/schibsted-grotesk'
import '@fontsource-variable/newsreader'
import '@fontsource-variable/newsreader/wght-italic.css'
import './werkbank.css'
import Werkbank from './Werkbank.jsx'

createRoot(document.getElementById('root')).render(<Werkbank />)
