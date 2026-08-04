/** GS1 mod-10 check digit for the first 17 digits of an SSCC (N1–N17). */
export function gs1SsccCheckDigit (base17: string): number {
  if (base17.length !== 17) {
    throw new Error(`SSCC base must be exactly 17 digits, got ${base17.length}`)
  }

  let sum = 0
  for (let i = 0; i < 17; i++) {
    const digit = Number.parseInt(base17[16 - i] ?? '0', 10)
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
  if (base17.length !== 17) {
    throw new Error(`SSCC base must be exactly 17 digits, got ${base17.length}`)
  }

  let sum = 0
  for (let i = 0; i < 17; i++) {
    const weight = i % 2 === 0 ? 3 : 1
    sum += Number.parseInt(base17[i] ?? '0', 10) * weight
  }
  return (10 - (sum % 10)) % 10
}

export function buildSsccFromBase17 (base17: string): string {
  return `${base17}${gs1SsccCheckDigit(base17)}`
}

/** Known base17 → check digit pairs (verify at GS1 AU SSCC calculator). */
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
