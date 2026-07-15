import { fileURLToPath, URL } from 'node:url'
import type { Plugin } from 'vite'
import Vue from '@vitejs/plugin-vue'
import Fonts from 'unplugin-fonts/vite'
import { defineConfig } from 'vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

function probeEndpoints (): Plugin {
  return {
    name: 'probe-endpoints',
    configureServer (server) {
      for (const path of ['/health', '/ready']) {
        server.middlewares.use(path, (_req, res) => {
          res.statusCode = 200
          res.setHeader('Content-Type', 'text/plain')
          res.end('ok\n')
        })
      }
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    probeEndpoints(),
    Vue({
      template: { transformAssetUrls },
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    Vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    Fonts({
      fontsource: {
        families: [
          {
            name: 'Roboto',
            weights: [100, 300, 400, 500, 700, 900],
            styles: ['normal', 'italic'],
          },
        ],
      },
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('src', import.meta.url)),
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
    },
  },
})
