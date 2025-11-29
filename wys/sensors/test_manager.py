import serial
import time
import csv
from datetime import datetime

SERIAL_PORT = '/dev/ttyUSB0'   # 환경에 맞게 변경
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
ser.flush()
print(f"{SERIAL_PORT} 포트 연결 완료, 데이터 수신 중...")

csv_filename = "sensor_log.csv"
csv_file = open(csv_filename, mode="a", newline="", encoding="utf-8")
writer = csv.writer(csv_file)

if csv_file.tell() == 0:
    writer.writerow(["timestamp", "temperature", "humidity", "distance_cm"])

last_temp_humi_time = 0.0   # 온습도 마지막 처리 시각
last_distance_time = 0.0    # 거리 마지막 처리 시각

try:
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            continue

        if not line:
            time.sleep(0.01)
            continue

        now = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1) 온습도 패킷: "온도:21.5,습도:41.2;"
        if "온도" in line and "습도" in line:
            # 2초마다만 처리
            if now - last_temp_humi_time < 2.0:
                continue

            try:
                clean = line.strip(';')
                parts = dict(s.strip().split(':') for s in clean.split(','))

                temp_val = parts.get("온도", "").strip()
                humi_val = parts.get("습도", "").strip()

                if not temp_val or not humi_val:
                    continue

                t = float(temp_val)
                h = float(humi_val)

                print(f"[{now_str}] 온도: {t:.1f} ℃, 습도: {h:.1f} %")

                writer.writerow([now_str, t, h, ""])
                csv_file.flush()

                last_temp_humi_time = now

            except Exception:
                continue

        # 2) 거리 패킷: 숫자만 (예: "123.4")
        else:
            # 1초마다만 처리
            if now - last_distance_time < 1.0:
                continue

            try:
                d = float(line)
            except ValueError:
                continue

            print(f"[{now_str}] 거리: {d:.1f} cm")

            # ✅ 거리 30cm 이하일 때 실행할 동작 (직접 구현해서 넣기)
            if d <= 30:
                # TODO: 여기 안에 원하는 동작 구현
                # 예시)
                #   - 화면 켜기
                #   - LED 패턴 변경
                #   - 다른 프로그램 실행
                pass

            writer.writerow([now_str, "", "", d])
            csv_file.flush()

            last_distance_time = now

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n사용자 종료로 프로그램을 종료합니다.")

finally:
    csv_file.close()
    ser.close()

