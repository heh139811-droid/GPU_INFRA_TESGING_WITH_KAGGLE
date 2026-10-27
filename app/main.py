import copy
import json
import random
import uuid
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import comfy, translate
from .presets import ASPECTS, MODELS, NEGATIVE, STYLES, build_prompt

ROOT = Path(__file__).resolve().parent
WORKFLOWS = {
    model_id: json.loads((ROOT.parent / "workflows" / m["workflow"]).read_text(encoding="utf-8"))
    for model_id, m in MODELS.items()
}
LATENT_NODES = {"EmptyLatentImage", "EmptySD3LatentImage"}

app = FastAPI(title="광고 이미지 생성")
jobs: dict[str, dict] = {}


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    model: str = "zimage"
    style: str = "studio"
    aspect: str = "1:1"
    count: int = Field(default=2, ge=1, le=4)
    prompt_en: str | None = None
    seed: int | None = None


def _available_models() -> list[str]:
    cache: dict[str, set[str]] = {}
    available = []
    for model_id, m in MODELS.items():
        ok = True
        for folder, filename in m["requires"]:
            if folder not in cache:
                cache[folder] = comfy.model_files(folder)
            ok = ok and filename in cache[folder]
        if ok:
            available.append(model_id)
    return available


def _workflow(model: str, positive: str, width: int, height: int, seed: int) -> dict:
    wf = copy.deepcopy(WORKFLOWS[model])
    sampler = next(n for n in wf.values() if n["class_type"] == "KSampler")
    latent = next(n for n in wf.values() if n["class_type"] in LATENT_NODES)
    wf[sampler["inputs"]["positive"][0]]["inputs"]["text"] = positive
    if MODELS[model]["negative"]:
        wf[sampler["inputs"]["negative"][0]]["inputs"]["text"] = NEGATIVE
    sampler["inputs"]["seed"] = seed
    latent["inputs"].update(width=width, height=height, batch_size=1)
    return wf


@app.get("/api/options")
def options():
    up = comfy.is_up()
    available = _available_models() if up else []
    return {
        "models": [
            {"id": k, "label": v["label"], "desc": v["desc"], "available": k in available}
            for k, v in MODELS.items()
        ],
        "styles": [{"id": k, **{f: v[f] for f in ("label", "desc")}} for k, v in STYLES.items()],
        "aspects": [{"id": k, **v} for k, v in ASPECTS.items()],
        "comfy_up": up,
    }


@app.post("/api/generate")
def generate(req: GenerateRequest):
    if req.model not in MODELS or req.style not in STYLES or req.aspect not in ASPECTS:
        raise HTTPException(400, "알 수 없는 모델, 스타일 또는 화면비입니다.")
    if not comfy.is_up():
        raise HTTPException(503, "이미지 생성 서버(ComfyUI)가 꺼져 있습니다.")
    if req.model not in _available_models():
        raise HTTPException(409, f"{MODELS[req.model]['label']} 모델 파일이 ComfyUI에 없습니다.")

    subject_en = req.prompt_en.strip() if req.prompt_en else translate.ko_to_en(req.prompt)
    positive = build_prompt(subject_en, req.style)
    size = ASPECTS[req.aspect]
    base_seed = req.seed if req.seed is not None else random.randint(0, 2**31 - 1)

    prompt_ids = [
        comfy.submit(_workflow(req.model, positive, size["width"], size["height"], base_seed + i))
        for i in range(req.count)
    ]
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "prompt_ids": prompt_ids,
        "model": req.model,
        "prompt": req.prompt,
        "prompt_en": subject_en,
        "positive": positive,
        "seed": base_seed,
        "aspect": req.aspect,
        "results": {},
    }
    return {"job_id": job_id, "prompt_en": subject_en, "positive": positive, "seed": base_seed}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "작업을 찾을 수 없습니다.")
    for pid in job["prompt_ids"]:
        if pid not in job["results"]:
            res = comfy.result(pid)
            if res is not None:
                job["results"][pid] = res

    images, errors = [], []
    for pid in job["prompt_ids"]:
        res = job["results"].get(pid)
        if res is None:
            continue
        if not res["ok"]:
            errors.append(res["error"])
        for img in res["images"]:
            query = urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
            images.append(f"/api/image?{query}")
    done = len(job["results"])
    return {
        "done": done,
        "total": len(job["prompt_ids"]),
        "finished": done == len(job["prompt_ids"]),
        "images": images,
        "errors": errors,
        "prompt_en": job["prompt_en"],
        "positive": job["positive"],
        "seed": job["seed"],
        "aspect": job["aspect"],
        "model": MODELS[job["model"]]["label"],
    }


@app.get("/api/image")
def image(filename: str, subfolder: str = "", type: str = "output"):
    if "/" in filename or "\\" in filename or ".." in subfolder:
        raise HTTPException(400, "잘못된 파일 경로입니다.")
    return Response(comfy.image_bytes(filename, subfolder, type), media_type="image/png")


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
