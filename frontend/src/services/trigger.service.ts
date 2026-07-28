import type { EventSession } from '@/utils/epcis-session'
import { env } from '@/config/env'
import { BaseService } from '@/services/base'

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
    return this.post<TriggerResult>(`/trigger/${stepNumber}`, {
      sscc: session.sscc,
    })
  }
}

export const triggerService = new TriggerService()
