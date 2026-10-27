import re
import threading

MODEL_ID = "Helsinki-NLP/opus-mt-ko-en"
HANGUL = re.compile(r"[\uac00-\ud7a3]")

_lock = threading.Lock()
_model = None
_tokenizer = None


def _load():
    global _model, _tokenizer
    if _model is None:
        from transformers import MarianMTModel, MarianTokenizer

        _tokenizer = MarianTokenizer.from_pretrained(MODEL_ID)
        _model = MarianMTModel.from_pretrained(MODEL_ID).eval()


def ko_to_en(text: str) -> str:
    text = text.strip()
    if not HANGUL.search(text):
        return text
    # 문장 단위로 끊어야 긴 브리프에서 뒷부분이 잘리지 않는다.
    parts = [p.strip() for p in re.split(r"(?<=[.!?。])\s+|\n+|,\s*", text) if p.strip()]
    with _lock:
        _load()
        batch = _tokenizer(parts, return_tensors="pt", padding=True, truncation=True, max_length=256)
        out = _model.generate(**batch, max_new_tokens=256, num_beams=4)
        decoded = _tokenizer.batch_decode(out, skip_special_tokens=True)
    return ", ".join(d.strip().rstrip(".") for d in decoded if d.strip())
