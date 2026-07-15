import stepImage1 from '@/assets/1.png'
import stepImage2 from '@/assets/2.png'
import stepImage3 from '@/assets/3.png'
import stepImage4 from '@/assets/4.png'
import stepImage5 from '@/assets/5.png'
import stepImage6 from '@/assets/6.png'
import stepImage7 from '@/assets/7.png'

export interface LifecycleStep {
  id: string
  label: string
  image: string
}

export interface LifecycleStory {
  title: string
  steps: LifecycleStep[]
}

export const LIFECYCLE_STORIES: LifecycleStory[] = [
  {
    title: 'Einbau',
    steps: [
      { id: 'ausgang-hersteller', label: 'Ausgang beim Hersteller', image: stepImage1 },
      { id: 'baustellen-eingang', label: 'Baustellen-Eingang', image: stepImage2 },
      { id: 'einbau', label: 'Einbau', image: stepImage3 },
    ],
  },
  {
    title: 'Rückbau',
    steps: [
      { id: 'rueckbau', label: 'Rückbau', image: stepImage4 },
      { id: 'ausgang-baustelle', label: 'Ausgang Baustelle', image: stepImage5 },
      { id: 'eingang-hersteller', label: 'Eingang beim Hersteller', image: stepImage6 },
      { id: 'aufbereitung', label: 'Aufbereitung', image: stepImage7 },
    ],
  },
]

export const LIFECYCLE_STEPS: LifecycleStep[] = LIFECYCLE_STORIES.flatMap(story => story.steps)
