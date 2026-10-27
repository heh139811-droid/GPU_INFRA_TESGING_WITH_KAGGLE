import json
import urllib.parse
import urllib.request
import uuid

COMFY_URL = "http://127.0.0.1:8188"


def _request(path: str, payload: dict | None = None) -> bytes:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{COMFY_URL}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def submit(workflow: dict) -> str:
    res = json.loads(_request("/prompt", {"prompt": workflow, "client_id": uuid.uuid4().hex}))
    return res["prompt_id"]


def result(prompt_id: str) -> dict | None:
    """끝난 작업이면 {"ok": bool, "images": [...], "error": str|None}, 아직이면 None."""
    history = json.loads(_request(f"/history/{prompt_id}"))
    entry = history.get(prompt_id)
    if entry is None:
        return None
    status = entry.get("status", {})
    if status.get("status_str") != "success":
        return {"ok": False, "images": [], "error": json.dumps(status.get("messages", []), ensure_ascii=False)}
    images = [
        img
        for node_output in entry["outputs"].values()
        for img in node_output.get("images", [])
    ]
    return {"ok": True, "images": images, "error": None}


def image_bytes(filename: str, subfolder: str, kind: str) -> bytes:
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": kind})
    return _request(f"/view?{query}")


def model_files(folder: str) -> set[str]:
    return set(json.loads(_request(f"/models/{folder}")))


def is_up() -> bool:
    try:
        _request("/system_stats")
        return True
    except OSError:
        return False
