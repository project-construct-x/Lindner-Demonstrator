const GS1_BASE_URI = 'https://id.gs1.org/00'
const SSCC_DIGITAL_LINK_PATTERN = /^https:\/\/id\.gs1\.org\/00\/\d{18}$/
const SSCC_DIGITS_PATTERN = /^\d{18}$/

export interface EventSession {
  sscc: string
  digitalLink: string
}

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

export function normalizeSsccDigitalLink (value: string): string | null {
  const trimmed = value.trim()

  const digitalLinkMatch = SSCC_DIGITAL_LINK_PATTERN.exec(trimmed)
  if (digitalLinkMatch) {
    return trimmed
  }

  const embeddedDigitalLink = trimmed.match(/https:\/\/id\.gs1\.org\/00\/\d{18}/)?.[0]
  if (embeddedDigitalLink) {
    return embeddedDigitalLink
  }

  const digitsMatch = SSCC_DIGITS_PATTERN.exec(trimmed)
  if (digitsMatch) {
    return toDigitalLink(trimmed)
  }

  const embeddedDigits = trimmed.match(/\d{18}/)?.[0]
  if (embeddedDigits) {
    return toDigitalLink(embeddedDigits)
  }

  return null
}

export function createEventSessionFromDigitalLink (digitalLink: string): EventSession {
  return {
    sscc: digitalLink,
    digitalLink,
  }
}

export function createEventSession (): EventSession {
  const sscc = generateSscc()
  const digitalLink = toDigitalLink(sscc)

  return {
    sscc: digitalLink,
    digitalLink,
  }
}
