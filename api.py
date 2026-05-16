import asyncio
import json
import os
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from data_science_crew.main import run

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")

app = FastAPI(title="CrewAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://agentic-ai-data-science.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
RUNS_DIR = Path("runs")

UPLOAD_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)

app.mount("/runs", StaticFiles(directory="runs"), name="runs")

# run_id → asyncio.Queue of progress events
_run_queues: dict[str, asyncio.Queue] = {}


@app.post("/run")
async def run_crew(file: UploadFile = File(...)):
    dataset_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    dataset_path.write_bytes(await file.read())

    run_id = str(uuid.uuid4())
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir()

    q: asyncio.Queue = asyncio.Queue()
    _run_queues[run_id] = q

    loop = asyncio.get_event_loop()
    base_url = os.getenv("BASE_URL", "http://localhost:10000")

    def emit(event: dict):
        loop.call_soon_threadsafe(q.put_nowait, event)

    def run_in_thread():
        try:
            run(
                dataset_path=str(dataset_path),
                base_url=base_url,
                run_dir=str(run_dir),
                emit=emit,
            )
            emit({
                "type": "done",
                "run_id": run_id,
                "report_path": f"runs/{run_id}/reports/insights_report.md",
            })
        except Exception as e:
            emit({"type": "error", "message": str(e)})

    threading.Thread(target=run_in_thread, daemon=True).start()

    return {"run_id": run_id}


@app.get("/progress/{run_id}")
async def progress_stream(run_id: str):
    q = _run_queues.get(run_id)
    if not q:
        return {"error": "Run not found"}

    async def event_generator():
        try:
            while True:
                event = await q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
        finally:
            _run_queues.pop(run_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/download/{run_id}/cleaned")
def download_cleaned(run_id: str):
    file_path = RUNS_DIR / run_id / "data" / "cleaned.csv"

    if not file_path.exists():
        return {"error": "File not found"}

    return FileResponse(
        path=str(file_path),
        filename="cleaned_dataset.csv",
        media_type="text/csv",
    )


app.mount("/", StaticFiles(directory="build", html=True), name="static")
