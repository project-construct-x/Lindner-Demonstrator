const GS1_BASE_URI = 'https://id.gs1.org/00'
const LGTIN_GTIN_1 = '04047111793267'
const LGTIN_GTIN_2 = '04047111288459'
const LGTIN_GTIN_3 = '04047111528531'
const DESADV_PREFIX = '40471113333333'
const LOT_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'

export interface EventSession {
  sscc: string
  digitalLink: string
  lgtin1: string
  lgtin2: string
  lgtin3: string
  desadv: string
}

export interface StepContext {
  eventTimeZoneOffset: string
}

function gs1CheckDigit (base17: string): number {
  let sum = 0
  for (let i = 0; i < 17; i++) {
    const digit = Number.parseInt(base17[16 - i] ?? '0', 10)
    sum += digit * (i % 2 === 0 ? 3 : 1)
  }
  return (10 - (sum % 10)) % 10
}

function randomToken (length: number): string {
  return Array.from(
    { length },
    () => LOT_CHARS[Math.floor(Math.random() * LOT_CHARS.length)],
  ).join('')
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

function toLgtin (gtin: string): string {
  return `https://id.gs1.org/01/${gtin}/10/${randomToken(4)}`
}

function generateDesadv (): string {
  return `https://id.gs1.org/253/${DESADV_PREFIX}${randomToken(10)}`
}

export function createEventSession (): EventSession {
  const sscc = generateSscc()
  const digitalLink = toDigitalLink(sscc)

  return {
    sscc: digitalLink,
    digitalLink,
    lgtin1: toLgtin(LGTIN_GTIN_1),
    lgtin2: toLgtin(LGTIN_GTIN_2),
    lgtin3: toLgtin(LGTIN_GTIN_3),
    desadv: generateDesadv(),
  }
}

export function formatEventTimeZoneOffset (date: Date): string {
  const offsetMinutes = -date.getTimezoneOffset()
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, '0')
  const minutes = String(Math.abs(offsetMinutes) % 60).padStart(2, '0')
  return `${sign}${hours}:${minutes}`
}

export function createStepContext (date = new Date()): StepContext {
  return {
    eventTimeZoneOffset: formatEventTimeZoneOffset(date),
  }
}
