"""Control panel + audio engine in one process.

Starts WASAPI capture / lighting / UDP in a background thread, then serves the
dashboard UI for live slider edits.

    cd python
    python dashboard_server.py

Standalone audio without the UI:

    python main.py
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from audio_runtime import shared_runtime
from settings_store import (
    SETTING_SPECS,
    defaults_from_config,
    merged_settings,
    save_settings,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    shared_runtime.start()
    print("Audio engine started in background.")
    try:
        yield
    finally:
        print("Stopping audio engine...")
        shared_runtime.stop()


app = FastAPI(title="ESP32 LED Sync", docs_url=None, redoc_url=None, lifespan=lifespan)


class SettingsPatch(BaseModel):
    values: dict


@app.get("/api/schema")
def api_schema() -> dict:
    return {"specs": SETTING_SPECS, "groups": _group_order()}


@app.get("/api/settings")
def api_get_settings() -> dict:
    return {
        "values": merged_settings(),
        "defaults": defaults_from_config(),
        "source": "settings.local.json",
    }


@app.put("/api/settings")
def api_put_settings(patch: SettingsPatch) -> dict:
    try:
        values = save_settings(patch.values)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"values": values}


@app.post("/api/settings/reset")
def api_reset_settings() -> dict:
    from settings_store import SETTINGS_PATH

    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()
    return {"values": merged_settings()}


@app.get("/api/runtime")
def api_runtime() -> dict:
    return shared_runtime.snapshot()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _group_order() -> list[str]:
    seen: list[str] = []
    for spec in SETTING_SPECS.values():
        group = spec["group"]
        if group not in seen:
            seen.append(group)
    return seen


def main() -> None:
    import uvicorn

    print("Dashboard + audio: http://127.0.0.1:8765")
    print("Standalone audio only: python main.py")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
