import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Built output (dist/) is served by the FastAPI hub on https://<LAN-IP>:8443.
// `npm run dev` proxies /api to the local hub, with or without local TLS certificates.
const repoRoot = resolve(import.meta.dirname, '..')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, '')
  const certFile = resolve(repoRoot, env.CERT_FILE || 'certs/cert.pem')
  const keyFile = resolve(repoRoot, env.KEY_FILE || 'certs/key.pem')
  const protocol = existsSync(certFile) && existsSync(keyFile) ? 'https' : 'http'
  const port = env.PORT || '8443'

  return {
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
      allowedHosts: ['die-consumer-subsidiary-poster.trycloudflare.com','dancing-consultants-robinson-nathan.trycloudflare.com'],
      proxy: { '/api': { target: `${protocol}://127.0.0.1:${port}`, secure: false } },
    },
  }
})
