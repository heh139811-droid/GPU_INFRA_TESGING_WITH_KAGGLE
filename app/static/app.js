const EXAMPLES = [
  "나무 테이블 위 흰 젖병, 따뜻한 아침 햇살",
  "대리석 위 화장품 세럼 병, 물방울, 상쾌한 느낌",
  "캠핑장 모닥불 옆 스테인리스 텀블러, 저녁 노을",
  "흰 운동화 한 켤레, 파스텔 배경, 공중에 떠 있는 구도",
];

const state = { model: "zimage", style: "studio", aspect: "1:1", count: 2, aspects: {} };
const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const res = await fetch(path, body ? {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  } : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `요청 실패 (${res.status})`);
  return data;
}

function selectable(container, items, key, render) {
  container.innerHTML = "";
  for (const item of items) {
    const el = render(item);
    el.type = "button";
    el.classList.toggle("active", state[key] === item.id);
    el.addEventListener("click", () => {
      state[key] = item.id;
      [...container.children].forEach((c) => c.classList.remove("active"));
      el.classList.add("active");
    });
    container.appendChild(el);
  }
}

function setStatus(up) {
  $("status").className = `status ${up ? "up" : "down"}`;
  $("status-text").textContent = up ? "생성 서버 연결됨" : "생성 서버 꺼짐";
}

async function init() {
  const opts = await api("/api/options");
  setStatus(opts.comfy_up);
  opts.aspects.forEach((a) => (state.aspects[a.id] = a));

  const firstAvailable = opts.models.find((m) => m.available);
  if (firstAvailable) state.model = firstAvailable.id;
  selectable($("models"), opts.models, "model", (m) => {
    const b = document.createElement("button");
    b.className = "style-card";
    b.disabled = !m.available;
    b.innerHTML = `<b>${m.label}</b><span>${m.available ? m.desc : "모델 파일 없음"}</span>`;
    return b;
  });

  selectable($("styles"), opts.styles, "style", (s) => {
    const b = document.createElement("button");
    b.className = "style-card";
    b.innerHTML = `<b>${s.label}</b><span>${s.desc}</span>`;
    return b;
  });
  selectable($("aspects"), opts.aspects, "aspect", (a) => {
    const b = document.createElement("button");
    b.className = "chip";
    b.textContent = a.label;
    return b;
  });
  selectable($("counts"), [1, 2, 3, 4].map((n) => ({ id: n })), "count", (c) => {
    const b = document.createElement("button");
    b.textContent = `${c.id}장`;
    return b;
  });

  for (const text of EXAMPLES) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "example";
    b.textContent = text;
    b.addEventListener("click", () => { $("prompt").value = text; $("prompt").focus(); });
    $("examples").appendChild(b);
  }
}

function addJobCard(prompt, aspect, count) {
  $("empty").hidden = true;
  const node = $("job-template").content.firstElementChild.cloneNode(true);
  node.querySelector(".job-prompt").textContent = prompt;
  node.querySelector(".job-progress").textContent = "번역 중…";
  const { width, height } = state.aspects[aspect];
  const grid = node.querySelector(".grid");
  for (let i = 0; i < count; i++) {
    const tile = document.createElement("div");
    tile.className = "tile loading";
    tile.style.aspectRatio = `${width} / ${height}`;
    grid.appendChild(tile);
  }
  $("jobs").prepend(node);
  return node;
}

function openViewer(src) {
  $("viewer-img").src = src;
  $("viewer-download").href = src;
  $("viewer-download").download = `ad_${Date.now()}.png`;
  $("viewer").showModal();
}

async function poll(jobId, card) {
  const tiles = [...card.querySelectorAll(".tile")];
  while (true) {
    const job = await api(`/api/jobs/${jobId}`);
    card.querySelector(".job-progress").textContent = job.finished
      ? `완료 · ${job.model} · 시드 ${job.seed}`
      : `${job.model} 생성 중 ${job.done}/${job.total}`;
    job.images.forEach((src, i) => {
      const tile = tiles[i];
      if (!tile || tile.querySelector("img")) return;
      tile.classList.remove("loading");
      const img = document.createElement("img");
      img.src = src;
      img.alt = "생성된 광고 이미지";
      img.addEventListener("click", () => openViewer(src));
      tile.appendChild(img);
    });
    if (job.finished) {
      tiles.slice(job.images.length).forEach((t) => {
        t.classList.remove("loading");
        t.innerHTML = '<div class="failed">생성 실패</div>';
      });
      return;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = $("prompt").value.trim();
  if (!prompt) return;
  $("error").hidden = true;
  $("generate").disabled = true;

  const card = addJobCard(prompt, state.aspect, state.count);
  try {
    const seed = $("seed").value;
    const job = await api("/api/generate", {
      prompt,
      model: state.model,
      style: state.style,
      aspect: state.aspect,
      count: state.count,
      prompt_en: $("prompt-en").value.trim() || null,
      seed: seed === "" ? null : Number(seed),
    });
    card.querySelector(".job-en").textContent = job.prompt_en;
    card.querySelector(".job-progress").textContent = "생성 대기 중…";
    $("generate").disabled = false;
    await poll(job.job_id, card);
  } catch (err) {
    card.remove();
    if (!$("jobs").children.length) $("empty").hidden = false;
    $("error").textContent = err.message;
    $("error").hidden = false;
    $("generate").disabled = false;
  }
});

$("viewer-close").addEventListener("click", () => $("viewer").close());

init().catch((err) => {
  setStatus(false);
  $("error").textContent = err.message;
  $("error").hidden = false;
});
