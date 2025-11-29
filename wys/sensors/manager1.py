from PyQt5.QtCore import QThread, pyqtSignal
import time
import random
import serial
import time
import csv
from datetime import datetime

class SensorWorker(QThread):
       # 온습도, 거리, 착석여부(Boolean) 신호 보냄
    data_signal = pyqtSignal(float, float, float, bool)
    def __init__(self, port='/dev/ttyUSB0', baud=9600):
        super().__init__()
        self.running = True
        self.port = port
        self.baud = baud
        self.ser = None

    def _connect_serial(self):
        if self.ser is None or not self.ser.is_open:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.ser.flush()
            print(f"{self.port} 포트 연결 완료 (SensorWorker)")

    def _read_line(self):
        """시리얼에서 한 줄 읽어오기 (문자열, 공백 제거)"""
        if self.ser is None:
            return ""
        try:
            line = self.ser.readline().decode('utf-8').strip()
            return line
        except Exception:
            return ""

    def run(self):
        print("🌡️  센서 스레드 시작")
        last_temp_humi_time = 0.0   # 온습도 2초 주기
        last_distance_time = 0.0    # 거리 1초 주기

        # 기본값 (데이터 안 들어올 때 대비)
        current_temp = 0.0
        current_humi = 0.0
        current_dist = 999.0
        current_seated = False

        try:
            self._connect_serial()
        except Exception as e:
            print(f"시리얼 연결 실패: {e}")
            return

        while self.running:
            line = self._read_line()
            now = time.time()

            if not line:
                time.sleep(0.01)
                continue

            # 1) 온습도 패킷: "온도:21.5,습도:41.2;"
            if "온도" in line and "습도" in line:
                if now - last_temp_humi_time >= 2.0:   # 2초마다 처리
                    try:
                        clean = line.strip(';')
                        parts = dict(s.strip().split(':') for s in clean.split(','))

                        temp_val = parts.get("온도", "").strip()
                        humi_val = parts.get("습도", "").strip()
                        if not temp_val or not humi_val:
                            raise ValueError("빈 값")

                        current_temp = float(temp_val)
                        current_humi = float(humi_val)
                        last_temp_humi_time = now

                        ts = datetime.now().strftime("%H:%M:%S")
                        print(f"[{ts}] 온도: {current_temp:.1f} ℃, 습도: {current_humi:.1f} %")

                    except Exception as e:
                        print(f"온습도 파싱 에러: {e}, line={line}")

            # 2) 거리 패킷: 숫자만 (예: "123.4")
            else:
                if now - last_distance_time >= 1.0:     # 1초마다 처리
                    try:
                        current_dist = float(line)
                        # 30cm 이하일 때 어떤 동작 실행할 자리
                        if current_dist <= 30:
                            # TODO: 여기서 원하는 동작 구현
                            # 예) 화면 켜기, 알림, 로그 등
                            pass

                        # 착석 여부 판단 (예: 50cm 이내면 착석)
                        current_seated = current_dist < 50.0
                        last_distance_time = now

                        ts = datetime.now().strftime("%H:%M:%S")
                        print(f"[{ts}] 거리: {current_dist:.1f} cm, seated={current_seated}")

                    except ValueError:
                        # 숫자가 아니면 무시
                        pass

            # 최신 값들을 UI로 emit (너무 자주면 부담되므로 여기서도 약간 쉼)
            self.data_signal.emit(current_temp, current_humi, current_dist, current_seated)
            time.sleep(0.01)

    def stop(self):
        self.running = False
        self.wait()
        if self.ser and self.ser.is_open:
            self.ser.close()

