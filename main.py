import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Sol.IA Motion Editor Local")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

job_queue: asyncio.Queue[str] = asyncio.Queue()
jobs: dict[str, dict] = {}


class JobStatus(BaseModel):
    id: str
    status: str
    result: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>Sol.IA Motion Editor Local</h1><p>Crie static/index.html.</p>"


@app.post("/upload", response_model=JobStatus)
async def upload_video(
    file: UploadFile = File(...),
    headline: str = Form(""),
    preset: str = Form("ugc"),
):
    """Recebe um vídeo e cria um job local de edição simples."""
    job_id = str(uuid.uuid4())
    extension = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    input_path = UPLOAD_DIR / f"{job_id}{extension}"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    jobs[job_id] = {
        "status": "queued",
        "input_path": str(input_path),
        "headline": headline.strip(),
        "preset": preset,
        "result": None,
        "error": None,
    }

    await job_queue.put(job_id)
    return JobStatus(id=job_id, status="queued")


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JobStatus(id=job_id, status="not_found", error="Job não encontrado.")

    filename = job.get("result")
    download_url = f"/download/{filename}" if filename else None
    return JobStatus(
        id=job_id,
        status=job["status"],
        result=filename,
        download_url=download_url,
        error=job.get("error"),
    )


@app.get("/download/{filename}")
async def download_video(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return {"error": "Arquivo não encontrado."}
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename,
    )


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", " ")
    )


def build_filters(headline: str, preset: str) -> str:
    # Converte qualquer vídeo para vertical 1080x1920, com crop central.
    base = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    if preset == "premium":
        # Leve contraste e vinheta para visual mais editorial.
        base += ",eq=contrast=1.08:saturation=0.92,vignette"
    elif preset == "retention":
        # Mais contraste e nitidez para conteúdo rápido.
        base += ",eq=contrast=1.12:saturation=1.08,unsharp=5:5:0.6"

    if headline:
        text = escape_drawtext(headline)
        draw = (
            ",drawtext="
            "fontcolor=white:fontsize=58:line_spacing=12:"
            "box=1:boxcolor=black@0.55:boxborderw=28:"
            f"text='{text}':"
            "x=(w-text_w)/2:y=170:"
            "enable='between(t,0,4)'"
        )
        base += draw

    return base


def process_video(input_path: str, output_path: str, headline: str, preset: str):
    if not ffmpeg_available():
        raise RuntimeError(
            "FFmpeg não está instalado. Instale o FFmpeg no computador para renderizar vídeos."
        )

    filters = build_filters(headline, preset)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        filters,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


async def process_jobs():
    while True:
        job_id = await job_queue.get()
        try:
            job = jobs.get(job_id)
            if not job:
                continue

            job["status"] = "processing"
            output_filename = f"solia_{job_id}.mp4"
            output_path = OUTPUT_DIR / output_filename

            await asyncio.to_thread(
                process_video,
                job["input_path"],
                str(output_path),
                job.get("headline", ""),
                job.get("preset", "ugc"),
            )

            job["status"] = "done"
            job["result"] = output_filename
        except Exception as exc:
            if job_id in jobs:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = str(exc)
        finally:
            job_queue.task_done()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_jobs())
