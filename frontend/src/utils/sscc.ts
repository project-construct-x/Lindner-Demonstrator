import { generateSscc, toDigitalLink } from '@/utils/epcis-session'

export { generateSscc, toDigitalLink }

export function createSsccSession (): { sscc: string, digitalLink: string } {
  const sscc = generateSscc()
  return { sscc, digitalLink: toDigitalLink(sscc) }
}
