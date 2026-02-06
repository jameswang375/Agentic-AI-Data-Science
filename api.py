from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid

from data_science_crew.main import run

app = FastAPI(title="CrewAI API")

# Allow React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
REPORT_DIR = Path("reports")

UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# Serve reports so React can fetch markdown + images
app.mount("/reports", StaticFiles(directory="reports"), name="reports")


@app.post("/run")
async def run_crew(file: UploadFile = File(...)):
    dataset_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    dataset_path.write_bytes(await file.read())

    # Run CrewAI (blocking, simple)
    run(dataset_path=str(dataset_path))

    return {
        "status": "completed",
        "report_path": "reports/insights_report.md",
    }
