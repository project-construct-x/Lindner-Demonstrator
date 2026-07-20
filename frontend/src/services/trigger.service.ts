import type { EventSession, StepContext } from '@/utils/epcis-session'
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

  triggerStep (
    stepNumber: number,
    session: EventSession,
    step: StepContext,
  ): Promise<TriggerResult> {
    return this.post<TriggerResult>(`/trigger/${stepNumber}`, {
      session: {
        sscc: session.sscc,
        lgtin1: session.lgtin1,
        lgtin2: session.lgtin2,
        desadv: session.desadv,
        po: session.po,
      },
      step,
    })
  }
}

export const triggerService = new TriggerService()
