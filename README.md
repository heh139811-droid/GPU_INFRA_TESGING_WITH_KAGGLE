# GPU_INFRA_TESGING_WITH_KAGGLE

자연어 브리프로 광고 이미지를 만드는 **사내 이미지 생성 에이전트**의 GPU 인프라 검증 저장소.

외부 이미지 생성 서비스 대신 오픈 웨이트 모델을 회사 GPU에서 직접 돌린다. 실행 엔진은 ComfyUI이고, 실험과 LoRA 학습은 Kaggle 무료 GPU(주 30시간)에서 한다.

## 구성

- **생성 엔진:** [ComfyUI](https://github.com/Comfy-Org/ComfyUI) (무료, GPL-3.0)
- **기본 모델:** [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) (Apache 2.0)
- **레이아웃 지정 모델:** [MOSS-Image-SFT](https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT) (Apache 2.0)
- **예비 모델:** [Kromoss](https://huggingface.co/lodestones/Kromoss) (Apache 2.0)
- **한글 카피:** 생성 모델이 아니라 Pillow 후처리로 합성

사내 업무용도 라이선스상 상업 이용이라 Apache 2.0 모델만 쓴다. 자세한 이유는 아키텍처 문서에 있다.

## 문서

| 문서 | 내용 |
|---|---|
| [docs/01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md) | 전체 구성, 모델 선정과 라이선스, 라우팅 규칙, ComfyUI 운영 방법 |
| [docs/02-SERVER-COST.md](docs/02-SERVER-COST.md) | 노트북·Kaggle·클라우드·사내 PC 비용 비교와 손익분기 |

## 빠른 시작 (Windows, NVIDIA GPU)

```powershell
uv tool install comfy-cli
comfy --workspace=C:\ComfyUI install --fast-deps
comfy --workspace=C:\ComfyUI launch
```

브라우저에서 `http://127.0.0.1:8188`로 접속한다. 모델 파일 위치와 서버 운영 방법은 [아키텍처 문서](docs/01-ARCHITECTURE.md#comfyui-운영)를 본다.

## 진행 상황

- [x] 모델 후보 조사 및 라이선스 확인
- [x] 아키텍처, 비용 문서 작성
- [ ] 개발 노트북(RTX 5070 8GB)에서 ComfyUI + Z-Image-Turbo PoC
- [ ] Z-Image-Turbo / MOSS-Image-SFT 광고 소재 품질 비교
- [ ] 워크플로 템플릿(API 형식 JSON) 확정
- [ ] Kaggle에서 제품 LoRA 학습
- [ ] 사내 에이전트(FastAPI) + ComfyUI 서버 시범 운영
