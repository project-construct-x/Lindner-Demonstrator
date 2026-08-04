import { generateSscc, toDigitalLink } from '@/utils/epcis-session'

export { generateSscc, toDigitalLink }

export function createSsccSession (): { sscc: string, digitalLink: string } {
  const digits = generateSscc()
  const digitalLink = toDigitalLink(digits)
  return { sscc: digits, digitalLink }
}
