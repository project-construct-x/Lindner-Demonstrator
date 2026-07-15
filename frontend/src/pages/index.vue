<script lang="ts" setup>
  import { computed, onMounted, ref } from 'vue'
  import QrcodeVue from 'qrcode.vue'
  import { triggerService } from '@/services/trigger.service'
  import { LIFECYCLE_STEPS } from '@/constants/steps'
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

  function isStepCompleted (stepId: string): boolean {
    return executedSteps.value.has(stepId)
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
  <v-container class="py-8" max-width="900">
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

        <v-row>
          <v-col
            v-for="(step, index) in LIFECYCLE_STEPS"
            :key="step.id"
            cols="12"
            sm="6"
          >
            <v-btn
              block
              :color="isStepCompleted(step.id) ? 'success' : isStepEnabled(step.id) ? 'primary' : undefined"
              :disabled="!isStepEnabled(step.id)"
              :loading="loadingStep === step.id"
              :prepend-icon="isStepCompleted(step.id) ? 'mdi-check' : undefined"
              :variant="isStepEnabled(step.id) ? 'elevated' : 'tonal'"
              @click="handleStep(step.id, step.label)"
            >
              {{ index + 1 }}. {{ step.label }}
            </v-btn>
          </v-col>
        </v-row>
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
