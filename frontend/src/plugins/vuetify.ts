/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

const constructXDark = {
  dark: true,
  colors: {
    background: '#0a0e17',
    surface: '#111827',
    'surface-bright': '#1a2332',
    'surface-light': '#1e293b',
    'surface-variant': '#243044',
    'on-surface-variant': '#94a3b8',
    primary: '#337ab7',
    'primary-darken-1': '#2a6399',
    secondary: '#818cf8',
    accent: '#337ab7',
    error: '#f87171',
    info: '#38bdf8',
    success: '#34d399',
    warning: '#fbbf24',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'constructXDark',
    themes: {
      constructXDark,
    },
  },
})
