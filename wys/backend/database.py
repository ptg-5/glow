import sqlite3
import json
from datetime import datetime

class DBManager:
    def __init__(self, db_path="skin_care.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # 환경 로그 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS env_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL,
                humidity REAL,
                is_seated INTEGER
            )
        """)
        
        # 피부 진단 기록 테이블 (수정됨)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                summary_score INTEGER,
                detail_json TEXT,  -- 부위별 상세 점수 (JSON 문자열)
                memo TEXT
            )
        """)
        self.conn.commit()

    def insert_env_log(self, temp, hum, seated):
        self.conn.execute(
            "INSERT INTO env_logs (timestamp, temperature, humidity, is_seated) VALUES (?, ?, ?, ?)",
            (datetime.now(), temp, hum, 1 if seated else 0)
        )
        self.conn.commit()

    def insert_skin_record(self, summary_score, detail_data):
        """
        detail_data (dict): {"chin": {"Dry": 10, ...}, ...}
        """
        json_str = json.dumps(detail_data, ensure_ascii=False)
        self.conn.execute(
            "INSERT INTO skin_records (timestamp, summary_score, detail_json) VALUES (?, ?, ?)",
            (datetime.now(), summary_score, json_str)
        )
        self.conn.commit()
        print(f"💾 [DB] 피부 진단 결과 저장 완료 (ID: {self.conn.execute('SELECT last_insert_rowid()').fetchone()[0]})")

    def close(self):
        self.conn.close()

    def fetch_recent_records(self, limit=10):
        """최근 피부 진단 기록 10개 가져오기"""
        try:
            cursor = self.conn.execute(
                "SELECT id, timestamp, summary_score, detail_json FROM skin_records ORDER BY id DESC LIMIT ?", 
                (limit,)
            )
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                r_id, r_time, r_score, r_json = row
                try:
                    details = json.loads(r_json)
                except:
                    details = {}
                
                results.append({
                    "id": r_id,
                    "time": r_time, # 문자열 그대로 사용 (YYYY-MM-DD HH:MM:SS.ssssss)
                    "score": r_score,
                    "details": details
                })
            return results
        except Exception as e:
            print(f"DB 조회 에러: {e}")
            return []