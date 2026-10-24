import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Zwei Seiten, je eine eigenständige Datei: `vite build` = Präsentation (index.html),
// `vite build --mode werkbank` = Produkt/Dashboard (werkbank.html).
export default defineConfig(({ mode }) => {
  const page = mode === 'werkbank' ? 'werkbank.html' : 'index.html'
  return {
    base: './',
    plugins: [react(), viteSingleFile()],
    build: {
      outDir: mode === 'werkbank' ? 'dist-werkbank' : 'dist',
      assetsInlineLimit: 100_000_000,
      chunkSizeWarningLimit: 5000,
      rollupOptions: { input: page },
    },
  }
})
