<script lang="ts" setup>
  import { ref } from 'vue'
  import { debugError } from '@/utils/debug'
  import { downloadSsccPrintPdf } from '@/utils/sscc-print-pdf'

  const model = defineModel<boolean>({ default: false })

  const count = ref(10)
  const isGenerating = ref(false)
  const errorMessage = ref('')

  const MIN_COUNT = 1
  const MAX_COUNT = 100

  function resetForm () {
    count.value = 10
    errorMessage.value = ''
    isGenerating.value = false
  }

  async function handleGenerate () {
    if (isGenerating.value) {
      return
    }

    const normalizedCount = Math.trunc(count.value)
    if (normalizedCount < MIN_COUNT || normalizedCount > MAX_COUNT) {
      errorMessage.value = `Bitte eine Zahl zwischen ${MIN_COUNT} und ${MAX_COUNT} eingeben.`
      return
    }

    isGenerating.value = true
    errorMessage.value = ''

    try {
      await downloadSsccPrintPdf(normalizedCount)
      model.value = false
      resetForm()
    } catch (error) {
      debugError('sscc-print', 'Failed to generate SSCC print PDF', error)
      errorMessage.value = error instanceof Error
        ? error.message
        : 'PDF konnte nicht erzeugt werden.'
    } finally {
      isGenerating.value = false
    }
  }
</script>

<template>
  <v-dialog
    v-model="model"
    max-width="420"
    @after-leave="resetForm"
  >
    <v-card rounded="lg" title="Generate SSCC Prints">
      <v-card-text>
        <p class="mb-4 text-medium-emphasis">
          Erzeugt ein PDF mit GS1-konformen SSCC-QR-Codes zum Ausdrucken.
        </p>

        <v-text-field
          v-model.number="count"
          :disabled="isGenerating"
          hide-details="auto"
          label="Anzahl SSCCs"
          :max="MAX_COUNT"
          :min="MIN_COUNT"
          type="number"
          variant="outlined"
        />

        <v-alert
          v-if="errorMessage"
          class="mt-4"
          density="compact"
          type="error"
          variant="tonal"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          :disabled="isGenerating"
          rounded="lg"
          variant="text"
          @click="model = false"
        >
          Abbrechen
        </v-btn>
        <v-btn
          color="primary"
          :disabled="isGenerating"
          :loading="isGenerating"
          prepend-icon="mdi-file-pdf-box"
          rounded="lg"
          variant="flat"
          @click="handleGenerate"
        >
          Generate
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
