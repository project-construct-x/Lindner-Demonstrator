<script lang="ts" setup>
  import { Html5Qrcode } from 'html5-qrcode'
  import jsQR from 'jsqr'
  import { nextTick, ref, useId, watch } from 'vue'
  import { debugError, debugLog, debugWarn } from '@/utils/debug'
  import { normalizeSsccDigitalLink } from '@/utils/epcis-session'

  const model = defineModel<boolean>({ default: false })

  const emit = defineEmits<{
    scanned: [value: string]
  }>()

  const scannerRegionId = `qr-scanner-${useId()}`
  const scannerError = ref('')
  const isStarting = ref(false)

  let html5QrCode: Html5Qrcode | null = null
  let canvasScanFrameId = 0
  let canvasScanAttempts = 0
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let stopped = false

  async function stopScanner () {
    debugLog('scanner', 'Stopping camera scanner')
    stopped = true

    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }

    if (canvasScanFrameId) {
      cancelAnimationFrame(canvasScanFrameId)
      canvasScanFrameId = 0
    }

    if (!html5QrCode) {
      return
    }

    const scanner = html5QrCode
    html5QrCode = null

    try {
      if (scanner.isScanning) {
        await scanner.stop()
      }
      await scanner.clear()
    } catch (error) {
      debugWarn('scanner', 'Error while stopping scanner', error)
    }
  }

  function handleScanResult (value: string, source: 'html5-qrcode' | 'jsqr') {
    if (stopped) {
      return
    }

    const normalizedDigitalLink = normalizeSsccDigitalLink(value)
    if (!normalizedDigitalLink) {
      debugWarn('scanner', 'Ignored non-SSCC QR code', { source, value })
      return
    }

    debugLog('scanner', 'SSCC QR code detected', {
      source,
      value: normalizedDigitalLink,
    })

    stopped = true
    emit('scanned', normalizedDigitalLink)
    model.value = false
    stopScanner()
  }

  function startScanHeartbeat () {
    heartbeatTimer = setInterval(() => {
      debugLog('scanner', 'Scanning...', {
        canvasAttempts: canvasScanAttempts,
      })
    }, 2000)
  }

  function startCanvasFallback (videoElement: HTMLVideoElement) {
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d', { willReadFrequently: true })

    if (!context) {
      debugWarn('scanner', 'Canvas fallback unavailable')
      return
    }

    const scanFrame = () => {
      if (stopped) {
        return
      }

      canvasScanAttempts += 1

      if (
        videoElement.videoWidth > 0
        && videoElement.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA
      ) {
        canvas.width = videoElement.videoWidth
        canvas.height = videoElement.videoHeight
        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height)

        const imageData = context.getImageData(0, 0, canvas.width, canvas.height)
        const result = jsQR(imageData.data, imageData.width, imageData.height, {
          inversionAttempts: 'attemptBoth',
        })

        if (result?.data) {
          debugLog('scanner', 'jsQR raw decode', { decodedText: result.data })
          handleScanResult(result.data, 'jsqr')
          return
        }
      }

      canvasScanFrameId = requestAnimationFrame(scanFrame)
    }

    canvasScanFrameId = requestAnimationFrame(scanFrame)
    debugLog('scanner', 'jsQR canvas fallback started')
  }

  async function startScanner () {
    stopped = false
    scannerError.value = ''
    isStarting.value = true
    canvasScanAttempts = 0

    await nextTick()

    try {
      html5QrCode = new Html5Qrcode(scannerRegionId, {
        verbose: false,
      })

      const cameras = await Html5Qrcode.getCameras()
      debugLog('scanner', 'Available video devices', cameras)

      const preferredCamera = cameras.find(camera =>
        /back|rear|environment/i.test(camera.label),
      ) ?? cameras[0]

      if (!preferredCamera) {
        throw new Error('Keine Kamera gefunden.')
      }

      debugLog('scanner', 'Selected camera device', preferredCamera)

      await html5QrCode.start(
        preferredCamera.id,
        {
          fps: 15,
          disableFlip: false,
        },
        (decodedText, decodedResult) => {
          debugLog('scanner', 'html5-qrcode raw decode', {
            decodedText,
            format: decodedResult.result.format?.formatName,
          })
          handleScanResult(decodedText, 'html5-qrcode')
        },
        () => {
          // Expected on most frames when no QR code is visible.
        },
      )

      debugLog('scanner', 'html5-qrcode scanning started')

      const videoElement = document
        .querySelector(`#${scannerRegionId} video`)

      if (videoElement instanceof HTMLVideoElement) {
        debugLog('scanner', 'Video element ready for fallback', {
          videoWidth: videoElement.videoWidth,
          videoHeight: videoElement.videoHeight,
        })
        startCanvasFallback(videoElement)
      } else {
        debugWarn('scanner', 'Video element not found for canvas fallback')
      }

      startScanHeartbeat()
    } catch (error) {
      debugError('scanner', 'Failed to start camera scanner', error)
      scannerError.value = error instanceof Error
        ? error.message
        : 'Kamerazugriff fehlgeschlagen.'
      await stopScanner()
    } finally {
      isStarting.value = false
    }
  }

  function onDialogOpened () {
    debugLog('scanner', 'Scanner dialog opened')
    startScanner()
  }

  watch(model, open => {
    if (open) {
      return
    }

    debugLog('scanner', 'Scanner dialog closed')
    stopScanner()
    scannerError.value = ''
  })
</script>

<template>
  <v-dialog
    v-model="model"
    max-width="560"
    scrollable
    @after-enter="onDialogOpened"
  >
    <v-card class="scanner-dialog" rounded="lg">
      <v-card-title class="scanner-dialog__title">
        <v-icon class="mr-2" icon="mdi-qrcode-scan" />
        SSCC scannen
      </v-card-title>

      <v-card-text class="scanner-dialog__content">
        <p class="scanner-dialog__hint">
          Richte die Kamera auf einen SSCC-QR-Code. Der gelesene Wert wird automatisch übernommen.
        </p>

        <div class="scanner-dialog__viewport-wrap">
          <div
            :id="scannerRegionId"
            class="scanner-dialog__viewport"
          />

          <div
            v-if="isStarting"
            class="scanner-dialog__loading"
          >
            <v-progress-circular
              color="primary"
              indeterminate
              size="42"
            />
          </div>
        </div>

        <v-alert
          v-if="scannerError"
          class="scanner-dialog__error"
          color="error"
          density="compact"
          icon="mdi-alert-circle-outline"
          variant="tonal"
        >
          {{ scannerError }}
        </v-alert>
      </v-card-text>

      <v-card-actions class="scanner-dialog__actions">
        <v-spacer />

        <v-btn
          color="primary"
          rounded="lg"
          variant="flat"
          @click="model = false"
        >
          Schließen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.scanner-dialog {
  background: #111827;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.scanner-dialog__title {
  color: #f1f5f9;
  font-size: 1.125rem;
  font-weight: 700;
  padding: 20px 24px 12px;
}

.scanner-dialog__content {
  padding: 8px 24px 20px;
}

.scanner-dialog__hint {
  color: #94a3b8;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0 0 16px;
}

.scanner-dialog__viewport-wrap {
  position: relative;
}

.scanner-dialog__viewport {
  aspect-ratio: 4 / 3;
  background: #020617;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 16px;
  min-height: 280px;
  overflow: hidden;
  position: relative;
}

.scanner-dialog__viewport :deep(video) {
  display: block;
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.scanner-dialog__loading {
  align-items: center;
  background: rgba(2, 6, 23, 0.55);
  border-radius: 16px;
  display: flex;
  inset: 0;
  justify-content: center;
  pointer-events: none;
  position: absolute;
  z-index: 2;
}

.scanner-dialog__error {
  margin-top: 16px;
}

.scanner-dialog__actions {
  padding: 12px 24px 20px;
}
</style>
