import { env } from '@/config/env'
import { debugError, debugLog, debugWarn } from '@/utils/debug'

export interface SsccSnapshot {
  sscc: string
  completed_steps: number[]
  completed_step_ids: string[]
}

export interface StepCompletedEvent {
  sscc: string
  step_number: number
  step_id: string
  step_label: string
  document_file: string
  event_count: number
  completed_steps: number[]
  completed_step_ids: string[]
}

export interface SsccSubscriptionHandlers {
  onSnapshot: (snapshot: SsccSnapshot) => void
  onStepCompleted: (event: StepCompletedEvent) => void
  onError?: (error: Event) => void
}

class SsccSubscriptionService {
  private eventSource: EventSource | null = null
  private activeSscc: string | null = null

  subscribe (sscc: string, handlers: SsccSubscriptionHandlers): void {
    if (this.activeSscc === sscc && this.eventSource) {
      return
    }

    this.unsubscribe()

    const url = `${env.backendBaseUrl}/sscc/stream?sscc=${encodeURIComponent(sscc)}`
    debugLog('subscription', 'Opening SSCC stream', { sscc, url })

    const eventSource = new EventSource(url)
    this.eventSource = eventSource
    this.activeSscc = sscc

    eventSource.addEventListener('snapshot', event => {
      try {
        const snapshot = JSON.parse(event.data) as SsccSnapshot
        debugLog('subscription', 'Received snapshot', snapshot)
        handlers.onSnapshot(snapshot)
      } catch (error) {
        debugError('subscription', 'Failed to parse snapshot event', error)
      }
    })

    eventSource.addEventListener('step_completed', event => {
      try {
        const stepEvent = JSON.parse(event.data) as StepCompletedEvent
        debugLog('subscription', 'Step completed event', stepEvent)
        handlers.onStepCompleted(stepEvent)
      } catch (error) {
        debugError('subscription', 'Failed to parse step_completed event', error)
      }
    })

    eventSource.addEventListener('error', error => {
      debugWarn('subscription', 'SSCC stream error', {
        sscc,
        readyState: eventSource.readyState,
      })
      handlers.onError?.(error)
    })
  }

  unsubscribe (): void {
    if (this.eventSource) {
      debugLog('subscription', 'Closing SSCC stream', { sscc: this.activeSscc })
      this.eventSource.close()
    }

    this.eventSource = null
    this.activeSscc = null
  }
}

export const ssccSubscriptionService = new SsccSubscriptionService()
