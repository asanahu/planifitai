import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

const enablePwa = process.env.VITE_PWA === '1';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    enablePwa &&
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
          runtimeCaching: [
            {
              urlPattern: ({ url }: { url: URL }) => url.pathname.startsWith('/api/'),
              handler: 'NetworkOnly',
            },
          ],
        },
        manifest: {
          name: 'PlanifitAI',
          short_name: 'PlanifitAI',
          start_url: '/',
          display: 'standalone',
          background_color: '#0b1015',
          theme_color: '#0ea5e9',
          icons: [
            { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          ],
        },
      }),
  ].filter(Boolean),
});