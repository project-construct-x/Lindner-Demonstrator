const GS1_BASE_URI = 'https://id.gs1.org/00'
const SSCC_DIGITAL_LINK_PATTERN = /^https:\/\/id\.gs1\.org\/00\/\d{18}$/
const SSCC_DIGITS_PATTERN = /^\d{18}$/
const SSCC_PREFIX = '04047111'

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

export function isValidSsccDigits (digits: string): boolean {
  if (!SSCC_DIGITS_PATTERN.test(digits)) {
    return false
  }
  if (!digits.startsWith(SSCC_PREFIX)) {
    return false
  }
  const base17 = digits.slice(0, 17)
  return gs1CheckDigit(base17) === Number.parseInt(digits[17] ?? '-1', 10)
}

function cryptoRandomInt (max: number): number {
  const array = new Uint32Array(1)
  crypto.getRandomValues(array)
  return array[0]! % max
}

function buildSsccSerial (): string {
  const seconds = Math.floor(Date.now() / 1000)
  const timePart = seconds % 100_000
  const randomPart = cryptoRandomInt(1000)
  return String(timePart * 1000 + randomPart).padStart(8, '0')
}

export function generateSscc (): string {
  const base17 = `${SSCC_PREFIX}${buildSsccSerial()}`
  return `${base17}${gs1CheckDigit(base17)}`
}

export function toDigitalLink (sscc: string): string {
  return `${GS1_BASE_URI}/${sscc}`
}

export function normalizeSsccDigitalLink (value: string): string | null {
  const trimmed = value.trim()

  const digitalLinkMatch = SSCC_DIGITAL_LINK_PATTERN.exec(trimmed)
  if (digitalLinkMatch) {
    const digits = trimmed.slice(trimmed.lastIndexOf('/') + 1)
    return isValidSsccDigits(digits) ? trimmed : null
  }

  const embeddedDigitalLink = trimmed.match(/https:\/\/id\.gs1\.org\/00\/\d{18}/)?.[0]
  if (embeddedDigitalLink) {
    const digits = embeddedDigitalLink.slice(embeddedDigitalLink.lastIndexOf('/') + 1)
    return isValidSsccDigits(digits) ? embeddedDigitalLink : null
  }

  const digitsMatch = SSCC_DIGITS_PATTERN.exec(trimmed)
  if (digitsMatch) {
    if (!isValidSsccDigits(trimmed)) {
      return null
    }
    return toDigitalLink(trimmed)
  }

  const embeddedDigits = trimmed.match(/\d{18}/)?.[0]
  if (embeddedDigits) {
    if (!isValidSsccDigits(embeddedDigits)) {
      return null
    }
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
