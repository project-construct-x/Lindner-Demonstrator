function requireEnv (name: keyof ImportMetaEnv): string {
  const value = import.meta.env[name]
  if (!value) {
    throw new Error(`Missing environment variable: ${name}`)
  }
  return value
}

export const env = {
  backendBaseUrl: requireEnv('VITE_BACKEND_BASE_URL'),
} as const
