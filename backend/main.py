from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import commentary as c
import metrics as m

app = FastAPI(title="Churn Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/metrics")
def get_metrics():
    try:
        return m.compute_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commentary")
def get_commentary():
    return c.get_all_commentary()


@app.put("/api/commentary/{section_id}")
def update_commentary(section_id: str, body: dict = Body(...)):
    content = body.get("content", "")
    try:
        return c.save_user_override(section_id, content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/commentary/{section_id}/override")
def revert_commentary(section_id: str):
    try:
        return c.clear_user_override(section_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/refresh")
def refresh_data():
    """Re-read Excel + regenerate AI commentary (skips user overrides)."""
    try:
        return c.regenerate_all(skip_overridden=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
