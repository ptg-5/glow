# Project GLOW FOREVER


* 당신의 거울이 피부 분석과 화장품 추천까지 해 주는 온디바이스 AI 뷰티 코치 프로젝트입니다​
Raspberry Pi 5와 Hailo 가속기 위에서 PyQt UI, 피부 비전 모델, Qwen2.5 1.5B 기반 LLM까지 모두 로컬에서 동작하는 엣지 뷰티 솔루션을 목표로 합니다​

## High Level Design

* GLOW FOREVER는 라즈베리파이 5 + Hailo-10H를 기반으로 카메라 입력 → 피부 분석 모델 추론 → 결과 정리 → 온디바이스 Qwen LLM 추천까지 하나의 파이프라인으로 구성됩니다​
UI는 라즈베리파이에서 직접 실행되는 PyQt 풀스크린 앱 형태이며, 향후 동일 API를 활용해 웹 UI로 확장 가능한 구조를 전제로 합니다​

+-------------------------------------------------------------+
|                 PyQt Smart Mirror UI (Fullscreen)           |
|  - 카메라 프리뷰 (USB / RPi Cam)                            |
|  - 실시간 피부 상태 오버레이                               |
|  - LLM 추천 결과 카드 / 대화 영역                          |
+--------------------------+----------------------------------+
                           |
                           v
+-------------------------------------------------------------+
|        Application Core (Python, main.py)                   |
|  - 카메라 프레임 캡처 (OpenCV/Libcamera)                   |
|  - Hailo 추론 호출 (skin_model.hef 등)                      |
|  - 지성/건성/복합성/민감성 및 트러블·주름·모공 등 스코어 산출 |
|  - Qwen2.5 1.5B LLM 프롬프트 구성 및 응답 파싱              |
+--------------------------+----------------------------------+
                           |
                           v
+-------------------------------------------------------------+
|          AI Inference Layer (on-device)                     |
|  - Vision: pt → ONNX → HEF 변환된 피부 분석 모델들          |
|    * 피부 타입 분류 모델                                    |
|    * 트러블/색소침착/주름/턱처짐/모공/입술 건조도 스코어링  |
|  - LLM: Qwen2.5 1.5B (KO 화장품 데이터로 파인튜닝)          |
|    * int4/gguf 양자화 + 온디바이스 추론 (Ollama/llama.cpp 등)|
+--------------------------+----------------------------------+
                           |
                           v
+-------------------------------------------------------------+
|   Hardware & OS Layer                                       |
|  - Raspberry Pi 5 (4GB 이상 권장)                           |
|  - Hailo AI HAT / Hailo-10H (M.2)                           |
|  - Raspberry Pi Camera (8MP) + 1080p USB 웹캠               |
|  - Raspberry Pi OS 64-bit                                  |
+-------------------------------------------------------------+

Vision 쪽은 Hailo SDK와 Python API를 이용해 HEF 모델을 로딩하고, 피부 타입과 각 지표들을 실시간으로 산출하는 구조를 가정합니다​
LLM은 Qwen2.5 1.5B를 한국어 화장품/성분 데이터로 파인튜닝한 모델을 온디바이스에서 양자화해 실행하며, 피부 분석 결과를 입력으로 받아 제품 추천과 후속 질문 응답을 생성하는 역할을 합니다

## Clone code


```shell
git clone https://github.com/ptg-5/glow.git
cd glow-forever

```

## Prerequite

* (프로잭트를 실행하기 위해 필요한 dependencies 및 configuration들이 있다면, 설치 및 설정 방법에 대해 기술)

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
하드웨어 및 OS 요구사항은 다음과 같습니다​

Raspberry Pi 5 (4GB 이상 권장), 64-bit Raspberry Pi OS Bookworm 최신 버전​

Hailo-10 기반 AI HAT 또는 AI Kit (M.2 HAT+ 포함), hailo-all 패키지로 드라이버·HailoRT 설치 완료 상태​

카메라: 8MP Raspberry Pi Camera Module + 1080p USB 웹캠 중 하나 또는 둘 다 연결 가능​

소프트웨어 및 Python 환경은 아래를 가정합니다​

Python 3.10+

Hailo Python API / HailoRT

OpenCV, NumPy 등 비전 라이브러리

PyQt5 또는 PyQt6 (풀스크린 스마트 미러 UI용)

Qwen2.5 1.5B 온디바이스 추론용 스택 (예: llama.cpp / Ollama / ONNX Runtime 등 중 택1) 및 양자화된 모델 파일​

Python 가상환경 및 기본 의존성 설치 예시는 다음과 같습니다​

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

requirements.txt에는 opencv-python, pyqt5 또는 pyqt6, numpy, Hailo 관련 패키지, LLM 실행용 라이브러리(예: llama-cpp-python 또는 onnxruntime-genai)를 포함하는 구성을 가정합니다​

## Steps to build

Vision 모델은 pt → ONNX → HEF 파이프라인으로 계속 튜닝·교체할 예정이므로, 빌드 과정에서 ONNX/HEF 파일 배치와 설정 파일 생성을 자동화하는 것이 좋습니다​
또한 이후 웹 UI로 확장될 수 있도록 PyQt 앱과 코어 로직을 분리한 디렉터리 구조를 전제로 합니다​

예시 절차는 다음과 같습니다​

shell
cd ~/glow-forever
source .venv/bin/activate

1) Vision 모델 변환 / 배치 (옵션: 이미 변환된 HEF를 받아 쓸 수도 있음)
scripts/export_to_onnx.py         # pt -> onnx
scripts/compile_to_hef.sh         # onnx -> hef (hailo_model_zoo / hailomz 활용)

mkdir -p models
예시: 변환된 HEF 파일들을 models/ 아래로 복사
cp /path/to/skin_type.hef models/
cp /path/to/skin_trouble.hef models/

2) PyQt 리소스 및 설정 파일 생성
python tools/gen_qt_resources.py
python tools/gen_default_config.py

make
make install
여기서 make는 모델 다운로드/복사, 기본 설정 파일 생성, 로그 디렉터리 생성 등 개발 편의를 위한 작업을 포함하도록 설계할 수 있습니다​
make install에서는 부팅 시 main.py가 자동으로 실행되도록 systemd 서비스 또는 데스크톱 자동 실행 설정을 배치하는 역할로 사용할 수 있습니다

## Steps to run

일반적인 실행은 라즈베리파이에서 자동 부팅 실행이지만, 개발 단계에서는 다음과 같이 수동 실행을 할 수 있습니다​

shell
cd ~/glow-forever
source .venv/bin/activate

python main.py \
  --camera rpi \
  --usb-camera 0 \
  --skin-type-model models/skin_type.hef \
  --skin-score-model models/skin_score.hef \
  --llm-backend qwen-local \
  --llm-model-path /path/to/qwen2.5-1.5b-ko.gguf
예상 동작 플로우는 다음과 같습니다​

RPi 카메라(8MP) 또는 1080p USB 웹캠에서 얼굴 영상 프레임을 받아와 Hailo 가속기로 전달합니다​

피부 타입(지성/건성/복합성/민감성)과 트러블 정도, 색소침착 정도, 주름 정도, 턱처짐 정도, 모공 정도, 입술 건조도 등을 각 HEF 모델 혹은 멀티헤드 모델로부터 스코어로 얻습니다​

main.py는 이 스코어들을 구조화된 형태(예: JSON dict)로 정리한 뒤, Qwen2.5 1.5B 온디바이스 LLM에 프롬프트로 전달합니다​

LLM은 한국 화장품 이름/성분으로 학습된 지식을 기반으로 스킨케어/연고/메이크업 카테고리별 추천과 간단한 설명을 생성하고, PyQt UI는 이를 카드·텍스트 형태로 표시합니다​

사용자는 이후 “추가 분석” 또는 “질문하기” 버튼을 눌러 LLM과 추가 질의응답을 진행할 수 있습니다​

실제 인자 이름(--camera, --llm-backend 등)은 코드 구현에 맞게 자유롭게 바꾸면 되고, README에는 대표적인 개발용 실행 예시만 유지하면 됩니다​



## Output

실행 결과 화면은 PyQt 기반 풀스크린 스마트 미러 레이아웃을 다음과 같이 가정합니다​

좌측: 실시간 카메라 프리뷰와 함께 얼굴 감지 박스 및 트러블/색소침착/모공 영역 등 오버레이 표시​

우측 상단: 피부 타입(지성/건성/복합성/민감성)과 각 지표(트러블, 색소침착, 주름, 턱처짐, 모공, 입술 건조도)가 게이지/점수 형태로 정리된 패널​

우측 하단: LLM이 생성한 “오늘 피부 상태 요약 + 추천 루틴 + 제품 제안” 카드 목록 및 간단한 설명 텍스트​


![./result.jpg](./result.jpg)

## Appendix

온디바이스 LLM 관련 메모​
Qwen2.5 1.5B 계열 모델은 1.5B 파라미터 규모로, 적절한 양자화(INT4/gguf)와 스트리밍 디코딩을 사용하면 엣지 디바이스에서도 현실적인 속도로 추론이 가능합니다​

한국 화장품 이름·성분 데이터셋으로 파인튜닝된 버전은 “피부 상태 → 카테고리별 제품 추천 → 사용법/주의사항”과 같은 뷰티 특화 프롬프트 구조에 최적화할 수 있습니다​

Hailo + Raspberry Pi 참고​
Raspberry Pi AI Kit/Hailo 사용 시 sudo apt install hailo-all로 드라이버, HailoRT, TAPPAS 등을 한 번에 설치할 수 있으며, rpicam-apps와 연동한 카메라+NPU 파이프라인 예제를 참고하면 구현이 편해집니다​

hailo_model_zoo나 관련 도구를 활용하면 YOLO 등 ONNX 모델을 HEF로 컴파일하여 라즈베리파이 5에서 효율적으로 구동할 수 있고, 이 과정은 pt → onnx → hef 워크플로우와 잘 맞습니다​

PyQt 기반 스마트 미러 참고​
기존 PyQt 스마트 미러 프로젝트들은 풀스크린, 프레임 없는 윈도우, 항상 위에 표시, 모듈형 위젯 구조 등을 사용하므로, GLOW FOREVER에서도 동일한 패턴으로 피부 분석 위젯과 추천 위젯을 분리해서 설계할 수 있습니다​​

이후 웹 UI로 확장할 계획이라면, 코어 로직(카메라 캡처, 추론, LLM 호출)을 REST API 또는 내부 서비스 레이어로 분리하고, PyQt는 그 API를 호출하는 클라이언트로 두면 MagicMirror 스타일 웹 기반 UI로 전환하기가 수월합니다​

향후 추가 예정 기능 (퍼스널컬러 등)​
퍼스널컬러 분석은 현재 단계에서는 보류하지만, 추후 얼굴/피부 톤 특징량을 추가로 추출해 별도 HEF 모델 또는 LLM 기반 규칙으로 통합할 수 있습니다​

히스토리 저장, 주간/월간 피부 컨디션 변화 그래프, 알림 기능(예: “선크림 미사용일이 3일 연속입니다”) 등은 스마트 미러의 지속 사용성을 높이는 기능으로 README 하단에 “Future Work” 섹션을 추가해도 좋습니다​

이제 이 초안을 기반으로 실제 디렉터리 구조, 옵션 이름, 모델 파일 경로만 네 프로젝트에 맞게 바꿔 주면 GLOW FOREVER README의 기본 틀은 거의 완성될 거야