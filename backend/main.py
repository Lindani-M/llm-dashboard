import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import commentary as c
import metrics as m

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dashboard.api")

app = FastAPI(title="Churn Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "An internal error occurred. Please try again."})


@app.get("/api/data-status")
def data_status():
    """Check whether the data source is newer than the last AI regeneration."""
    try:
        from metrics import get_excel_mtime
        excel_mtime = get_excel_mtime()
        store = c.load_store()
        # Find the oldest last_data_refresh among AI-generated sections
        ai_sections = [
            v["last_data_refresh"]
            for k, v in store.items()
            if k not in c._STATIC_SECTIONS
            and not v.get("is_user_override_active")
            and v.get("last_data_refresh")
        ]
        if not ai_sections:
            return {"needs_refresh": True, "reason": "No refresh recorded yet"}
        oldest_refresh = min(
            datetime.fromisoformat(ts) for ts in ai_sections
        )
        # Ensure both are offset-aware for comparison
        if oldest_refresh.tzinfo is None:
            oldest_refresh = oldest_refresh.replace(tzinfo=timezone.utc)
        needs = excel_mtime > oldest_refresh
        logger.info(
            "Data status check — Excel mtime: %s, last refresh: %s, needs_refresh: %s",
            excel_mtime.isoformat(), oldest_refresh.isoformat(), needs
        )
        return {
            "needs_refresh": needs,
            "excel_modified_at": excel_mtime.isoformat(),
            "last_commentary_refresh": oldest_refresh.isoformat(),
        }
    except Exception as e:
        logger.error("data-status check failed: %s", e, exc_info=True)
        return {"needs_refresh": False, "reason": "Status check unavailable"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/metrics")
def get_metrics():
    try:
        logger.info("Computing metrics from data source")
        result = m.compute_metrics()
        logger.info("Metrics computed successfully")
        return result
    except Exception as e:
        logger.error("Failed to compute metrics: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load dashboard data. Please try again.")


@app.get("/api/commentary")
def get_commentary():
    try:
        return c.get_all_commentary()
    except Exception as e:
        logger.error("Failed to load commentary: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load commentary. Please try again.")


@app.put("/api/commentary/{section_id}")
def update_commentary(section_id: str, body: dict = Body(...)):
    content = body.get("content", "")
    try:
        result = c.save_user_override(section_id, content)
        logger.info("User edited section '%s' (%d chars)", section_id, len(content))
        return result
    except ValueError as e:
        logger.warning("Edit rejected for unknown section '%s'", section_id)
        raise HTTPException(status_code=404, detail="Section not found.")
    except Exception as e:
        logger.error("Failed to save override for '%s': %s", section_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save your edit. Please try again.")


@app.delete("/api/commentary/{section_id}/override")
def revert_commentary(section_id: str):
    try:
        result = c.clear_user_override(section_id)
        logger.info("User reverted section '%s' to AI content", section_id)
        return result
    except ValueError as e:
        logger.warning("Revert rejected for unknown section '%s'", section_id)
        raise HTTPException(status_code=404, detail="Section not found.")
    except Exception as e:
        logger.error("Failed to revert '%s': %s", section_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revert. Please try again.")


@app.post("/api/refresh")
def refresh_data():
    """Re-read data source + regenerate AI commentary (skips user overrides)."""
    logger.info("Data refresh requested — recomputing metrics and regenerating AI commentary")
    try:
        result = c.regenerate_all(skip_overridden=True)
        error_count = len(result.get("errors", []))
        if error_count:
            logger.warning("Refresh completed with %d AI section error(s)", error_count)
        else:
            logger.info("Refresh completed successfully — all sections updated")
        return result
    except Exception as e:
        logger.error("Refresh failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Data refresh failed. Please try again.")
