import sys
import time
from PyQt5.QtCore import QThread, pyqtSignal

from hailo_platform import VDevice
from backend.stt import RealtimeSTT
from backend.llm import LLMResponseGenerator

class VoiceWorker(QThread):
    status_signal = pyqtSignal(str)
    user_text_signal = pyqtSignal(str)
    
    # [수정] 스트리밍용 신호들
    ai_start_signal = pyqtSignal()      # 말풍선 생성
    ai_chunk_signal = pyqtSignal(str)   # 글자 추가
    finished_signal = pyqtSignal()      # 종료

    def __init__(self, mode="VOICE", input_text=""):
        super().__init__()
        self.whisper_path = "/home/intelai/hailo/.venv/lib/python3.11/site-packages/hailo_tutorials/hefs/Whisper-Base.hef"
        self.llm_path = "/home/intelai/hailo/.venv/lib/python3.11/site-packages/hailo_tutorials/hefs/Qwen2-1.5B-Instruct.hef"
        
        self.running = False
        self.skin_context = "아직 측정된 피부 데이터가 없습니다."
        self.mode = mode
        self.input_text = input_text

    def set_context(self, skin_data):
        if not skin_data: return
        desc = "사용자의 현재 피부 상태:\n"
        part_map = {"chin":"턱", "lips":"입술", "right_cheek":"우볼", "left_cheek":"좌볼", "forehead":"이마"}
        for part, scores in skin_data.items():
            kor_part = part_map.get(part, part)
            oil = scores.get('Oil', 0)
            dry = scores.get('Dry', 0)
            desc += f"- {kor_part}: 유분{oil}%, 건조{dry}%\n"
        self.skin_context = desc

    def run(self):
        self.running = True
        try:
            params = VDevice.create_params()
            with VDevice(params) as vdevice:
                user_text = ""

                # 1. 입력 받기 (음성 or 텍스트)
                if self.mode == "VOICE":
                    self.status_signal.emit("음성 모델 로딩 중...")
                    with RealtimeSTT(vdevice, self.whisper_path) as stt:
                        self.status_signal.emit("👂 말씀해주세요!")
                        user_text = stt.wait_and_record(language="ko")
                        if not self.running or not user_text:
                            self.status_signal.emit("입력 없음")
                            return
                        self.user_text_signal.emit(user_text)
                elif self.mode == "TEXT":
                    user_text = self.input_text

                # 2. LLM 스트리밍 생성
                self.status_signal.emit("🤔 답변 작성 중...")
                
                with LLMResponseGenerator(vdevice, self.llm_path) as llm:
                    sys_prompt = (
                    "당신은 한국의 유능한 피부과 전문의 'Dr.Glow'입니다. "
                    "사용자의 피부 데이터를 분석하여 전문적이고 친절하게 조언해 주세요. "
                    "절대로 중국어나 한자를 사용하지 마세요. 오직 자연스러운 한국어만 사용하세요.\n"
                    f"[사용자 피부 데이터]\n{self.skin_context}"
                )
                    
                    # [핵심] 말풍선 먼저 만들고 -> 글자 채우기
                    self.ai_start_signal.emit()
                    
                    # stream_response는 generator이므로 for문으로 돌림
                    for token in llm.stream_response(user_text, max_tokens=200, system_prompt=sys_prompt):
                        if not self.running: break
                        self.ai_chunk_signal.emit(token)
                        # 너무 빠르면 UI가 못 따라갈 수 있으니 아주 미세한 지연 (선택사항)
                        # time.sleep(0.01) 

        except Exception as e:
            self.status_signal.emit(f"오류: {str(e)}")
            print(f"Voice Error: {e}")
        
        finally:
            self.finished_signal.emit()
            self.running = False

    def stop(self):
        self.running = False
        self.terminate()
        self.wait()