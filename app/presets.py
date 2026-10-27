MODELS = {
    "zimage": {
        "label": "Z-Image Turbo",
        "desc": "최신 실사 모델, 8스텝",
        "workflow": "zimage_turbo_t2i_api.json",
        "requires": [
            ("diffusion_models", "z_image_turbo_nvfp4.safetensors"),
            ("text_encoders", "qwen_3_4b_fp8_mixed.safetensors"),
            ("vae", "ae.safetensors"),
        ],
        # cfg 1.0으로 돌리는 증류 모델이라 네거티브 프롬프트가 적용되지 않는다.
        "negative": False,
    },
    "sdxl": {
        "label": "SDXL",
        "desc": "가볍고 빠름, 품질은 낮음",
        "workflow": "sdxl_t2i_api.json",
        "requires": [("checkpoints", "sd_xl_base_1.0.safetensors")],
        "negative": True,
    },
}

STYLES = {
    "studio": {
        "label": "스튜디오",
        "desc": "깔끔한 배경, 소프트박스 조명",
        "prompt": "professional studio product photography, seamless backdrop, softbox lighting, "
        "crisp soft shadows, commercial advertising photo, sharp focus, high detail",
    },
    "lifestyle": {
        "label": "라이프스타일",
        "desc": "자연광, 실제 생활 공간",
        "prompt": "lifestyle advertising photo, natural window light, cozy real-life interior, "
        "warm tones, shallow depth of field, 50mm lens, editorial look",
    },
    "minimal": {
        "label": "미니멀",
        "desc": "파스텔 단색 배경, 여백",
        "prompt": "minimalist product shot, clean pastel solid background, soft diffused light, "
        "generous negative space, modern aesthetic, centered composition",
    },
    "premium": {
        "label": "프리미엄",
        "desc": "어두운 배경, 림 라이트",
        "prompt": "luxury premium advertising photo, dramatic rim lighting, dark elegant background, "
        "glossy reflective surface, cinematic contrast, high-end commercial look",
    },
    "flatlay": {
        "label": "플랫레이",
        "desc": "위에서 내려다본 구도",
        "prompt": "top-down flat lay composition, overhead shot, neatly arranged props, "
        "even soft lighting, styled tabletop, commercial photo",
    },
    "outdoor": {
        "label": "야외",
        "desc": "햇살, 자연 배경",
        "prompt": "outdoor advertising photo, golden hour sunlight, natural scenery background, "
        "fresh airy mood, bokeh, vibrant but natural colors",
    },
    "none": {
        "label": "스타일 없음",
        "desc": "입력한 내용만 사용",
        "prompt": "",
    },
}

# SDXL 학습 해상도 버킷에 맞춘 크기
ASPECTS = {
    "1:1": {"label": "1:1 피드", "width": 1024, "height": 1024},
    "4:5": {"label": "4:5 세로 피드", "width": 896, "height": 1152},
    "9:16": {"label": "9:16 스토리·릴스", "width": 768, "height": 1344},
    "16:9": {"label": "16:9 배너", "width": 1344, "height": 768},
    "3:2": {"label": "3:2 가로", "width": 1216, "height": 832},
}

NEGATIVE = (
    "text, letters, words, watermark, logo, signature, blurry, lowres, jpeg artifacts, "
    "deformed, distorted, disfigured, extra limbs, bad anatomy, bad hands, duplicate, "
    "oversaturated, cartoon, illustration, 3d render"
)


def build_prompt(subject_en: str, style: str) -> str:
    style_prompt = STYLES.get(style, STYLES["none"])["prompt"]
    return f"{subject_en}, {style_prompt}" if style_prompt else subject_en
