const PREFIX = '[Construct-X]'

function formatScope (scope: string): string {
  return `${PREFIX} [${scope}]`
}

export function debugLog (scope: string, message: string, data?: unknown): void {
  if (data === undefined) {
    console.log(formatScope(scope), message)
    return
  }

  console.log(formatScope(scope), message, data)
}

export function debugWarn (scope: string, message: string, data?: unknown): void {
  if (data === undefined) {
    console.warn(formatScope(scope), message)
    return
  }

  console.warn(formatScope(scope), message, data)
}

export function debugError (scope: string, message: string, data?: unknown): void {
  if (data === undefined) {
    console.error(formatScope(scope), message)
    return
  }

  console.error(formatScope(scope), message, data)
}
