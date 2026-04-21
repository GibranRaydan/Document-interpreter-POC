from django.conf import settings

from temporalio.common import RetryPolicy
from datetime import timedelta


DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError"],
)


def temporal_address() -> str:
    return getattr(settings, "TEMPORAL_ADDRESS", "localhost:7233")


def temporal_namespace() -> str:
    return getattr(settings, "TEMPORAL_NAMESPACE", "default")


def temporal_task_queue() -> str:
    return getattr(settings, "TEMPORAL_TASK_QUEUE", "courtney-landrecord")
