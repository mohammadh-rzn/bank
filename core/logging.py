import structlog

logger = structlog.get_logger('api')

def log_api_event(event_type, **kwargs):
    """Helper function for structured logging"""
    logger.info(
        event_type,
        **kwargs
    )