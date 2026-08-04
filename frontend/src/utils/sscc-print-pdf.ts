import { jsPDF } from 'jspdf'
import QRCode from 'qrcode'
import { generateSsccBatch } from '@/utils/epcis-session'
import {
  SSCC_DIGITS_LENGTH,
  isValidSsccDigits,
  ssccDigitsFromDigitalLink,
} from '@/utils/sscc-check-digit'

const PAGE_WIDTH_MM = 210
const PAGE_HEIGHT_MM = 297
const MARGIN_MM = 12
const COLS = 3
const QR_SIZE_MM = 38
const CELL_HEIGHT_MM = 56
const COL_WIDTH_MM = (PAGE_WIDTH_MM - MARGIN_MM * 2) / COLS
const FIRST_PAGE_HEADER_MM = 12
const FIRST_PAGE_ROWS = Math.floor(
  (PAGE_HEIGHT_MM - MARGIN_MM * 2 - FIRST_PAGE_HEADER_MM) / CELL_HEIGHT_MM,
)
const OTHER_PAGE_ROWS = Math.floor((PAGE_HEIGHT_MM - MARGIN_MM * 2) / CELL_HEIGHT_MM)

function pageLayout (index: number): {
  page: number
  col: number
  row: number
  headerOffset: number
} {
  if (index < FIRST_PAGE_ROWS * COLS) {
    return {
      page: 0,
      col: index % COLS,
      row: Math.floor(index / COLS),
      headerOffset: FIRST_PAGE_HEADER_MM,
    }
  }

  const remaining = index - FIRST_PAGE_ROWS * COLS
  const indexOnLaterPages = remaining
  const labelsPerLaterPage = OTHER_PAGE_ROWS * COLS
  const page = 1 + Math.floor(indexOnLaterPages / labelsPerLaterPage)
  const indexOnPage = indexOnLaterPages % labelsPerLaterPage

  return {
    page,
    col: indexOnPage % COLS,
    row: Math.floor(indexOnPage / COLS),
    headerOffset: 0,
  }
}

export async function downloadSsccPrintPdf (count: number): Promise<void> {
  const ssccs = generateSsccBatch(count)
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  let currentPage = -1

  for (let index = 0; index < ssccs.length; index += 1) {
    const digitalLink = ssccs[index]!
    const digits = ssccDigitsFromDigitalLink(digitalLink)

    if (digits.length !== SSCC_DIGITS_LENGTH || !isValidSsccDigits(digits)) {
      throw new Error(`Refusing to print invalid SSCC at index ${index}: ${digitalLink}`)
    }

    const layout = pageLayout(index)

    if (layout.page !== currentPage) {
      if (currentPage >= 0) {
        doc.addPage()
      }
      currentPage = layout.page

      if (layout.page === 0) {
        doc.setFont('helvetica', 'bold')
        doc.setFontSize(13)
        doc.text('Construct-X SSCC Print Labels', PAGE_WIDTH_MM / 2, MARGIN_MM + 4, {
          align: 'center',
        })
      }
    }

    const cellX = MARGIN_MM + layout.col * COL_WIDTH_MM
    const qrY = MARGIN_MM + layout.headerOffset + layout.row * CELL_HEIGHT_MM
    const qrX = cellX + (COL_WIDTH_MM - QR_SIZE_MM) / 2

    const qrDataUrl = await QRCode.toDataURL(digitalLink, {
      errorCorrectionLevel: 'M',
      margin: 1,
      width: 256,
    })

    doc.addImage(qrDataUrl, 'PNG', qrX, qrY, QR_SIZE_MM, QR_SIZE_MM)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(7)
    doc.text(
      digits,
      cellX + COL_WIDTH_MM / 2,
      qrY + QR_SIZE_MM + 4,
      { align: 'center', maxWidth: COL_WIDTH_MM - 4 },
    )

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(5)
    doc.text(
      digitalLink,
      cellX + COL_WIDTH_MM / 2,
      qrY + QR_SIZE_MM + 8,
      { align: 'center', maxWidth: COL_WIDTH_MM - 4 },
    )
  }

  const timestamp = new Date().toISOString().slice(0, 19).replaceAll(':', '-')
  doc.save(`sscc-prints-${count}-${timestamp}.pdf`)
}
