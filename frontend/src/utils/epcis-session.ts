import {
  SSCC_PREFIX,
  buildSsccFromBase17,
  isValidSsccDigits,
  toSsccDigitalLink,
} from './sscc-check-digit'

const SSCC_DIGITAL_LINK_PATTERN = /^https:\/\/id\.gs1\.org\/00\/\d{18}$/
const SSCC_DIGITS_PATTERN = /^\d{18}$/

export interface EventSession {
  sscc: string
  digitalLink: string
}

export {
  gs1SsccCheckDigit,
  isValidSsccDigits,
  toSsccDigitalLink as toDigitalLink,
} from './sscc-check-digit'

function cryptoRandomInt (max: number): number {
  const array = new Uint32Array(1)
  crypto.getRandomValues(array)
  return array[0]! % max
}

function normalizeSerial (serial: string): string {
  return serial.padStart(9, '0').slice(-9)
}

function buildSsccSerial (sequenceOffset = 0): string {
  const seconds = Math.floor(Date.now() / 1000)
  const timePart = seconds % 100_000
  const randomPart = (cryptoRandomInt(1000) + sequenceOffset) % 1000
  return normalizeSerial(String(timePart * 1000 + randomPart))
}

function ssccDigitsFromSerial (serial: string): string {
  const base17 = `${SSCC_PREFIX}${normalizeSerial(serial)}`
  return buildSsccFromBase17(base17)
}

export function generateSscc (): string {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    const digits = ssccDigitsFromSerial(buildSsccSerial(attempt))
    if (isValidSsccDigits(digits)) {
      return digits
    }
  }

  throw new Error('Failed to generate a valid 18-digit SSCC')
}

export function generateSsccBatch (count: number): string[] {
  if (count < 1) {
    throw new Error('Count must be at least 1')
  }

  const seen = new Set<string>()
  const results: string[] = []

  for (let offset = 0; results.length < count; offset += 1) {
    const digits = generateSsccFromOffset(offset)
    if (seen.has(digits)) {
      continue
    }

    seen.add(digits)
    results.push(toSsccDigitalLink(digits))
  }

  if (results.length < count) {
    throw new Error(`Failed to generate ${count} unique valid SSCCs`)
  }

  return results
}

function generateSsccFromOffset (offset: number): string {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    const digits = ssccDigitsFromSerial(buildSsccSerial(offset + attempt))
    if (isValidSsccDigits(digits)) {
      return digits
    }
  }

  throw new Error('Failed to generate a valid 18-digit SSCC')
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
    return toSsccDigitalLink(trimmed)
  }

  const embeddedDigits = trimmed.match(/\d{18}/)?.[0]
  if (embeddedDigits) {
    if (!isValidSsccDigits(embeddedDigits)) {
      return null
    }
    return toSsccDigitalLink(embeddedDigits)
  }

  return null
}

export function createEventSessionFromDigitalLink (digitalLink: string): EventSession {
  const normalized = normalizeSsccDigitalLink(digitalLink)
  if (!normalized) {
    throw new Error('Invalid SSCC digital link')
  }

  return {
    sscc: normalized,
    digitalLink: normalized,
  }
}

export function createEventSession (): EventSession {
  const digitalLink = toSsccDigitalLink(generateSscc())

  return {
    sscc: digitalLink,
    digitalLink,
  }
}
