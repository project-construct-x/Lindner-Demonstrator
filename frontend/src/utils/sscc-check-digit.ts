/**
 * GS1 SSCC structure (18 digits total):
 *   N1–N17  extension digit + company prefix + serial reference (17 digits)
 *   N18     GS1 mod-10 check digit
 *
 * Enter N1–N17 in the GS1 AU calculator; N18 is computed from those 17 digits.
 * @see https://www.gs1au.org/services/tools/check-digit-calculator
 */
export const SSCC_PREFIX = '04047111'
export const SSCC_BASE_LENGTH = 17
export const SSCC_DIGITS_LENGTH = 18
export const GS1_SSCC_BASE_URI = 'https://id.gs1.org/00'

const SSCC_DIGITS_PATTERN = /^\d{18}$/

/** GS1 mod-10 check digit for the first 17 digits of an SSCC (N1–N17). */
export function gs1SsccCheckDigit (base17: string): number {
  if (base17.length !== SSCC_BASE_LENGTH) {
    throw new Error(`SSCC base must be exactly ${SSCC_BASE_LENGTH} digits, got ${base17.length}`)
  }

  let sum = 0
  for (let i = 0; i < SSCC_BASE_LENGTH; i++) {
    const digit = Number.parseInt(base17[SSCC_BASE_LENGTH - 1 - i] ?? '0', 10)
    sum += digit * (i % 2 === 0 ? 3 : 1)
  }
  return (10 - (sum % 10)) % 10
}

/**
 * Reference implementation matching GS1 Australia / GS1.org documentation:
 * multiply N1..N17 left-to-right by 3,1,3,1,... starting with ×3 on N1.
 * @see https://www.gs1.org/services/how-calculate-check-digit-manually
 * @see https://www.gs1au.org/services/tools/check-digit-calculator
 */
export function gs1SsccCheckDigitGs1Reference (base17: string): number {
  if (base17.length !== SSCC_BASE_LENGTH) {
    throw new Error(`SSCC base must be exactly ${SSCC_BASE_LENGTH} digits, got ${base17.length}`)
  }

  let sum = 0
  for (let i = 0; i < SSCC_BASE_LENGTH; i++) {
    const weight = i % 2 === 0 ? 3 : 1
    sum += Number.parseInt(base17[i] ?? '0', 10) * weight
  }
  return (10 - (sum % 10)) % 10
}

export function hasValidSsccCheckDigit (digits: string): boolean {
  if (!SSCC_DIGITS_PATTERN.test(digits)) {
    return false
  }
  const base17 = digits.slice(0, SSCC_BASE_LENGTH)
  return gs1SsccCheckDigit(base17) === Number.parseInt(digits[SSCC_BASE_LENGTH] ?? '-1', 10)
}

export function isValidSsccDigits (digits: string, prefix = SSCC_PREFIX): boolean {
  return hasValidSsccCheckDigit(digits) && digits.startsWith(prefix)
}

export function assertValidSsccDigits (digits: string, prefix = SSCC_PREFIX): void {
  if (!isValidSsccDigits(digits, prefix)) {
    throw new Error(
      `Invalid SSCC: expected 17-digit base + check digit (${SSCC_DIGITS_LENGTH} digits total), got "${digits}"`,
    )
  }
}

export function buildSsccFromBase17 (base17: string): string {
  if (!/^\d{17}$/.test(base17)) {
    throw new Error(`SSCC base must be exactly ${SSCC_BASE_LENGTH} digits, got "${base17}"`)
  }

  const digits = `${base17}${gs1SsccCheckDigit(base17)}`
  if (!hasValidSsccCheckDigit(digits)) {
    throw new Error(`Failed to build valid SSCC from base17 "${base17}"`)
  }
  return digits
}

export function toSsccDigitalLink (digits: string): string {
  assertValidSsccDigits(digits)
  return `${GS1_SSCC_BASE_URI}/${digits}`
}

export function ssccDigitsFromDigitalLink (digitalLink: string): string {
  const digits = digitalLink.slice(digitalLink.lastIndexOf('/') + 1)
  assertValidSsccDigits(digits)
  return digits
}
export const SSCC_CHECK_DIGIT_EXAMPLES = [
  {
    base17: '04047111681574983',
    checkDigit: 3,
    full: '040471116815749833',
    note: 'Demonstrator original template SSCC',
  },
  {
    base17: '04047111410764989',
    checkDigit: 2,
    full: '040471114107649892',
    note: 'User-verified via GS1 AU calculator',
  },
  {
    base17: '04047111041724879',
    checkDigit: 4,
    full: '040471110417248794',
    note: 'User-verified via GS1 AU calculator',
  },
  {
    base17: '00614141123456789',
    checkDigit: 0,
    full: '006141411234567890',
    note: 'Docs example; sum is exact multiple of 10',
  },
  {
    base17: '62910415000003239',
    checkDigit: 1,
    full: '629104150000032391',
    note: 'Generic SSCC structure example',
  },
  {
    base17: '10012345678901234',
    checkDigit: 0,
    full: '100123456789012340',
    note: 'Extension digit 1; sum is exact multiple of 10',
  },
] as const
