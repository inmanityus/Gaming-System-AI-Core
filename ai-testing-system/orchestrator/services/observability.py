#!/usr/bin/env python3
"""
Observability Service
Structured logging, metrics, and tracing for report system.

P2: Production observability for monitoring and debugging.
"""

import structlog
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict, Any
from datetime import datetime
import time

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get structured logger
def get_logger(name: str = __name__):
    """Get structured logger instance."""
    return structlog.get_logger(name)


# Prometheus Metrics

# Report generation counter
report_generation_total = Counter(
    'report_generation_total',
    'Total report generation requests',
    ['format', 'status']
)

# Report generation duration
report_generation_duration = Histogram(
    'report_generation_duration_seconds',
    'Time to generate report',
    ['format'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

# PDF generation duration (separate metric for CPU-intensive operation)
pdf_generation_duration = Histogram(
    'pdf_generation_duration_seconds',
    'Time to generate PDF',
    buckets=(1, 5, 10, 30, 60, 120, 300)
)

# S3 operations
s3_upload_total = Counter(
    's3_upload_total',
    'Total S3 uploads',
    ['status']
)

s3_upload_duration = Histogram(
    's3_upload_duration_seconds',
    'Time to upload to S3',
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
)

# Database operations
db_query_total = Counter(
    'db_query_total',
    'Total database queries',
    ['operation', 'status']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1, 5)
)

# Cache operations
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

# Active reports gauge
active_reports = Gauge(
    'active_reports',
    'Number of reports currently being generated'
)

# Report queue depth
report_queue_depth = Gauge(
    'report_queue_depth',
    'Number of reports waiting to be generated'
)


class ObservabilityService:
    """
    Observability service for metrics and logging.
    
    Provides structured logging and Prometheus metrics.
    """
    
    @staticmethod
    def metrics_endpoint() -> Response:
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @staticmethod
    def track_report_generation(format: str, status: str):
        """Track report generation completion."""
        report_generation_total.labels(format=format, status=status).inc()
    
    @staticmethod
    def track_report_duration(format: str, duration: float):
        """Track report generation duration."""
        report_generation_duration.labels(format=format).observe(duration)
    
    @staticmethod
    def track_pdf_duration(duration: float):
        """Track PDF generation duration specifically."""
        pdf_generation_duration.observe(duration)
    
    @staticmethod
    def track_s3_upload(status: str, duration: float):
        """Track S3 upload operations."""
        s3_upload_total.labels(status=status).inc()
        s3_upload_duration.observe(duration)
    
    @staticmethod
    def track_db_query(operation: str, status: str, duration: float):
        """Track database query operations."""
        db_query_total.labels(operation=operation, status=status).inc()
        db_query_duration.labels(operation=operation).observe(duration)
    
    @staticmethod
    def track_cache_operation(operation: str, result: str):
        """Track cache operations."""
        cache_operations_total.labels(operation=operation, result=result).inc()
    
    @staticmethod
    def set_active_reports(count: int):
        """Set active reports gauge."""
        active_reports.set(count)
    
    @staticmethod
    def set_queue_depth(count: int):
        """Set queue depth gauge."""
        report_queue_depth.set(count)


# Context managers for automatic timing

class TimedOperation:
    """Context manager for timing operations with Prometheus."""
    
    def __init__(self, metric_func, *args, **kwargs):
        self.metric_func = metric_func
        self.args = args
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metric_func(duration, *self.args, **self.kwargs)


def timed_report_generation(format: str):
    """Time report generation and record metrics."""
    return TimedOperation(
        lambda d, f: ObservabilityService.track_report_duration(f, d),
        format
    )


def timed_pdf_generation():
    """Time PDF generation specifically."""
    return TimedOperation(
        lambda d: ObservabilityService.track_pdf_duration(d)
    )


def timed_s3_upload(status: str):
    """Time S3 upload operations."""
    return TimedOperation(
        lambda d, s: ObservabilityService.track_s3_upload(s, d),
        status
    )


def timed_db_query(operation: str, status: str = 'success'):
    """Time database query operations."""
    return TimedOperation(
        lambda d, op, st: ObservabilityService.track_db_query(op, st, d),
        operation,
        status
    )

