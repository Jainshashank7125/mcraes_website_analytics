const enabled = import.meta.env.VITE_DEBUG_LOG === 'true'

export const debugLog = (...args) => {
  if (enabled) console.log(...args)
}

export const debugWarn = (...args) => {
  if (enabled) console.warn(...args)
}

export const debugError = (...args) => {
  if (enabled) console.error(...args)
}
