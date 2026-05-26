from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger("frontend.telemetry")


class FrontendLogPayload(BaseModel):
    level: str
    message: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/telemetry/frontend-log")
async def ingest_frontend_log(payload: FrontendLogPayload):
    level = (payload.level or "info").lower()
    extra = {
        "frontend_source": payload.source or "browser",
        "frontend_metadata": payload.metadata or {},
    }
    text = f"[frontend:{extra['frontend_source']}] {payload.message}"

    if level == "error":
        logger.error(text, extra=extra)
    elif level == "warn":
        logger.warning(text, extra=extra)
    elif level == "debug":
        logger.debug(text, extra=extra)
    else:
        logger.info(text, extra=extra)

    return {"status": "ok"}
