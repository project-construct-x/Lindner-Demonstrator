import {
  buildSsccFromBase17,
  gs1SsccCheckDigit,
} from './sscc-check-digit'

const GS1_BASE_URI = 'https://id.gs1.org/00'
const SSCC_DIGITAL_LINK_PATTERN = /^https:\/\/id\.gs1\.org\/00\/\d{18}$/
const SSCC_DIGITS_PATTERN = /^\d{18}$/
const SSCC_PREFIX = '04047111'

export interface EventSession {
  sscc: string
  digitalLink: string
}

export { gs1SsccCheckDigit } from './sscc-check-digit'

export function isValidSsccDigits (digits: string): boolean {
  if (!SSCC_DIGITS_PATTERN.test(digits)) {
    return false
  }
  if (!digits.startsWith(SSCC_PREFIX)) {
    return false
  }
  const base17 = digits.slice(0, 17)
  return gs1SsccCheckDigit(base17) === Number.parseInt(digits[17] ?? '-1', 10)
}

function cryptoRandomInt (max: number): number {
  const array = new Uint32Array(1)
  crypto.getRandomValues(array)
  return array[0]! % max
}

function buildSsccSerial (sequenceOffset = 0): string {
  const seconds = Math.floor(Date.now() / 1000)
  const timePart = seconds % 100_000
  const randomPart = (cryptoRandomInt(1000) + sequenceOffset) % 1000
  return String(timePart * 1000 + randomPart).padStart(9, '0')
}

function ssccDigitsFromSerial (serial: string): string {
  const base17 = `${SSCC_PREFIX}${serial}`
  return buildSsccFromBase17(base17)
}

export function generateSscc (): string {
  return ssccDigitsFromSerial(buildSsccSerial())
}

export function generateSsccBatch (count: number): string[] {
  if (count < 1) {
    throw new Error('Count must be at least 1')
  }

  const seen = new Set<string>()
  const results: string[] = []

  for (let offset = 0; results.length < count; offset += 1) {
    const digits = ssccDigitsFromSerial(buildSsccSerial(offset))
    if (seen.has(digits)) {
      continue
    }

    seen.add(digits)
    results.push(toDigitalLink(digits))
  }

  return results
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
