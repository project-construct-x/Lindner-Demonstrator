export interface LifecycleStep {
  id: string
  label: string
}

export const LIFECYCLE_STEPS: LifecycleStep[] = [
  { id: 'ausgang-hersteller', label: 'Ausgang beim Hersteller' },
  { id: 'baustellen-eingang', label: 'Baustellen-Eingang' },
  { id: 'einbau', label: 'Einbau' },
  { id: 'rueckbau', label: 'Rückbau' },
  { id: 'ausgang-baustelle', label: 'Ausgang Baustelle' },
  { id: 'eingang-hersteller', label: 'Eingang beim Hersteller' },
  { id: 'aufbereitung', label: 'Aufbereitung' },
]
