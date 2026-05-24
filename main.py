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
ASSET_DIR = BASE_DIR / "assets"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Sol.IA UGC Cut 0.3")
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
    product: Optional[UploadFile] = File(None),
    template: str = Form("punch"),
    hook: str = Form("NAO E DEDO PODRE"),
    middle: str = Form("E PADRAO REPETINDO"),
    cta: str = Form("POSICIONE-SE"),
    seconds: int = Form(30),
):
    job_id = str(uuid.uuid4())
    video_ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    input_path = UPLOAD_DIR / f"{job_id}{video_ext}"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    product_path = None
    if product and product.filename:
        product_ext = Path(product.filename).suffix.lower() or ".png"
        product_path = ASSET_DIR / f"{job_id}_product{product_ext}"
        with product_path.open("wb") as f:
            shutil.copyfileobj(product.file, f)

    seconds = max(5, min(int(seconds), 90))

    jobs[job_id] = {
        "status": "queued",
        "input_path": str(input_path),
        "product_path": str(product_path) if product_path else None,
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


def wrap_text(text: str, max_chars: int = 15, max_lines: int = 4) -> str:
    words = text.upper().split()
    lines = []
    current = ""

    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "\n".join(lines[:max_lines])


def write_text_file(job_id: str, name: str, text: str, max_chars: int = 15, max_lines: int = 4) -> str:
    path = TEXT_DIR / f"{job_id}_{name}.txt"
    path.write_text(wrap_text(text, max_chars=max_chars, max_lines=max_lines), encoding="utf-8")
    return str(path)


def common_output_args(output_path: Path) -> list[str]:
    return [
        "-map", "[outv]",
        "-map", "0:a:0?",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "25",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]


def build_split_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 13)
    middle_file = write_text_file(job_id, "middle", job["middle"], 14)
    cta_file = write_text_file(job_id, "cta", job["cta"], 14)

    filter_complex = (
        f"[0:v]scale=620:1920:force_original_aspect_ratio=increase,crop=620:1920,"
        f"eq=contrast=1.22:saturation=1.15,unsharp=5:5:0.8[left];"
        f"color=c=0x070707:s=460x1920:d={seconds}[rightbase];"
        f"[rightbase]"
        f"drawbox=x=0:y=0:w=460:h=1920:color=white@0.04:t=fill,"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=54:line_spacing=12:"
        f"x=(w-text_w)/2:y=220:enable='between(t,0,7)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=46:line_spacing=12:"
        f"x=(w-text_w)/2:y=560:enable='between(t,7,20)',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=50:line_spacing=12:"
        f"x=(w-text_w)/2:y=940:enable='gte(t,20)',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.72:fontsize=28:x=(w-text_w)/2:y=1700[right];"
        f"[left][right]hstack=inputs=2[outv]"
    )

    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_punch_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 18, 3)
    middle_file = write_text_file(job_id, "middle", job["middle"], 20, 2)
    cta_file = write_text_file(job_id, "cta", job["cta"], 18, 3)
    cta_start = max(seconds - 7, 5)

    filter_complex = (
        f"[0:v]scale=1215:2160:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.23:saturation=1.16,unsharp=5:5:0.7,"
        f"drawbox=x=0:y=0:w=1080:h=300:color=black@0.72:t=fill:enable='between(t,0,6)',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=66:line_spacing=12:"
        f"box=1:boxcolor=red@0.72:boxborderw=22:x=(w-text_w)/2:y=70:enable='between(t,0,6)',"
        f"drawbox=x=0:y=1540:w=1080:h=260:color=black@0.70:t=fill:enable='between(t,10,22)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=52:line_spacing=12:"
        f"x=(w-text_w)/2:y=1600:enable='between(t,10,22)',"
        f"drawbox=x=0:y=1515:w=1080:h=305:color=black@0.78:t=fill:enable='gte(t,{cta_start})',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=64:line_spacing=12:"
        f"x=(w-text_w)/2:y=1580:enable='gte(t,{cta_start})',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.72:fontsize=28:x=w-text_w-45:y=h-70"
        f"[outv]"
    )

    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_noir_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 17, 3)
    cta_file = write_text_file(job_id, "cta", job["cta"], 18, 3)
    cta_start = max(seconds - 7, 5)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.18:brightness=-0.035:saturation=0.82,vignette=PI/4,"
        f"drawbox=x=70:y=120:w=940:h=300:color=black@0.65:t=fill:enable='between(t,0,7)',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=60:line_spacing=12:"
        f"x=(w-text_w)/2:y=180:enable='between(t,0,7)',"
        f"drawbox=x=70:y=1515:w=940:h=280:color=black@0.66:t=fill:enable='gte(t,{cta_start})',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=52:line_spacing=12:"
        f"x=(w-text_w)/2:y=1590:enable='gte(t,{cta_start})'"
        f"[outv]"
    )

    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_product_template(job: dict, output_path: Path) -> list[str]:
    # Se nao houver imagem do produto, usa a tela dividida normal.
    if not job.get("product_path"):
        return build_split_template(job, output_path)

    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 13)
    middle_file = write_text_file(job_id, "middle", job["middle"], 14)
    cta_file = write_text_file(job_id, "cta", job["cta"], 13)

    filter_complex = (
        f"[0:v]scale=620:1920:force_original_aspect_ratio=increase,crop=620:1920,"
        f"eq=contrast=1.22:saturation=1.14,unsharp=5:5:0.7[left];"
        f"color=c=0x080808:s=460x1920:d={seconds}[rightbase];"
        f"[1:v]scale=330:-1,format=rgba[prod];"
        f"[rightbase][prod]overlay=x=(W-w)/2:y=690:enable='gte(t,3)'[rightprod];"
        f"[rightprod]"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=46:line_spacing=10:"
        f"x=(w-text_w)/2:y=160:enable='between(t,0,8)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=38:line_spacing=10:"
        f"x=(w-text_w)/2:y=470:enable='between(t,8,21)',"
        f"drawbox=x=28:y=1410:w=404:h=210:color=red@0.70:t=fill:enable='gte(t,21)',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=42:line_spacing=10:"
        f"x=(w-text_w)/2:y=1460:enable='gte(t,21)',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.72:fontsize=26:x=(w-text_w)/2:y=1725[right];"
        f"[left][right]hstack=inputs=2[outv]"
    )

    return [
        "ffmpeg", "-y", "-t", str(seconds),
        "-i", job["input_path"],
        "-loop", "1", "-t", str(seconds), "-i", job["product_path"],
        "-filter_complex", filter_complex,
        *common_output_args(output_path),
    ]


def build_command(job: dict, output_path: Path) -> list[str]:
    template = job.get("template", "punch")
    if template == "split":
        return build_split_template(job, output_path)
    if template == "noir":
        return build_noir_template(job, output_path)
    if template == "product":
        return build_product_template(job, output_path)
    return build_punch_template(job, output_path)


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
            jobs[job_id]["error"] = exc.stderr[-2500:] if exc.stderr else str(exc)
        except Exception as exc:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
        finally:
            queue.task_done()


@app.on_event("startup")
async def startup():
    asyncio.create_task(worker())
