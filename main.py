import asyncio
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
TEXT_DIR = BASE_DIR / "text_assets"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Sol.IA UGC Cut 0.2")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

jobs: dict[str, dict] = {}
queue: asyncio.Queue[str] = asyncio.Queue()


class JobStatus(BaseModel):
    id: str
    status: str
    result: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    template: str = Form("split"),
    hook: str = Form("NAO E DEDO PODRE"),
    middle: str = Form("E PADRAO REPETINDO"),
    cta: str = Form("POSICIONE-SE"),
    seconds: int = Form(30),
):
    job_id = str(uuid.uuid4())
    ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    input_path = UPLOAD_DIR / f"{job_id}{ext}"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    seconds = max(5, min(int(seconds), 90))

    jobs[job_id] = {
        "status": "queued",
        "input_path": str(input_path),
        "template": template,
        "hook": hook.strip() or "NAO E DEDO PODRE",
        "middle": middle.strip() or "E PADRAO REPETINDO",
        "cta": cta.strip() or "POSICIONE-SE",
        "seconds": seconds,
        "result": None,
        "error": None,
    }

    await queue.put(job_id)
    return JobStatus(id=job_id, status="queued")


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JobStatus(id=job_id, status="not_found", error="Job nao encontrado.")

    filename = job.get("result")
    return JobStatus(
        id=job_id,
        status=job.get("status", "unknown"),
        result=filename,
        download_url=f"/download/{filename}" if filename else None,
        error=job.get("error"),
    )


@app.get("/download/{filename}")
async def download(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return {"error": "Arquivo nao encontrado."}
    return FileResponse(str(path), media_type="video/mp4", filename=filename)


def wrap_text(text: str, max_chars: int = 16) -> str:
    words = text.upper().split()
    lines = []
    current = ""

    for word in words:
        if len((current + " " + word).strip()) <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "\n".join(lines[:4])


def write_text_file(job_id: str, name: str, text: str) -> str:
    path = TEXT_DIR / f"{job_id}_{name}.txt"
    path.write_text(wrap_text(text), encoding="utf-8")
    return str(path)


def build_split_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"])
    middle_file = write_text_file(job_id, "middle", job["middle"])
    cta_file = write_text_file(job_id, "cta", job["cta"])

    filter_complex = (
        f"[0:v]scale=620:1920:force_original_aspect_ratio=increase,"
        f"crop=620:1920,eq=contrast=1.22:saturation=1.15,unsharp=5:5:0.8[left];"
        f"color=c=black:s=460x1920:d={seconds}[right];"
        f"[right]"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=52:line_spacing=12:"
        f"x=(w-text_w)/2:y=220:enable='between(t,0,7)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=44:line_spacing=12:"
        f"x=(w-text_w)/2:y=520:enable='between(t,7,20)',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=48:line_spacing=12:"
        f"x=(w-text_w)/2:y=900:enable='gte(t,20)',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.75:fontsize=28:"
        f"x=(w-text_w)/2:y=1700[righttext];"
        f"[left][righttext]hstack=inputs=2[outv]"
    )

    return [
        "ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"],
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(output_path),
    ]


def build_hook_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"])
    cta_file = write_text_file(job_id, "cta", job["cta"])
    cta_start = max(seconds - 7, 5)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,eq=contrast=1.28:saturation=1.18,unsharp=5:5:0.8,"
        f"drawbox=x=0:y=0:w=1080:h=330:color=black@0.78:t=fill:enable='between(t,0,6)',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=68:line_spacing=14:"
        f"x=(w-text_w)/2:y=95:enable='between(t,0,6)',"
        f"drawbox=x=0:y=1640:w=1080:h=280:color=black@0.75:t=fill:enable='gte(t,{cta_start})',"
        f"drawtext=textfile={cta_file}:fontcolor=yellow:fontsize=58:line_spacing=12:"
        f"x=(w-text_w)/2:y=1710:enable='gte(t,{cta_start})'[outv]"
    )

    return [
        "ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"],
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(output_path),
    ]


def build_noir_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"])
    cta_file = write_text_file(job_id, "cta", job["cta"])
    cta_start = max(seconds - 7, 5)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,eq=contrast=1.16:brightness=-0.03:saturation=0.82,vignette=PI/4,"
        f"drawbox=x=80:y=120:w=920:h=260:color=black@0.62:t=fill:enable='between(t,0,6)',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=60:line_spacing=12:"
        f"x=(w-text_w)/2:y=170:enable='between(t,0,6)',"
        f"drawbox=x=80:y=1550:w=920:h=240:color=black@0.62:t=fill:enable='gte(t,{cta_start})',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=50:line_spacing=12:"
        f"x=(w-text_w)/2:y=1620:enable='gte(t,{cta_start})'[outv]"
    )

    return [
        "ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"],
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(output_path),
    ]


def build_command(job: dict, output_path: Path) -> list[str]:
    template = job.get("template", "split")
    if template == "hook":
        return build_hook_template(job, output_path)
    if template == "noir":
        return build_noir_template(job, output_path)
    return build_split_template(job, output_path)


def process_video(job_id: str):
    job = jobs[job_id]
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg nao encontrado. Instale com: brew install ffmpeg")

    output_name = f"solia_{job_id}.mp4"
    output_path = OUTPUT_DIR / output_name
    cmd = build_command(job, output_path)
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    job["status"] = "done"
    job["result"] = output_name


async def worker():
    while True:
        job_id = await queue.get()
        try:
            if job_id in jobs:
                jobs[job_id]["status"] = "processing"
                await asyncio.to_thread(process_video, job_id)
        except subprocess.CalledProcessError as exc:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = exc.stderr[-2000:] if exc.stderr else str(exc)
        except Exception as exc:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
        finally:
            queue.task_done()


@app.on_event("startup")
async def startup():
    asyncio.create_task(worker())
