from temporalio import activity

from core.langfuse import start_trace

from ..ctx import RecordContext, TraceContext


@activity.defn
async def bootstrap_activity(record_ctx: RecordContext) -> TraceContext:
    activity.heartbeat()
    trace_id = start_trace(
        "land-record-pipeline",
        metadata={"record_pk": record_ctx.pk, "record_uuid": record_ctx.uuid},
    )
    return TraceContext(id=trace_id)
