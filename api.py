from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import os
from fastapi.responses import FileResponse
from data_science_crew.main import run

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")

app = FastAPI(title="CrewAI API")

# Allow React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://agentic-ai-data-science.onrender.com"],
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

    # Run CrewAI
    run(dataset_path=str(dataset_path), base_url=os.getenv("BASE_URL", "http://localhost:10000"))

    return {
        "status": "completed",
        "report_path": "reports/insights_report.md",
    }

@app.get("/download/cleaned")
def download_cleaned():
    file_path = "data/cleaned.csv"

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        filename="cleaned_dataset.csv",
        media_type="text/csv"
    )

app.mount("/", StaticFiles(directory="build", html=True), name="static")