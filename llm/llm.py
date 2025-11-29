# llm.py

import sys
from hailo_platform.genai import LLM
from hailo_platform import VDevice
from typing import List, Dict

class LLMResponseGenerator:
    """
    LLM 응답 생성 클래스 - 스트리밍으로 응답하고 최종 텍스트 반환
    """
    def __init__(self, vdevice: VDevice, llm_hef: str, lora_name: str = ""):
        self.vdevice = vdevice
        self.llm_hef = llm_hef
        self.lora_name = lora_name
        self.llm_model = None

    def __enter__(self):
        """LLM 모델 로드"""
        print("🧠 LLM: 모델 로드 중...")
        try:
            self.llm_model = LLM(self.vdevice, self.llm_hef, self.lora_name)
            print("✅ LLM: 준비 완료")
        except Exception as e:
            print(f"❌ LLM 로드 실패: {e}", file=sys.stderr)
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """LLM 모델 해제"""
        self._safe_release(self.llm_model)
        self.llm_model = None

    def _safe_release(self, obj):
        if obj is None:
            return
        try:
            if hasattr(obj, "release"):
                obj.release()
            elif hasattr(obj, "__exit__"):
                obj.__exit__(None, None, None)
        except:
            pass

    def generate_response(self, user_prompt: str, 
                         max_tokens: int = 150,
                         system_prompt: str = "You are a helpful AI assistant.") -> str:
        """
        사용자 입력에 대한 LLM 응답 생성
        
        Args:
            user_prompt: STT로 인식된 사용자 질문
            max_tokens: 최대 생성 토큰 수
            system_prompt: 시스템 프롬프트
            
        Returns:
            str: LLM의 최종 응답 텍스트
        """
        if not self.llm_model:
            raise RuntimeError("LLM 모델이 로드되지 않았습니다")
        
        if not user_prompt.strip():
            print("⚠️ 빈 프롬프트 - LLM 호출 건너뜀")
            return ""

        structured_prompt: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print("\n💬 LLM 응답 생성 중...\n")
        print("─" * 60)
        
        full_response = ""
        
        try:
            with self.llm_model.generate(structured_prompt, 
                                        max_generated_tokens=max_tokens, 
                                        seed=31) as gen:
                for token in gen:
                    print(token, end="", flush=True)
                    full_response += token
                    
            print("\n" + "─" * 60)
            print("✅ 응답 완료\n")
            
        except Exception as e:
            print(f"\n❌ LLM 응답 생성 오류: {e}", file=sys.stderr)
        
        return full_response.strip()