import sys
from hailo_platform.genai import LLM
from hailo_platform import VDevice
from typing import List, Dict, Iterator # Iterator 추가

class LLMResponseGenerator:
    def __init__(self, vdevice: VDevice, llm_hef: str, lora_name: str = ""):
        self.vdevice = vdevice
        self.llm_hef = llm_hef
        self.lora_name = lora_name
        self.llm_model = None

    def __enter__(self):
        print("🧠 LLM: 모델 로드 중...")
        try:
            self.llm_model = LLM(self.vdevice, self.llm_hef, self.lora_name)
            print("✅ LLM: 준비 완료")
        except Exception as e:
            print(f"❌ LLM 로드 실패: {e}", file=sys.stderr)
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.llm_model:
            self.llm_model.release()
            self.llm_model = None

    # [핵심 수정] 반환 타입을 Iterator[str]로 변경하고 yield 사용
    def stream_response(self, user_prompt: str, 
                          max_tokens: int = 150,
                          system_prompt: str = "You are a helpful AI assistant.") -> Iterator[str]:
        
        if not self.llm_model:
            raise RuntimeError("LLM 모델 미로드")
        
        if not user_prompt.strip():
            return

        structured_prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print("\n💬 LLM 응답 생성 시작...")
        
        try:
            # Hailo SDK의 generate 함수가 generator를 반환함
            with self.llm_model.generate(structured_prompt, 
                                       max_generated_tokens=max_tokens, 
                                       seed=31) as gen:
                for token in gen:
                    # CLI 확인용 (원하면 삭제 가능)
                    print(token, end="", flush=True)
                    # [중요] 한 글자씩 밖으로 던짐
                    if "<|im_end|>" in token:
                        break
                    yield token
                    
            print("\n✅ 응답 완료")
            
        except Exception as e:
            print(f"\n❌ 오류: {e}", file=sys.stderr)
            yield f"[오류 발생: {e}]"