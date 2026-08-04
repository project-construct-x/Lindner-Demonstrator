import {
  SSCC_CHECK_DIGIT_EXAMPLES,
  buildSsccFromBase17,
  gs1SsccCheckDigit,
  gs1SsccCheckDigitGs1Reference,
} from '../src/utils/sscc-check-digit.ts'
import { generateSsccBatch, isValidSsccDigits } from '../src/utils/epcis-session.ts'

let failed = 0

function assert (condition: boolean, message: string) {
  if (!condition) {
    console.error(`FAIL: ${message}`)
    failed += 1
  }
}

console.log('SSCC check digit verification (GS1 AU / GS1.org reference)\n')
console.log('base17 (17 digits)          | expected | ours | GS1 ref | full SSCC')
console.log('-'.repeat(85))

for (const example of SSCC_CHECK_DIGIT_EXAMPLES) {
  const ours = gs1SsccCheckDigit(example.base17)
  const reference = gs1SsccCheckDigitGs1Reference(example.base17)
  const built = buildSsccFromBase17(example.base17)

  console.log(
    `${example.base17} | ${String(example.checkDigit).padStart(8)} | ${String(ours).padStart(4)} | ${String(reference).padStart(7)} | ${built}`,
  )

  assert(ours === example.checkDigit, `${example.base17}: ours !== expected (${ours} vs ${example.checkDigit})`)
  assert(reference === example.checkDigit, `${example.base17}: GS1 ref !== expected`)
  assert(ours === reference, `${example.base17}: ours !== GS1 reference`)
  assert(built === example.full, `${example.base17}: built full SSCC mismatch (${built} vs ${example.full})`)
  assert(
    gs1SsccCheckDigit(built.slice(0, 17)) === Number.parseInt(built[17] ?? '-1', 10),
    `${example.full}: full SSCC check digit invalid`,
  )
  if (built.startsWith('04047111')) {
    assert(isValidSsccDigits(built), `${example.full}: isValidSsccDigits should pass`)
  }
}

console.log('\nGenerated batch (prefix 04047111, 5 samples):')
const batch = generateSsccBatch(5)
for (const digitalLink of batch) {
  const digits = digitalLink.slice(digitalLink.lastIndexOf('/') + 1)
  const base17 = digits.slice(0, 17)
  const ours = gs1SsccCheckDigit(base17)
  const reference = gs1SsccCheckDigitGs1Reference(base17)
  const check = Number.parseInt(digits[17] ?? '-1', 10)

  console.log(`  ${digits} | check=${check} ours=${ours} ref=${reference}`)
  assert(digits.length === 18, `${digits}: must be 18 digits`)
  assert(ours === check, `${digits}: generated check mismatch`)
  assert(ours === reference, `${digits}: ours !== GS1 reference`)
  assert(isValidSsccDigits(digits), `${digits}: validation failed`)
}

console.log(failed === 0 ? '\nAll checks passed.' : `\n${failed} check(s) failed.`)
process.exit(failed === 0 ? 0 : 1)
