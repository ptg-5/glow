# stt.py

import sys
import time
import numpy as np
import pyaudio
from hailo_platform.genai import Speech2Text
from hailo_platform import VDevice

# 오디오 설정
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class RealtimeSTT:
    """
    음성 활동 감지 기반 실시간 음성 인식 클래스
    - 음성이 감지될 때까지 대기
    - 음성이 시작되면 끝날 때까지 계속 녹음
    - 침묵이 일정 시간 지속되면 녹음 종료 후 STT 실행
    """
    def __init__(self, vdevice: VDevice, whisper_hef: str, 
                 voice_threshold: int = 300,      # 음성 감지 임계값 (절댓값 평균)
                 silence_threshold: int = 150,    # 침묵 판단 임계값
                 silence_duration: float = 2.0,   # 침묵 지속 시간 (초)
                 max_recording_time: float = 60.0): # 최대 녹음 시간 (초)
        self.vdevice = vdevice
        self.whisper_hef = whisper_hef
        self.voice_threshold = voice_threshold
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_recording_time = max_recording_time
        
        self.p = None
        self.stream = None
        self.stt_model = None

    def __enter__(self):
        """PyAudio 및 STT 모델 초기화"""
        print("🎤 STT: 초기화 중...")
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            print("✅ STT: PyAudio 스트림 열림")
            
            print("🔄 STT: Whisper 모델 로딩 중...")
            self.stt_model = Speech2Text(self.vdevice, self.whisper_hef)
            print("✅ STT: 준비 완료\n")
            
        except Exception as e:
            print(f"❌ STT 초기화 실패: {e}", file=sys.stderr)
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """리소스 정리"""
        print("\n🧹 STT: 리소스 정리 중...")
        self._safe_release(self.stt_model)
        
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except:
                pass
                
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
        print("✅ STT: 정리 완료")

    def _safe_release(self, obj):
        """Hailo 객체 안전 해제"""
        if obj is None:
            return
        try:
            if hasattr(obj, "release"):
                obj.release()
            elif hasattr(obj, "__exit__"):
                obj.__exit__(None, None, None)
        except:
            pass

    def _get_volume(self, audio_chunk: bytes) -> int:
        """오디오 청크의 볼륨 계산 (절댓값 평균)"""
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            if len(audio_data) == 0:
                return 0
            return int(np.abs(audio_data).mean())
        except:
            return 0

    def wait_and_record(self, language: str = "ko") -> str:
        """
        음성이 감지될 때까지 대기 → 음성이 끝날 때까지 녹음 → STT 실행
        
        Returns:
            str: 인식된 텍스트 (없으면 빈 문자열)
        """
        if not self.stream or not self.stt_model:
            raise RuntimeError("STT가 초기화되지 않았습니다")

        # ========== 1단계: 음성 감지 대기 ==========
        print("🎧 음성을 기다리는 중...", end="", flush=True)
        
        while True:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                volume = self._get_volume(data)
                
                # 음성 감지
                if volume > self.voice_threshold:
                    print(f"\r🎤 음성 감지! (볼륨: {volume})     ")
                    break
                    
                # 대기 중 표시
                print(".", end="", flush=True)
                
            except Exception as e:
                print(f"\n⚠️ 오디오 읽기 오류: {e}", file=sys.stderr)
                continue

        # ========== 2단계: 음성 녹음 (침묵까지) ==========
        print("🔴 녹음 중... (말씀하세요)")
        
        frames = []
        silent_chunks = 0
        max_silent_chunks = int((self.silence_duration * RATE) / CHUNK)
        max_chunks = int((self.max_recording_time * RATE) / CHUNK)
        
        chunk_count = 0
        recording = True
        has_voice_detected = False  # 음성이 한 번이라도 감지되었는지 추적
        
        while recording and chunk_count < max_chunks:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                chunk_count += 1
                
                volume = self._get_volume(data)
                
                # 음성 감지 여부 확인
                if volume >= self.silence_threshold:
                    has_voice_detected = True
                    frames.append(data)  # 음성이 있을 때만 프레임 저장
                    
                    # 음성이 다시 감지되면 침묵 카운터 리셋
                    if silent_chunks > 0:
                        print()  # 줄바꿈
                        silent_chunks = 0
                    # 진행 표시
                    if len(frames) % 20 == 0:
                        elapsed = len(frames) * CHUNK / RATE
                        print(f"  🗣️  {elapsed:.1f}초 (볼륨: {volume})", flush=True)
                else:
                    # 침묵 감지
                    if has_voice_detected:
                        silent_chunks += 1
                        # 침묵 중에도 프레임은 저장 (자연스러운 끝을 위해)
                        frames.append(data)
                        
                        # 침묵 진행 표시 (디버깅용) - 볼륨도 표시
                        if silent_chunks % 10 == 0:
                            print(f"  🔇 침묵 감지 중... ({silent_chunks}/{max_silent_chunks}) 현재볼륨:{volume}", end="\r", flush=True)
                        
                        # 침묵 지속 시간 도달하면 녹음 종료
                        if silent_chunks >= max_silent_chunks:
                            print(f"\n⏸️  침묵 감지 ({self.silence_duration}초) - 녹음 종료")
                            recording = False
                    # else: 음성 감지 전 침묵은 버림 (프레임에 추가 안 함)
                    
            except Exception as e:
                print(f"⚠️ 녹음 중 오류: {e}", file=sys.stderr)
                continue

        # 최대 시간 도달
        if chunk_count >= max_chunks:
            print(f"⏰ 최대 녹음 시간 ({self.max_recording_time}초) 도달")

        total_duration = len(frames) * CHUNK / RATE
        print(f"✅ 녹음 완료 (총 {total_duration:.1f}초, 실제 오디오: {len(frames)}개 청크)")

        # ========== 3단계: STT 실행 ==========
        if len(frames) == 0:
            print("⚠️ 녹음된 오디오가 없습니다")
            return ""
            
        print("🔄 음성 인식 중...")
        
        audio_bytes = b"".join(frames)
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        
        full_text = ""
        try:
            param = self.stt_model.create_generator_params()
            param.set_language(language)
            
            for seg in self.stt_model.generate_all_segments(param, audio_data=audio_float):
                print(f"  [{seg.start_sec:.2f}s - {seg.end_sec:.2f}s]: {seg.text}")
                full_text += seg.text + " "
                
        except Exception as e:
            print(f"❌ STT 변환 오류: {e}", file=sys.stderr)
        
        recognized = full_text.strip()
        
        if recognized:
            print(f"\n✅ 최종 인식 텍스트: {recognized}\n")
        else:
            print("\n⚠️ 음성 인식 실패 또는 텍스트 없음\n")
            
        return recognized