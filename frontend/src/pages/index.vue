<script lang="ts" setup>
  import { computed, onMounted, ref } from 'vue'
  import QrcodeVue from 'qrcode.vue'
  import { triggerService } from '@/services/trigger.service'
  import { LIFECYCLE_STEPS, LIFECYCLE_STORIES } from '@/constants/steps'
  import { createSsccSession } from '@/utils/sscc'

  const digitalLink = ref('')
  const executedSteps = ref<Set<string>>(new Set())
  const loadingStep = ref<string | null>(null)
  const snackbar = ref(false)
  const snackbarText = ref('')
  const snackbarColor = ref<'success' | 'error'>('success')

  const nextStepIndex = computed(() =>
    LIFECYCLE_STEPS.findIndex(step => !executedSteps.value.has(step.id)),
  )

  const allStepsCompleted = computed(() => nextStepIndex.value === -1)

  function isStepEnabled (stepId: string): boolean {
    const index = LIFECYCLE_STEPS.findIndex(step => step.id === stepId)
    return index === nextStepIndex.value
  }

  function getStepNumber (stepId: string): number {
    return LIFECYCLE_STEPS.findIndex(step => step.id === stepId) + 1
  }

  function isStepCompleted (stepId: string): boolean {
    return executedSteps.value.has(stepId)
  }

  function isStoryCompleted (storyIndex: number): boolean {
    const story = LIFECYCLE_STORIES[storyIndex]
    return story.steps.every(step => executedSteps.value.has(step.id))
  }

  function resetSession () {
    const session = createSsccSession()
    digitalLink.value = session.digitalLink
    executedSteps.value = new Set()
    loadingStep.value = null
  }

  function notify (text: string, color: 'success' | 'error') {
    snackbarText.value = text
    snackbarColor.value = color
    snackbar.value = true
  }

  async function handleStep (stepId: string, label: string) {
    if (loadingStep.value) {
      return
    }

    if (!isStepEnabled(stepId)) {
      notify('Prozessschritte müssen in der vorgegebenen Reihenfolge ausgeführt werden.', 'error')
      return
    }

    loadingStep.value = stepId
    try {
      const result = await triggerService.triggerStep(stepId, digitalLink.value)
      executedSteps.value = new Set([...executedSteps.value, stepId])
      notify(`${label}: ${result.event_file} erzeugt`, 'success')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unbekannter Fehler'
      notify(message, 'error')
    } finally {
      loadingStep.value = null
    }
  }

  onMounted(resetSession)
</script>

<template>
  <v-container class="py-8" max-width="1200">
    <v-card>
      <v-card-title class="text-h5">
        Construct-X Demonstrator
      </v-card-title>

      <v-card-subtitle>
        GS1 SSCC Simulation — QR-Code Scan
      </v-card-subtitle>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-subtitle-2 mb-2">
              Aktuelle SSCC (GS1 Digital Link)
            </div>
            <code class="d-block text-body-2 mb-4 text-wrap">{{ digitalLink }}</code>

            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              variant="tonal"
              @click="resetSession"
            >
              Neue SSCC generieren
            </v-btn>
          </v-col>

          <v-col class="d-flex justify-center align-center" cols="12" md="6">
            <qrcode-vue
              v-if="digitalLink"
              :size="220"
              :value="digitalLink"
              level="M"
            />
          </v-col>
        </v-row>

        <v-divider class="my-6" />

        <div class="text-subtitle-1 mb-1">
          Prozessschritte
        </div>
        <div class="text-body-2 text-medium-emphasis mb-4">
          Schritte müssen der Reihe nach ausgeführt werden.
          <span v-if="allStepsCompleted"> Alle Schritte abgeschlossen.</span>
        </div>

        <div
          v-for="(story, storyIndex) in LIFECYCLE_STORIES"
          :key="story.title"
          class="story-section"
          :class="{ 'story-section--not-first': storyIndex > 0 }"
        >
          <div class="story-section__header">
            <div class="text-h6">
              {{ story.title }}
            </div>
            <div class="text-body-2 text-medium-emphasis">
              Schritt {{ storyIndex === 0 ? '1–3' : '4–7' }}
              <span v-if="isStoryCompleted(storyIndex)"> — abgeschlossen</span>
            </div>
          </div>

          <div
            class="step-row"
            :style="{ '--step-count': story.steps.length }"
          >
            <button
              v-for="step in story.steps"
              :key="step.id"
              class="step-button"
              :class="{
                'step-button--active': isStepEnabled(step.id),
                'step-button--completed': isStepCompleted(step.id),
                'step-button--disabled': !isStepEnabled(step.id) && !isStepCompleted(step.id),
              }"
              :disabled="!isStepEnabled(step.id) || loadingStep === step.id"
              type="button"
              @click="handleStep(step.id, step.label)"
            >
              <div class="step-button__icon">
                <v-img
                  :alt="step.label"
                  class="step-button__image"
                  cover
                  :src="step.image"
                />
                <v-progress-circular
                  v-if="loadingStep === step.id"
                  class="step-button__loading"
                  color="primary"
                  indeterminate
                  size="24"
                  width="2"
                />
                <v-icon
                  v-else-if="isStepCompleted(step.id)"
                  class="step-button__check"
                  color="success"
                  icon="mdi-check-circle"
                  size="22"
                />
              </div>
              <div class="step-button__content">
                <span class="step-button__number">{{ getStepNumber(step.id) }}</span>
                <span class="step-button__label">{{ step.label }}</span>
              </div>
            </button>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="4000"
    >
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.story-section--not-first {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  margin-top: 24px;
  padding-top: 24px;
}

.story-section__header {
  margin-bottom: 16px;
}

.step-row {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(var(--step-count), minmax(0, 260px));
  width: 100%;
}

.step-button {
  align-items: center;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: row;
  gap: 14px;
  max-width: 260px;
  padding: 16px 18px;
  text-align: left;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  width: 100%;
}

.step-button:hover:not(:disabled) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.step-button--active {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgb(var(--v-theme-primary));
}

.step-button--completed {
  border-color: rgb(var(--v-theme-success));
}

.step-button--disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.step-button:disabled {
  pointer-events: none;
}

.step-button__icon {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  height: 72px;
  justify-content: center;
  position: relative;
  width: 72px;
}

.step-button__image {
  border-radius: 10px;
  height: 72px;
  width: 72px;
}

.step-button__check {
  bottom: -4px;
  position: absolute;
  right: -4px;
}

.step-button__loading {
  bottom: -4px;
  position: absolute;
  right: -4px;
}

.step-button__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.step-button__number {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1;
}

.step-button__label {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.3;
}

@media (max-width: 960px) {
  .step-row {
    grid-template-columns: repeat(var(--step-count), minmax(200px, 260px));
    overflow-x: auto;
    padding-bottom: 8px;
  }
}
</style>
