import sqlite3
import json

# DB 파일 연결
conn = sqlite3.connect("skin_care.db")
cursor = conn.cursor()

print("=== 📋 저장된 피부 기록 확인 ===")

try:
    cursor.execute("SELECT * FROM skin_records ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()

    if not rows:
        print("❌ 데이터가 없습니다.")
    else:
        for row in rows:
            # row 구조: (id, timestamp, score, detail_json, memo)
            r_id, r_time, r_score, r_json, r_memo = row
            print(f"\n[ID: {r_id}] 시간: {r_time}")
            print(f"   - 종합 점수: {r_score}점")
            
            # JSON 파싱해서 보기 좋게 출력
            try:
                details = json.loads(r_json)
                print(f"   - 상세 데이터: {list(details.keys())} ...")
            except:
                print(f"   - 상세 데이터: {r_json}")

except Exception as e:
    print(f"에러 발생: {e}")

conn.close()