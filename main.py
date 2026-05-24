import asyncio
import json
import re
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

app = FastAPI(title="Sol.IA Motion Planner 0.4.1")
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


@app.get("/latest")
async def latest_video():
    path = OUTPUT_DIR / "ULTIMO_SOLIA_EDITADO.mp4"
    if not path.exists():
        return {"error": "Nenhum video final gerado ainda."}
    return FileResponse(str(path), media_type="video/mp4", filename="ULTIMO_SOLIA_EDITADO.mp4")


@app.get("/latest-plan")
async def latest_plan():
    path = OUTPUT_DIR / "ULTIMO_PLANO_SOLIA.json"
    if not path.exists():
        return {"error": "Nenhum plano gerado ainda."}
    return FileResponse(str(path), media_type="application/json", filename="ULTIMO_PLANO_SOLIA.json")


@app.post("/plan")
async def plan_video(
    template: str = Form("planner"),
    hook: str = Form("NAO E DEDO PODRE"),
    middle: str = Form("E PADRAO REPETINDO"),
    cta: str = Form("POSICIONE-SE"),
    script: str = Form(""),
    seconds: int = Form(30),
):
    seconds = max(5, min(int(seconds), 90))
    scenes = generate_plan(script, hook, middle, cta, seconds, has_product=(template == "product"))
    return {
        "version": "0.4.1",
        "template": template,
        "seconds": seconds,
        "render_note": "Plano editorial por cenas. Render limpo: menos escuro, menos texto repetido e menos poluicao visual.",
        "scenes": scenes,
    }


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    product: Optional[UploadFile] = File(None),
    template: str = Form("planner"),
    hook: str = Form("NAO E DEDO PODRE"),
    middle: str = Form("E PADRAO REPETINDO"),
    cta: str = Form("POSICIONE-SE"),
    script: str = Form(""),
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
    scenes = generate_plan(script, hook, middle, cta, seconds, has_product=bool(product_path))

    jobs[job_id] = {
        "status": "queued",
        "input_path": str(input_path),
        "product_path": str(product_path) if product_path else None,
        "template": template,
        "hook": hook.strip() or "NAO E DEDO PODRE",
        "middle": middle.strip() or "E PADRAO REPETINDO",
        "cta": cta.strip() or "POSICIONE-SE",
        "script": script.strip(),
        "seconds": seconds,
        "scenes": scenes,
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


def clean_text(text: str) -> str:
    return " ".join((text or "").replace("\n", " ").split()).strip()


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\s+[–—-]\s+", text)
    return [p.strip(" .!?\n\t") for p in parts if p.strip(" .!?\n\t")]


def chunk_words(text: str, max_chunks: int) -> list[str]:
    words = clean_text(text).split()
    if not words:
        return []
    size = max(1, round(len(words) / max_chunks))
    chunks = []
    for i in range(0, len(words), size):
        chunks.append(" ".join(words[i:i + size]))
    return chunks[:max_chunks]


def generate_plan(script: str, hook: str, middle: str, cta: str, seconds: int, has_product: bool = False) -> list[dict]:
    hook = clean_text(hook) or "NAO E DEDO PODRE"
    middle = clean_text(middle) or "E PADRAO REPETINDO"
    cta = clean_text(cta) or "POSICIONE-SE"
    sentences = split_sentences(script)

    if len(sentences) < 3:
        sentences = [hook, middle, cta]
    elif len(sentences) > 6:
        sentences = chunk_words(script, 6)

    total = max(5, seconds)
    scene_count = max(3, min(6, len(sentences)))
    base_duration = total / scene_count
    scenes = []

    for idx in range(scene_count):
        start = round(idx * base_duration, 2)
        end = round(total if idx == scene_count - 1 else (idx + 1) * base_duration, 2)
        text = sentences[idx] if idx < len(sentences) else ""

        if idx == 0:
            role = "GANCHO"
            visual = "Texto forte no topo, sem cobrir o rosto"
            overlay = hook
            layer = "top"
        elif idx == scene_count - 1:
            role = "CTA"
            visual = "Chamada final limpa na parte inferior"
            overlay = cta
            layer = "bottom"
        elif has_product and idx == scene_count - 2:
            role = "PRODUTO"
            visual = "Capa/produto na lateral + voce falando"
            overlay = middle
            layer = "side_product"
        elif idx == 1:
            role = "DOR"
            visual = "Legenda grande de identificacao, 2 linhas"
            overlay = text
            layer = "caption"
        else:
            role = "VIRADA"
            visual = "Legenda por bloco com leve respiro visual"
            overlay = text
            layer = "caption"

        scenes.append({
            "index": idx + 1,
            "start": start,
            "end": end,
            "duration": round(end - start, 2),
            "role": role,
            "spoken_text": text,
            "overlay": overlay,
            "visual": visual,
            "layer": layer,
        })

    return scenes


def wrap_text(text: str, max_chars: int = 15, max_lines: int = 4) -> str:
    cleaned = clean_text(text).upper()
    words = cleaned.split()
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
        "-crf", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]


def scene_caption_filters(job: dict, job_id: str, y: int = 1345) -> str:
    filters = ""
    scenes = job.get("scenes") or []
    for scene in scenes:
        if scene["role"] in {"GANCHO", "CTA", "PRODUTO"}:
            continue
        text = scene.get("spoken_text") or scene.get("overlay") or ""
        file_path = write_text_file(job_id, f"scene_{scene['index']}", text, max_chars=23, max_lines=2)
        a = scene["start"]
        b = scene["end"]
        filters += (
            f",drawbox=x=90:y={y}:w=900:h=210:color=black@0.54:t=fill:enable='between(t,{a:.2f},{b:.2f})'"
            f",drawtext=textfile={file_path}:fontcolor=white:fontsize=52:line_spacing=10:"
            f"x=(w-text_w)/2:y={y + 52}:enable='between(t,{a:.2f},{b:.2f})'"
        )
    return filters


def save_plan_files(job_id: str, job: dict, output_name: str):
    plan = {
        "version": "0.4.1",
        "job_id": job_id,
        "output": output_name,
        "template": job.get("template"),
        "seconds": job.get("seconds"),
        "scenes": job.get("scenes", []),
    }
    plan_path = OUTPUT_DIR / f"solia_{job_id}_plan.json"
    latest_plan_path = OUTPUT_DIR / "ULTIMO_PLANO_SOLIA.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def build_planner_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    scenes = job.get("scenes") or generate_plan(job.get("script", ""), job["hook"], job["middle"], job["cta"], seconds)
    hook_scene = scenes[0]
    cta_scene = scenes[-1]
    hook_file = write_text_file(job_id, "planner_hook", hook_scene["overlay"], 18, 3)
    cta_file = write_text_file(job_id, "planner_cta", cta_scene["overlay"], 18, 2)
    captions = scene_caption_filters(job, job_id, 1345)

    filter_complex = (
        f"[0:v]scale=1215:2160:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.06:brightness=0.045:saturation=1.08,unsharp=5:5:0.35,"
        f"drawbox=x=0:y=0:w=1080:h=285:color=black@0.46:t=fill:enable='between(t,{hook_scene['start']:.2f},{hook_scene['end']:.2f})',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=62:line_spacing=12:"
        f"box=1:boxcolor=black@0.22:boxborderw=14:x=(w-text_w)/2:y=78:enable='between(t,{hook_scene['start']:.2f},{hook_scene['end']:.2f})'"
        f"{captions},"
        f"drawbox=x=0:y=1515:w=1080:h=310:color=black@0.66:t=fill:enable='between(t,{cta_scene['start']:.2f},{cta_scene['end']:.2f})',"
        f"drawtext=textfile={cta_file}:fontcolor=yellow:fontsize=60:line_spacing=12:"
        f"x=(w-text_w)/2:y=1600:enable='between(t,{cta_scene['start']:.2f},{cta_scene['end']:.2f})',"
        f"drawbox=x=0:y=1892:w='1080*t/{seconds}':h=12:color=yellow@0.88:t=fill,"
        f"drawtext=text='Sol.IA Planner':fontcolor=white@0.56:fontsize=24:x=w-text_w-42:y=h-62[outv]"
    )
    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_split_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 13)
    middle_file = write_text_file(job_id, "middle", job["middle"], 14)
    cta_file = write_text_file(job_id, "cta", job["cta"], 14)

    filter_complex = (
        f"[0:v]scale=620:1920:force_original_aspect_ratio=increase,crop=620:1920,"
        f"eq=contrast=1.06:brightness=0.045:saturation=1.07,unsharp=5:5:0.35[left];"
        f"color=c=0x070707:s=460x1920:d={seconds}[rightbase];"
        f"[rightbase]drawbox=x=0:y=0:w=460:h=1920:color=white@0.04:t=fill,"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=54:line_spacing=12:"
        f"x=(w-text_w)/2:y=220:enable='between(t,0,7)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=46:line_spacing=12:"
        f"x=(w-text_w)/2:y=560:enable='between(t,7,20)',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=50:line_spacing=12:"
        f"x=(w-text_w)/2:y=940:enable='gte(t,20)',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.58:fontsize=26:x=(w-text_w)/2:y=1700[right];"
        f"[left][right]hstack=inputs=2[outv]"
    )
    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_punch_template(job: dict, output_path: Path) -> list[str]:
    return build_planner_template(job, output_path)


def build_noir_template(job: dict, output_path: Path) -> list[str]:
    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 17, 3)
    cta_file = write_text_file(job_id, "cta", job["cta"], 18, 3)
    captions = scene_caption_filters(job, job_id, 1300)
    cta_start = max(seconds - 7, 5)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.05:brightness=0.02:saturation=0.95,vignette=PI/6,"
        f"drawbox=x=70:y=120:w=940:h=300:color=black@0.48:t=fill:enable='between(t,0,7)',"
        f"drawtext=textfile={hook_file}:fontcolor=white:fontsize=60:line_spacing=12:"
        f"x=(w-text_w)/2:y=180:enable='between(t,0,7)'"
        f"{captions},"
        f"drawbox=x=70:y=1515:w=940:h=280:color=black@0.54:t=fill:enable='gte(t,{cta_start})',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=52:line_spacing=12:"
        f"x=(w-text_w)/2:y=1590:enable='gte(t,{cta_start})'[outv]"
    )
    return ["ffmpeg", "-y", "-t", str(seconds), "-i", job["input_path"], "-filter_complex", filter_complex, *common_output_args(output_path)]


def build_product_template(job: dict, output_path: Path) -> list[str]:
    if not job.get("product_path"):
        return build_split_template(job, output_path)

    job_id = output_path.stem
    seconds = job["seconds"]
    hook_file = write_text_file(job_id, "hook", job["hook"], 13)
    middle_file = write_text_file(job_id, "middle", job["middle"], 14)
    cta_file = write_text_file(job_id, "cta", job["cta"], 13)

    filter_complex = (
        f"[0:v]scale=620:1920:force_original_aspect_ratio=increase,crop=620:1920,"
        f"eq=contrast=1.06:brightness=0.045:saturation=1.06,unsharp=5:5:0.35[left];"
        f"color=c=0x080808:s=460x1920:d={seconds}[rightbase];"
        f"[1:v]scale=330:-1,format=rgba[prod];"
        f"[rightbase][prod]overlay=x=(W-w)/2:y=690:enable='gte(t,3)'[rightprod];"
        f"[rightprod]drawtext=textfile={hook_file}:fontcolor=white:fontsize=46:line_spacing=10:"
        f"x=(w-text_w)/2:y=160:enable='between(t,0,8)',"
        f"drawtext=textfile={middle_file}:fontcolor=yellow:fontsize=38:line_spacing=10:"
        f"x=(w-text_w)/2:y=470:enable='between(t,8,21)',"
        f"drawbox=x=28:y=1410:w=404:h=210:color=red@0.62:t=fill:enable='gte(t,21)',"
        f"drawtext=textfile={cta_file}:fontcolor=white:fontsize=42:line_spacing=10:"
        f"x=(w-text_w)/2:y=1460:enable='gte(t,21)',"
        f"drawtext=text='Sol.IA Cut':fontcolor=white@0.58:fontsize=24:x=(w-text_w)/2:y=1725[right];"
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
    template = job.get("template", "planner")
    if template == "split":
        return build_split_template(job, output_path)
    if template == "noir":
        return build_noir_template(job, output_path)
    if template == "product":
        return build_product_template(job, output_path)
    return build_planner_template(job, output_path)


def process_video(job_id: str):
    job = jobs[job_id]
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg nao encontrado. Instale com: brew install ffmpeg")

    output_name = f"solia_{job_id}.mp4"
    output_path = OUTPUT_DIR / output_name
    cmd = build_command(job, output_path)
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    save_plan_files(job_id, job, output_name)

    last_path = OUTPUT_DIR / "ULTIMO_SOLIA_EDITADO.mp4"
    shutil.copyfile(output_path, last_path)

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
            jobs[job_id]["error"] = exc.stderr[-3000:] if exc.stderr else str(exc)
        except Exception as exc:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
        finally:
            queue.task_done()


@app.on_event("startup")
async def startup():
    asyncio.create_task(worker())
