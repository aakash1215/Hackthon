import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Built output (dist/) is served by the FastAPI hub on https://<LAN-IP>:8443.
// `npm run dev` proxies /api to the hub for UI work on the laptop.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Apna Hisaab',
        short_name: 'Apna Hisaab',
        description: 'Daily work and pay record for construction workers',
        lang: 'hi',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#e4d5c4',
        theme_color: '#6c3d02',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // App shell offline; the API is never cached (offline entries go to the IndexedDB queue).
        globPatterns: ['**/*.{js,css,html,svg,png,jpg,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
  server: {
    allowedHosts: ['die-consumer-subsidiary-poster.trycloudflare.com'],
    proxy: { '/api': { target: 'https://localhost:8443', secure: false } },
  },
})
