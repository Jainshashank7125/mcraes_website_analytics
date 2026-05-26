import logging
import time
from typing import Optional
from urllib.parse import urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)
_otel_log_handler_attached = False


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def setup_telemetry(app=None) -> None:
    """
    Configure OpenTelemetry exporters/instrumentation.
    Safe-by-default: if disabled or dependencies are missing, app startup continues.
    """
    if not _as_bool(settings.OTEL_ENABLED, default=False):
        logger.info("OpenTelemetry disabled (OTEL_ENABLED=false)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.metrics import set_meter_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception as exc:
        logger.warning("OpenTelemetry packages unavailable; telemetry not started: %s", exc)
        return

    try:
        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
        scheme = urlparse(endpoint).scheme.lower()
        default_insecure = scheme not in {"https"}

        resource_attributes = {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.OTEL_SERVICE_VERSION,
            "deployment.environment": settings.OTEL_DEPLOYMENT_ENVIRONMENT,
        }
        # OTEL_RESOURCE_ATTRIBUTES has precedence over defaults when provided.
        resource_attributes.update(settings.otel_resource_attributes_dict)

        resource = Resource.create(
            resource_attributes
        )
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=_as_bool(settings.OTEL_EXPORTER_OTLP_INSECURE, default=default_insecure),
            headers=settings.otel_headers_dict,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)

        metric_exporter = OTLPMetricExporter(
            endpoint=endpoint,
            insecure=_as_bool(settings.OTEL_EXPORTER_OTLP_INSECURE, default=default_insecure),
            headers=settings.otel_headers_dict,
        )
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        set_meter_provider(meter_provider)
        meter = metrics.get_meter(__name__)

        LoggingInstrumentor().instrument(set_logging_format=True)
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        if _as_bool(settings.OTEL_LOGS_ENABLED, default=True):
            _configure_log_export(
                LoggerProvider=LoggerProvider,
                BatchLogRecordProcessor=BatchLogRecordProcessor,
                OTLPLogExporter=OTLPLogExporter,
                LoggingHandler=LoggingHandler,
                set_logger_provider=set_logger_provider,
                resource=resource,
                endpoint=endpoint,
                default_insecure=default_insecure,
            )

        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
            _attach_http_metrics_middleware(app, meter)

        logger.info(
            "OpenTelemetry initialized for service '%s' -> %s",
            resource_attributes.get("service.name", settings.OTEL_SERVICE_NAME),
            settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        )
    except Exception as exc:
        logger.exception("OpenTelemetry initialization failed: %s", exc)


def _configure_log_export(
    LoggerProvider,
    BatchLogRecordProcessor,
    OTLPLogExporter,
    LoggingHandler,
    set_logger_provider,
    resource,
    endpoint: str,
    default_insecure: bool,
) -> None:
    global _otel_log_handler_attached

    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(
        endpoint=endpoint,
        insecure=_as_bool(settings.OTEL_EXPORTER_OTLP_INSECURE, default=default_insecure),
        headers=settings.otel_headers_dict,
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    if not _otel_log_handler_attached:
        logging.getLogger().addHandler(LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider))
        _otel_log_handler_attached = True


def _attach_http_metrics_middleware(app, meter) -> None:
    """
    Attach lightweight HTTP metrics middleware for request count, duration, and errors.
    """
    if getattr(app.state, "_otel_metrics_middleware_installed", False):
        return

    request_counter = meter.create_counter(
        name="http.server.request.count",
        description="Total HTTP requests handled by FastAPI app",
        unit="1",
    )
    error_counter = meter.create_counter(
        name="http.server.error.count",
        description="Total HTTP requests resulting in 5xx status",
        unit="1",
    )
    latency_histogram = meter.create_histogram(
        name="http.server.request.duration",
        description="HTTP request duration",
        unit="ms",
    )

    @app.middleware("http")
    async def otel_metrics_middleware(request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        attrs = {
            "http.method": request.method,
            "http.route": request.url.path,
            "http.status_code": response.status_code,
        }
        request_counter.add(1, attrs)
        latency_histogram.record(duration_ms, attrs)
        if response.status_code >= 500:
            error_counter.add(1, attrs)
        return response

    app.state._otel_metrics_middleware_installed = True
