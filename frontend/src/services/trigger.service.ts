import { env } from '@/config/env'
import { BaseService } from '@/services/base'

export interface TriggerResult {
  step_id: string
  sscc: string
  event_file: string
}

class TriggerService extends BaseService {
  constructor () {
    super(env.backendBaseUrl)
  }

  triggerStep (stepId: string, sscc: string): Promise<TriggerResult> {
    return this.post<TriggerResult>(`/trigger/${stepId}`, { sscc })
  }
}

export const triggerService = new TriggerService()
