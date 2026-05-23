import asyncio
import os
import uuid
from typing import Optional

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Sol.IA Motion Editor")

job_queue: asyncio.Queue[str] = asyncio.Queue()
jobs: dict[str, dict] = {}


class JobStatus(BaseModel):
    id: str
    status: str
    result: Optional[str] = None


@app.get("/")
async def root():
    return {
        "app": "Sol.IA Motion Editor",
        "status": "online",
        "message": "Backend MVP rodando. Acesse /docs para testar upload e status.",
    }


@app.post("/upload", response_model=JobStatus)
async def upload_video(file: UploadFile = File(...)):
    """Recebe um arquivo, salva localmente e cria um job de processamento."""
    job_id = str(uuid.uuid4())
    safe_filename = file.filename or "video.mp4"
    filename = f"{job_id}_{safe_filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    jobs[job_id] = {
        "status": "queued",
        "result": None,
        "filepath": filepath,
        "original_filename": safe_filename,
    }

    await job_queue.put(job_id)
    return JobStatus(id=job_id, status="queued")


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Consulta status de um job."""
    job = jobs.get(job_id)
    if not job:
        return JobStatus(id=job_id, status="not_found")
    return JobStatus(id=job_id, status=job["status"], result=job.get("result"))


async def process_jobs():
    """Worker simples. Aqui entra o pipeline real de vídeo na próxima fase."""
    while True:
        job_id = await job_queue.get()

        try:
            if job_id in jobs:
                jobs[job_id]["status"] = "processing"

                # MVP técnico: simula processamento.
                # Próxima fase: substituir por FFmpeg + transcrição + IA + renderização.
                await asyncio.sleep(5)

                output_file = f"processed_{job_id}.mp4"
                jobs[job_id]["status"] = "done"
                jobs[job_id]["result"] = output_file
        except Exception as exc:
            if job_id in jobs:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["result"] = str(exc)
        finally:
            job_queue.task_done()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_jobs())
