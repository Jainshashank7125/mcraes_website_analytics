import { BatchSpanProcessor, WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { trace, SpanStatusCode } from '@opentelemetry/api'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web'
import { resourceFromAttributes } from '@opentelemetry/resources'
import { logs } from '@opentelemetry/api-logs'
import { LoggerProvider, BatchLogRecordProcessor } from '@opentelemetry/sdk-logs'
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http'

const parseHeaders = (raw) => {
  if (!raw) return {}
  return raw.split(',').reduce((acc, pair) => {
    const [key, ...rest] = pair.split('=')
    if (!key || rest.length === 0) return acc
    acc[key.trim()] = rest.join('=').trim()
    return acc
  }, {})
}

const postFrontendLogToBackend = async (level, message) => {
  try {
    const endpoint = '/api/v1/telemetry/frontend-log'
    const payload = {
      level,
      message,
      source: 'browser-console',
      metadata: {
        href: window.location.href,
        userAgent: navigator.userAgent,
      },
    }
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
      navigator.sendBeacon(endpoint, blob)
      return
    }
    await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    })
  } catch (_) {
    // Never disrupt app behavior due to logging failures.
  }
}

export const initTelemetry = () => {
  try {
    const enabled = (import.meta.env.VITE_OTEL_ENABLED || 'false').toLowerCase() === 'true'
    if (!enabled) return

    const collectorUrl =
      import.meta.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces'

    const resource = resourceFromAttributes({
      'service.name': import.meta.env.VITE_OTEL_SERVICE_NAME || 'mcraes-frontend',
      'service.version': import.meta.env.VITE_OTEL_SERVICE_VERSION || '1.0.0',
      'deployment.environment': import.meta.env.VITE_OTEL_DEPLOYMENT_ENVIRONMENT || 'staging',
    })

    const provider = new WebTracerProvider({ resource })

    provider.addSpanProcessor(
      new BatchSpanProcessor(
        new OTLPTraceExporter({
          url: collectorUrl,
          headers: parseHeaders(import.meta.env.VITE_OTEL_EXPORTER_OTLP_HEADERS),
        })
      )
    )

    // Keep frontend resilient: telemetry must never block app rendering.
    provider.register()

    registerInstrumentations({
      instrumentations: [
        getWebAutoInstrumentations({
          '@opentelemetry/instrumentation-fetch': {
            clearTimingResources: true,
            propagateTraceHeaderCorsUrls: [/.*/],
          },
          '@opentelemetry/instrumentation-xml-http-request': {
            propagateTraceHeaderCorsUrls: [/.*/],
          },
        }),
      ],
    })

    setupFrontendLogs(resource)
    emitBootstrapFrontendSpans()
  } catch (error) {
    console.warn('OpenTelemetry init failed; app continues without frontend telemetry.', error)
  }
}

const setupFrontendLogs = (resource) => {
  try {
    const logsEnabled = (import.meta.env.VITE_OTEL_LOGS_ENABLED || 'true').toLowerCase() === 'true'
    if (!logsEnabled) return

    const logsUrl =
      import.meta.env.VITE_OTEL_LOGS_EXPORTER_OTLP_ENDPOINT ||
      import.meta.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT?.replace(/\/v1\/traces$/, '/v1/logs')

    if (!logsUrl) return

    const loggerProvider = new LoggerProvider({ resource })
    loggerProvider.addLogRecordProcessor(
      new BatchLogRecordProcessor(
        new OTLPLogExporter({
          url: logsUrl,
          headers: parseHeaders(import.meta.env.VITE_OTEL_EXPORTER_OTLP_HEADERS),
        })
      )
    )
    logs.setGlobalLoggerProvider(loggerProvider)
    const otelLogger = logs.getLogger('frontend-browser-logger')

    const originalError = console.error
    const originalWarn = console.warn

    console.error = (...args) => {
      const message = args.map((item) => String(item)).join(' ')
      otelLogger.emit({
        severityNumber: 17,
        severityText: 'ERROR',
        body: message,
      })
      postFrontendLogToBackend('error', message)
      originalError(...args)
    }

    console.warn = (...args) => {
      const message = args.map((item) => String(item)).join(' ')
      otelLogger.emit({
        severityNumber: 13,
        severityText: 'WARN',
        body: message,
      })
      postFrontendLogToBackend('warn', message)
      originalWarn(...args)
    }
  } catch (error) {
    console.warn('Frontend OTEL logs init failed; continuing without log export.', error)
  }
}

const emitBootstrapFrontendSpans = () => {
  try {
    const tracer = trace.getTracer('frontend-bootstrap')
    const bootSpan = tracer.startSpan('frontend.app.bootstrap')
    bootSpan.setAttribute('frontend.url', window.location.href)
    bootSpan.setAttribute('frontend.path', window.location.pathname)
    bootSpan.end()

    window.addEventListener(
      'load',
      () => {
        const loadSpan = tracer.startSpan('frontend.window.load')
        loadSpan.setAttribute('frontend.path', window.location.pathname)
        loadSpan.end()
      },
      { once: true }
    )

    window.addEventListener('error', (event) => {
      const errorSpan = tracer.startSpan('frontend.window.error')
      errorSpan.setAttribute('frontend.error.message', String(event.message || 'unknown'))
      errorSpan.setStatus({ code: SpanStatusCode.ERROR })
      errorSpan.end()
    })
  } catch (_) {
    // Ignore telemetry failures.
  }
}
