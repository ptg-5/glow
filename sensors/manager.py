from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial

class SensorWorker(QThread):
    data_signal = pyqtSignal(float, float, float, bool)

    def __init__(self, port='/dev/ttyUSB0', baud=9600):
        super().__init__()
        self.running = True
        self.port = port
        self.baud = baud
        self.ser = None
        # 이전 값 기억용
        self.current_temp = 0.0
        self.current_hum = 0.0
        self.current_dist = 0.0

    def _connect_serial(self):
        try:
            if self.ser is None or not self.ser.is_open:
                self.ser = serial.Serial(self.port, self.baud, timeout=1)
                self.ser.reset_input_buffer()
                print(f"✅ {self.port} 연결 성공")
                return True
        except:
            return False

    def run(self):
        self._connect_serial()
        
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line: continue

                    if "온도" in line: # 온습도 데이터
                        try:
                            clean = line.replace(';', '')
                            parts = clean.split(',')
                            for p in parts:
                                if "온도" in p: self.current_temp = float(p.split(':')[1])
                                elif "습도" in p: self.current_hum = float(p.split(':')[1])
                        except: pass
                    else: # 거리 데이터
                        try:
                            val = float(line)
                            if 0 < val < 400: self.current_dist = val
                        except: pass
                    
                    # 매번 현재 상태 전송
                    is_seated = self.current_dist < 100
                    self.data_signal.emit(self.current_temp, self.current_hum, self.current_dist, is_seated)
                else:
                    time.sleep(0.1)
            except:
                time.sleep(1)
                self._connect_serial() # 재연결 시도

    def stop(self):
        self.running = False
        self.wait()
        if self.ser: self.ser.close()