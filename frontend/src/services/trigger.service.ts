import type { EventSession } from '@/utils/epcis-session'
import { env } from '@/config/env'
import { BaseService } from '@/services/base'
import { debugLog } from '@/utils/debug'

export interface TriggerResult {
  step_id: string
  sscc: string
  document_file: string
  event_count: number
}

class TriggerService extends BaseService {
  constructor () {
    super(env.backendBaseUrl)
  }

  triggerStep (stepNumber: number, session: EventSession): Promise<TriggerResult> {
    const payload = { sscc: session.sscc }
    debugLog('trigger', `POST /trigger/${stepNumber}`, payload)

    return this.post<TriggerResult>(`/trigger/${stepNumber}`, payload)
  }
}

export const triggerService = new TriggerService()
