
# main.py

import sys
from hailo_platform import VDevice
from stt import RealtimeSTT
from llm import LLMResponseGenerator

# ========== 설정 ==========
# WHISPER_HEF = "../hefs/Whisper-Base.hef"
# LLM_HEF = "../hefs/Qwen2-1.5B-Instruct.hef"
WHISPER_HEF = "/home/intelai/hailo/.venv/lib/python3.11/site-packages/hailo_tutorials/hefs/Whisper-Base.hef"
# LLM_HEF = "../hefs/Qwen2-1.5B-Instruct.hef"
LLM_HEF = "/home/intelai/hailo/.venv/lib/python3.11/site-packages/hailo_tutorials/hefs/Qwen2-1.5B-Instruct.hef"
LORA_NAME = ""
# main.py

# main.py

import sys
from hailo_platform import VDevice
from stt import RealtimeSTT
from llm import LLMResponseGenerator

# ========== 설정 ==========
# WHISPER_HEF = "../hefs/Whisper-Base.hef"
# LLM_HEF = "../hefs/Qwen2-1.5B-Instruct.hef"
LORA_NAME = ""

# 음성 감지 설정 (환경에 맞게 조정)
VOICE_THRESHOLD = 800       # 음성 시작 감지 임계값 (명확한 음성만)
SILENCE_THRESHOLD = 800     # 침묵 판단 임계값 (배경 소음보다 높게!)
SILENCE_DURATION = 1.5      # 침묵 지속 시간 (초) - 이 시간만큼 침묵하면 녹음 종료
MAX_RECORDING_TIME = 30.0   # 최대 녹음 시간 (초)

# LLM 설정
MAX_TOKENS = 150
SYSTEM_PROMPT = "You are a helpful AI assistant. Answer in Korean if the question is in Korean."
# =========================


def main_continuous_loop():
    """
    연속 대화 루프:
    음성 대기 → 음성 끝날때까지 녹음 → STT → LLM 응답 → 다시 음성 대기
    Ctrl+C로 종료
    """
    print("=" * 70)
    print("🚀 실시간 음성 대화 시스템")
    print("=" * 70)
    print(f"📁 Whisper: {WHISPER_HEF}")
    print(f"📁 LLM: {LLM_HEF}")
    print(f"🔊 음성 감지 임계값: {VOICE_THRESHOLD}")
    print(f"🔇 침묵 판단 임계값: {SILENCE_THRESHOLD}")
    print(f"⏱️  침묵 지속 시간: {SILENCE_DURATION}초")
    print(f"⏰ 최대 녹음 시간: {MAX_RECORDING_TIME}초")
    print("=" * 70)
    print("💡 Ctrl+C로 종료\n")

    try:
        # VDevice 초기화
        params = VDevice.create_params()
        params.group_id = "1"
        
        with VDevice(params) as vdevice:
            # STT 및 LLM 시스템 초기화
            with RealtimeSTT(vdevice, WHISPER_HEF,
                           voice_threshold=VOICE_THRESHOLD,
                           silence_threshold=SILENCE_THRESHOLD,
                           silence_duration=SILENCE_DURATION,
                           max_recording_time=MAX_RECORDING_TIME) as stt_system:
                
                with LLMResponseGenerator(vdevice, LLM_HEF, LORA_NAME) as llm_system:
                    
                    conversation_count = 0
                    
                    # 무한 대화 루프
                    while True:
                        conversation_count += 1
                        print(f"\n{'='*70}")
                        print(f"💬 대화 #{conversation_count}")
                        print(f"{'='*70}")
                        
                        # 1. 음성 대기 및 녹음 (말 끝날때까지)
                        recognized_text = stt_system.wait_and_record(language="ko")
                        
                        # 2. 인식 결과 확인
                        if not recognized_text:
                            print("⚠️ 음성 인식 실패 - 다시 시도하세요\n")
                            continue
                        
                        print(f"📝 인식된 질문: \"{recognized_text}\"")
                        
                        # 3. LLM 응답 생성
                        llm_response = llm_system.generate_response(
                            user_prompt=recognized_text,
                            max_tokens=MAX_TOKENS,
                            system_prompt=SYSTEM_PROMPT
                        )
                        
                        # 4. 응답 결과 확인
                        if llm_response:
                            print(f"📊 [응답 완료: {len(llm_response)} 문자]")
                        else:
                            print("⚠️ LLM 응답이 비어있습니다")

    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 중단됨")
    
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n" + "=" * 70)
        print("👋 시스템 종료")
        print("=" * 70)


if __name__ == "__main__":
    main_continuous_loop()