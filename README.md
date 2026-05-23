# Sol.IA Motion Editor

Backend inicial do editor automático de vídeos curtos da Sol.IA.

Este repositório contém um MVP técnico em FastAPI que já faz o fluxo básico:

1. recebe upload de arquivo;
2. salva o arquivo temporariamente;
3. cria um job;
4. coloca o job numa fila assíncrona;
5. processa o job em segundo plano;
6. permite consultar o status do processamento.

Por enquanto, o processamento real de vídeo ainda está simulado. O lugar onde hoje existe um `asyncio.sleep(5)` é onde entram, na próxima fase:

- extração de áudio com FFmpeg;
- transcrição com AssemblyAI ou Whisper;
- análise editorial com IA;
- geração de timeline JSON;
- renderização final em MP4 vertical.

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Depois abra:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

### Upload

```bash
curl -F "file=@video.mp4" http://127.0.0.1:8000/upload
```

Resposta:

```json
{
  "id": "job-id",
  "status": "queued",
  "result": null
}
```

### Status do job

```bash
curl http://127.0.0.1:8000/job/job-id
```

Quando concluído:

```json
{
  "id": "job-id",
  "status": "done",
  "result": "processed_job-id.mp4"
}
```

## Próximo passo técnico

Trocar a simulação do worker pela função real:

```python
await process_video_pipeline(job_id)
```

Essa função deverá executar:

1. `ffmpeg` para extrair áudio;
2. transcrição;
3. análise da transcrição;
4. geração de timeline;
5. renderização do vídeo final;
6. upload do resultado.
