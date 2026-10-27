"""ComfyUI 서버에 API 형식 워크플로를 제출하고 결과 이미지를 저장한다.

    python scripts/comfy_submit.py workflows/sdxl_t2i_api.json --prompt "..." --seed 1
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def call(server: str, path: str, payload: dict | None = None) -> bytes:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{server}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def find_node(workflow: dict, class_type: str) -> dict:
    for node in workflow.values():
        if node["class_type"] == class_type:
            return node
    raise KeyError(class_type)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow", type=Path)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--prompt", help="KSampler positive 입력에 연결된 프롬프트를 교체")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    sampler = find_node(workflow, "KSampler")
    if args.prompt:
        positive_id = sampler["inputs"]["positive"][0]
        workflow[positive_id]["inputs"]["text"] = args.prompt
    if args.seed is not None:
        sampler["inputs"]["seed"] = args.seed

    started = time.time()
    res = json.loads(call(args.server, "/prompt", {"prompt": workflow, "client_id": uuid.uuid4().hex}))
    prompt_id = res["prompt_id"]
    print(f"submitted prompt_id={prompt_id}")

    while True:
        history = json.loads(call(args.server, f"/history/{prompt_id}"))
        if prompt_id in history:
            entry = history[prompt_id]
            break
        if time.time() - started > args.timeout:
            raise TimeoutError(prompt_id)
        time.sleep(1)

    status = entry.get("status", {})
    if status.get("status_str") != "success":
        raise RuntimeError(json.dumps(status, ensure_ascii=False))

    elapsed = time.time() - started
    args.out.mkdir(parents=True, exist_ok=True)
    for node_output in entry["outputs"].values():
        for img in node_output.get("images", []):
            query = urllib.parse.urlencode(
                {"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]}
            )
            dest = args.out / img["filename"]
            dest.write_bytes(call(args.server, f"/view?{query}"))
            print(f"saved {dest}")
    print(f"elapsed {elapsed:.1f}s")


if __name__ == "__main__":
    main()
