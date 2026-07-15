import { env } from '@/config/env'
import { BaseService } from '@/services/base'
import type { EventSession, StepContext } from '@/utils/epcis-session'

export interface TriggerResult {
  step_id: string
  sscc: string
  event_file: string
}

class TriggerService extends BaseService {
  constructor () {
    super(env.backendBaseUrl)
  }

  triggerStep (
    stepId: string,
    session: EventSession,
    step: StepContext,
  ): Promise<TriggerResult> {
    return this.post<TriggerResult>(`/trigger/${stepId}`, {
      session: {
        sscc: session.sscc,
        lgtin1: session.lgtin1,
        lgtin2: session.lgtin2,
        lgtin3: session.lgtin3,
        desadv: session.desadv,
      },
      step,
    })
  }
}

export const triggerService = new TriggerService()
