import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.resources import Resource

def setup_otel_tracing():
    # Set up resource attributes
    resource = Resource.create({
        "service.name": "django-banking-app",
        "service.version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    })

    # Configure the tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Configure OTLP exporter (for Jaeger, Zipkin, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument Django and other libraries
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def setup_otel_metrics():
    # Configure metric reader
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        ),
        export_interval_millis=5000,
    )
    
    # Configure meter provider
    meter_provider = MeterProvider(
        resource=Resource.create({
            "service.name": "django-banking-app",
            "service.version": "1.0.0",
        }),
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

# Call this in settings.py
setup_otel_metrics()