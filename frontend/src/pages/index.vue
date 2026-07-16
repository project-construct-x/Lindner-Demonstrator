<script lang="ts" setup>
  import { computed, onMounted, ref, useId } from 'vue'
  import QrcodeVue from 'qrcode.vue'
  import { triggerService } from '@/services/trigger.service'
  import { LIFECYCLE_STEPS, LIFECYCLE_STORIES } from '@/constants/steps'
  import {
    createEventSession,
    createStepContext,
    formatEventTimeZoneOffset,
    type EventSession,
  } from '@/utils/epcis-session'
  import constructXLogo from '@/assets/cx.jpg'
  import { env } from '@/config/env'

  const swaggerUrl = `${env.backendBaseUrl}/docs`

  const eventSession = ref<EventSession | null>(null)
  const digitalLink = ref('')
  const qrGradientId = useId()
  const executedSteps = ref<Set<string>>(new Set())
  const loadingStep = ref<string | null>(null)
  const snackbar = ref(false)
  const snackbarText = ref('')
  const snackbarColor = ref<'success' | 'error'>('success')
  const infoDialogOpen = ref(false)

  const sessionInfoRows = computed(() => {
    if (!eventSession.value) {
      return []
    }

    const session = eventSession.value
    return [
      { label: 'SSCC', value: session.sscc },
      { label: 'LGTIN 1', value: session.lgtin1 },
      { label: 'LGTIN 2', value: session.lgtin2 },
      { label: 'Despatch Advice', value: session.desadv },
      { label: 'Purchase Order', value: session.po },
      { label: 'Zeitzone', value: formatEventTimeZoneOffset(new Date()) },
    ]
  })

  const completedStepLabels = computed(() =>
    LIFECYCLE_STEPS
      .filter(step => executedSteps.value.has(step.id))
      .map(step => `${getStepNumber(step.id)}. ${step.label}`),
  )

  const nextStepIndex = computed(() =>
    LIFECYCLE_STEPS.findIndex(step => !executedSteps.value.has(step.id)),
  )

  const allStepsCompleted = computed(() => nextStepIndex.value === -1)

  const progressPercent = computed(() =>
    Math.round((executedSteps.value.size / LIFECYCLE_STEPS.length) * 100),
  )

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

  function storyProgress (storyIndex: number): number {
    const story = LIFECYCLE_STORIES[storyIndex]
    const done = story.steps.filter(step => executedSteps.value.has(step.id)).length
    return Math.round((done / story.steps.length) * 100)
  }

  function resetSession () {
    const session = createEventSession()
    eventSession.value = session
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
      if (!eventSession.value) {
        throw new Error('Keine aktive SSCC-Sitzung')
      }

      const result = await triggerService.triggerStep(
        stepId,
        eventSession.value,
        createStepContext(),
      )
      executedSteps.value = new Set([...executedSteps.value, stepId])
      notify(
        `${label}: ${result.document_file} erzeugt (${result.event_count} Events)`,
        'success',
      )
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
  <v-container class="demo py-10" max-width="1200">
    <header class="demo__hero">
      <div class="demo__logo-wrap">
        <img
          alt="Construct-X"
          class="demo__logo"
          :src="constructXLogo"
        >
      </div>

      <div class="demo__hero-text">
        <div class="demo__hero-headline">
          <h1 class="demo__title">
            Construct-X Demonstrator
          </h1>
        </div>
        <p class="demo__subtitle">
          Simuliere den Materiallebenszyklus per QR-Code-Scan — von der Fertigung bis zur Aufbereitung.
        </p>
      </div>

      <div class="demo__hero-aside">
        <v-btn
          class="demo__api-btn"
          color="primary"
          :href="swaggerUrl"
          prepend-icon="mdi-book-open-page-variant"
          rel="noopener noreferrer"
          rounded="lg"
          size="small"
          target="_blank"
          variant="tonal"
        >
          Swagger API
        </v-btn>
      </div>
    </header>

    <section class="sscc-card">
      <div class="sscc-card__qr">
        <qrcode-vue
          v-if="digitalLink"
          :id="qrGradientId"
          background="transparent"
          class="sscc-card__qr-code"
          gradient
          gradient-end-color="#5a9fd4"
          gradient-start-color="#f8fafc"
          gradient-type="linear"
          :radius="0"
          :size="132"
          :value="digitalLink"
          level="M"
          render-as="svg"
        />
      </div>

      <div class="sscc-card__form">
        <v-text-field
          class="sscc-card__uri"
          density="comfortable"
          hide-details
          :model-value="digitalLink"
          prepend-inner-icon="mdi-link-variant"
          readonly
          variant="outlined"
        />
        <div class="sscc-card__actions">
          <v-btn
            class="sscc-card__btn"
            color="primary"
            prepend-icon="mdi-refresh"
            rounded="lg"
            size="large"
            variant="flat"
            @click="resetSession"
          >
            Neu generieren
          </v-btn>
          <v-btn
            class="sscc-card__btn sscc-card__btn--info"
            color="primary"
            prepend-icon="mdi-information-outline"
            rounded="lg"
            size="large"
            variant="tonal"
            @click="infoDialogOpen = true"
          >
            Verwendete Daten Anzeigen
          </v-btn>
        </div>
      </div>
    </section>

    <section class="steps-section">
      <div class="steps-section__header">
        <div class="steps-section__heading">
          <h2 class="steps-section__title">
            Prozessschritte
          </h2>
          <p class="steps-section__hint">
            Schritte müssen der Reihe nach ausgeführt werden.
          </p>
        </div>

        <div class="demo__progress-card">
          <div class="demo__progress-label">
            <span>Fortschritt</span>
            <span class="demo__progress-value">{{ executedSteps.size }} / {{ LIFECYCLE_STEPS.length }}</span>
          </div>
          <v-progress-linear
            class="demo__progress-bar"
            :color="allStepsCompleted ? 'success' : 'primary'"
            height="8"
            :model-value="progressPercent"
            rounded
          />
          <span v-if="allStepsCompleted" class="demo__progress-done">
            <v-icon icon="mdi-check-decagram" size="16" />
            Alle Schritte abgeschlossen
          </span>
        </div>
      </div>

      <div
        v-for="(story, storyIndex) in LIFECYCLE_STORIES"
        :key="story.title"
        class="story-section"
        :class="{
          'story-section--einbau': storyIndex === 0,
          'story-section--rueckbau': storyIndex === 1,
        }"
      >
        <div class="story-section__header">
          <div
            class="story-section__badge"
            :class="storyIndex === 0 ? 'story-section__badge--einbau' : 'story-section__badge--rueckbau'"
          >
            <v-icon
              :icon="storyIndex === 0 ? 'mdi-arrow-down-bold' : 'mdi-arrow-up-bold'"
              size="16"
            />
            {{ story.title }}
          </div>
          <div class="story-section__meta">
            <span class="story-section__range">Schritt {{ storyIndex === 0 ? '1–3' : '4–7' }}</span>
            <v-chip
              v-if="isStoryCompleted(storyIndex)"
              color="success"
              prepend-icon="mdi-check"
              size="small"
              variant="tonal"
            >
              Abgeschlossen
            </v-chip>
            <span v-else class="story-section__percent">{{ storyProgress(storyIndex) }}%</span>
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
            <div class="step-button__glow" />
            <div class="step-button__icon">
              <v-img
                :alt="step.label"
                class="step-button__image"
                cover
                :src="step.image"
              />
              <v-progress-circular
                v-if="loadingStep === step.id"
                class="step-button__status"
                color="primary"
                indeterminate
                size="26"
                width="2"
              />
              <v-icon
                v-else-if="isStepCompleted(step.id)"
                class="step-button__status step-button__status--done"
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
    </section>

    <v-dialog
      v-model="infoDialogOpen"
      max-width="640"
      scrollable
    >
      <v-card class="info-dialog" rounded="lg">
        <v-card-title class="info-dialog__title">
          <v-icon class="mr-2" icon="mdi-information-outline" />
          Aktuelle Sitzungsdaten
        </v-card-title>

        <v-card-text class="info-dialog__content">
          <div
            v-for="row in sessionInfoRows"
            :key="row.label"
            class="info-dialog__row"
          >
            <span class="info-dialog__label">{{ row.label }}</span>
            <code class="info-dialog__value">{{ row.value }}</code>
          </div>

          <div class="info-dialog__row">
            <span class="info-dialog__label">Fortschritt</span>
            <span class="info-dialog__value info-dialog__value--text">
              {{ executedSteps.size }} / {{ LIFECYCLE_STEPS.length }} Schritte
            </span>
          </div>

          <div class="info-dialog__row info-dialog__row--stacked">
            <span class="info-dialog__label">Abgeschlossene Schritte</span>
            <span
              v-if="completedStepLabels.length === 0"
              class="info-dialog__value info-dialog__value--text info-dialog__value--muted"
            >
              Noch keine Schritte ausgeführt
            </span>
            <ul
              v-else
              class="info-dialog__steps"
            >
              <li
                v-for="stepLabel in completedStepLabels"
                :key="stepLabel"
              >
                {{ stepLabel }}
              </li>
            </ul>
          </div>
        </v-card-text>

        <v-card-actions class="info-dialog__actions">
          <v-spacer />
          <v-btn
            color="primary"
            rounded="lg"
            variant="flat"
            @click="infoDialogOpen = false"
          >
            Schließen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar"
      class="demo-snackbar"
      :color="snackbarColor"
      location="top"
      :timeout="4000"
    >
      <v-icon
        class="mr-2"
        :icon="snackbarColor === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'"
      />
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.demo {
  position: relative;
}

.demo__hero {
  align-items: flex-start;
  display: flex;
  gap: 24px;
  justify-content: space-between;
  margin-bottom: 32px;
}

.demo__logo-wrap {
  align-items: center;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-shrink: 0;
  height: 96px;
  justify-content: center;
  padding: 12px 16px;
  width: 96px;
}

.demo__logo {
  display: block;
  height: 100%;
  max-height: 72px;
  object-fit: contain;
  width: 100%;
}

.demo__hero-text {
  flex: 1;
  min-width: 0;
}

.demo__hero-headline {
  margin-bottom: 8px;
}

.demo__title {
  background: linear-gradient(135deg, #f8fafc 0%, #337ab7 55%, #5a9fd4 100%);
  background-clip: text;
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 0;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.demo__subtitle {
  color: #94a3b8;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
  max-width: 520px;
}

.demo__api-btn {
  align-self: flex-end;
  text-transform: none;
}

.demo__hero-aside {
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.demo__progress-card {
  backdrop-filter: blur(12px);
  background: rgba(17, 24, 39, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 16px;
  flex-shrink: 0;
  min-width: 220px;
  padding: 16px 20px;
  width: 260px;
}

.demo__progress-label {
  color: #94a3b8;
  display: flex;
  font-size: 0.8125rem;
  font-weight: 500;
  justify-content: space-between;
  margin-bottom: 10px;
}

.demo__progress-value {
  color: #e2e8f0;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.demo__progress-bar {
  box-shadow: 0 0 12px rgba(51, 122, 183, 0.2);
}

.demo__progress-done {
  align-items: center;
  color: #34d399;
  display: flex;
  font-size: 0.75rem;
  font-weight: 600;
  gap: 4px;
  margin-top: 10px;
}

.sscc-card {
  align-items: flex-start;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  gap: 28px;
  margin-bottom: 36px;
  margin-top: 50px;
  padding-bottom: 36px;
}

.sscc-card__qr {
  flex-shrink: 0;
  line-height: 0;
  width: 132px;
}

.sscc-card__qr-code {
  display: block;
}

.sscc-card__qr-code :deep(svg) {
  display: block;
  height: 132px;
  width: 132px;
}

.sscc-card__form {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  max-width: 600px;
  min-width: 0;
}

.sscc-card__uri {
  font-family: 'Roboto Mono', monospace;
  margin-top: 0;
}

.sscc-card__uri :deep(.v-input) {
  margin-top: 0;
}

.sscc-card__uri :deep(.v-field) {
  background: rgba(15, 23, 42, 0.45);
  border-radius: 12px;
}

.sscc-card__uri :deep(.v-field__outline) {
  --v-field-border-opacity: 0.18;
  color: rgba(148, 163, 184, 0.6);
}

.sscc-card__uri :deep(.v-field--focused .v-field__outline) {
  color: #337ab7;
}

.sscc-card__uri :deep(.v-field__prepend-inner .v-icon) {
  color: rgba(51, 122, 183, 0.7);
  opacity: 1;
}

.sscc-card__uri :deep(.v-field__input) {
  color: #5a9fd4;
  font-size: 0.8125rem;
  letter-spacing: 0.01em;
}

.sscc-card__actions {
  align-items: stretch;
  display: flex;
  flex-wrap: nowrap;
  gap: 12px;
  width: 100%;
}

.sscc-card__btn {
  box-shadow: 0 4px 16px rgba(51, 122, 183, 0.22);
  flex: 1;
  font-weight: 600;
  letter-spacing: 0.02em;
  min-width: 0;
  text-transform: none;
}

.sscc-card__btn--info {
  box-shadow: none;
}

.steps-section__header {
  align-items: flex-start;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 24px;
}

.steps-section__heading {
  min-width: 0;
}

.steps-section__title {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0;
}

.steps-section__hint {
  color: #64748b;
  font-size: 0.875rem;
  margin-top: 4px;
}

.story-section {
  backdrop-filter: blur(12px);
  background: rgba(17, 24, 39, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 20px;
  margin-bottom: 20px;
  overflow: hidden;
  padding: 24px;
  position: relative;
}

.story-section--einbau {
  border-left: 3px solid #4aad6f;
}

.story-section--rueckbau {
  border-left: 3px solid #e8913a;
}

.story-section__header {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 20px;
}

.story-section__badge {
  align-items: center;
  border-radius: 10px;
  display: inline-flex;
  font-size: 1.125rem;
  font-weight: 700;
  gap: 8px;
  letter-spacing: -0.01em;
  padding: 6px 14px;
}

.story-section__badge--einbau {
  background: rgba(74, 173, 111, 0.12);
  color: #4aad6f;
}

.story-section__badge--rueckbau {
  background: rgba(232, 145, 58, 0.12);
  color: #e8913a;
}

.story-section__meta {
  align-items: center;
  display: flex;
  gap: 12px;
}

.story-section__range {
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 500;
}

.story-section__percent {
  color: #94a3b8;
  font-size: 0.8125rem;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.step-row {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(var(--step-count), minmax(0, 260px));
  width: 100%;
}

.step-button {
  align-items: center;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: row;
  gap: 14px;
  max-width: 260px;
  overflow: hidden;
  padding: 16px 18px;
  position: relative;
  text-align: left;
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
  width: 100%;
}

.step-button__glow {
  background: radial-gradient(circle at 50% 0%, rgba(51, 122, 183, 0.15), transparent 70%);
  inset: 0;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 0.25s;
}

.step-button:hover:not(:disabled) {
  border-color: rgba(148, 163, 184, 0.25);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  transform: translateY(-2px);
}

.step-button:hover:not(:disabled) .step-button__glow {
  opacity: 1;
}

.step-button--active {
  background: rgba(51, 122, 183, 0.06);
  border-color: rgba(51, 122, 183, 0.5);
  box-shadow:
    0 0 0 1px rgba(51, 122, 183, 0.3),
    0 0 24px rgba(51, 122, 183, 0.15);
}

.step-button--active .step-button__glow {
  opacity: 1;
}

.step-button--active .step-button__number {
  color: #337ab7;
}

.step-button--completed {
  background: rgba(52, 211, 153, 0.04);
  border-color: rgba(52, 211, 153, 0.35);
}

.step-button--completed .step-button__number {
  color: #34d399;
}

.step-button--disabled {
  cursor: not-allowed;
  opacity: 0.45;
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
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  height: 72px;
  width: 72px;
}

.step-button__status {
  bottom: -4px;
  position: absolute;
  right: -4px;
}

.step-button__status--done {
  color: #34d399;
  filter: drop-shadow(0 0 6px rgba(52, 211, 153, 0.5));
}

.step-button__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.step-button__number {
  color: #64748b;
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  line-height: 1;
  transition: color 0.25s;
}

.step-button__label {
  color: #e2e8f0;
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.3;
}

@media (max-width: 960px) {
  .demo__hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .demo__hero-text {
    width: 100%;
  }

  .demo__hero-aside {
    align-self: stretch;
    min-width: 0;
    width: 100%;
  }

  .sscc-card {
    align-items: flex-start;
    flex-direction: column;
    gap: 20px;
  }

  .sscc-card__qr {
    width: auto;
  }

  .sscc-card__form {
    max-width: 100%;
    width: 100%;
  }

  .sscc-card__actions {
    width: 100%;
  }

  .sscc-card__btn {
    flex: 1;
    min-width: 0;
  }

  .steps-section__header {
    align-items: stretch;
    flex-direction: column;
  }

  .demo__progress-card {
    width: 100%;
  }

  .step-row {
    grid-template-columns: repeat(var(--step-count), minmax(200px, 260px));
    overflow-x: auto;
    padding-bottom: 8px;
  }
}

.info-dialog {
  background: #111827;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.info-dialog__title {
  color: #f1f5f9;
  font-size: 1.125rem;
  font-weight: 700;
  padding: 20px 24px 12px;
}

.info-dialog__content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 24px 20px;
}

.info-dialog__row {
  display: grid;
  gap: 6px;
  grid-template-columns: 140px minmax(0, 1fr);
}

.info-dialog__row--stacked {
  grid-template-columns: 1fr;
}

.info-dialog__label {
  color: #94a3b8;
  font-size: 0.8125rem;
  font-weight: 600;
}

.info-dialog__value {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 8px;
  color: #5a9fd4;
  display: block;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  overflow-wrap: anywhere;
  padding: 8px 10px;
  word-break: break-word;
}

.info-dialog__value--text {
  background: transparent;
  border: 0;
  color: #e2e8f0;
  font-family: inherit;
  font-size: 0.875rem;
  padding: 0;
}

.info-dialog__value--muted {
  color: #64748b;
}

.info-dialog__steps {
  color: #e2e8f0;
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0;
  padding-left: 1.1rem;
}

.info-dialog__actions {
  padding: 12px 24px 20px;
}

@media (max-width: 600px) {
  .info-dialog__row {
    grid-template-columns: 1fr;
  }
}
</style>
