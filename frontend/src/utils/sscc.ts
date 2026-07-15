const GS1_BASE_URI = 'https://id.gs1.org/00'

function gs1CheckDigit (base17: string): number {
  let sum = 0
  for (let i = 0; i < 17; i++) {
    const digit = Number.parseInt(base17[16 - i] ?? '0', 10)
    sum += digit * (i % 2 === 0 ? 3 : 1)
  }
  return (10 - (sum % 10)) % 10
}

export function generateSscc (): string {
  const extensionDigit = Math.floor(Math.random() * 10)
  const serial = String(Math.floor(Math.random() * 10 ** 16)).padStart(16, '0')
  const base17 = `${extensionDigit}${serial}`
  return `${base17}${gs1CheckDigit(base17)}`
}

export function toDigitalLink (sscc: string): string {
  return `${GS1_BASE_URI}/${sscc}`
}

export function createSsccSession (): { sscc: string, digitalLink: string } {
  const sscc = generateSscc()
  return { sscc, digitalLink: toDigitalLink(sscc) }
}
