import sqlite3
import json
from datetime import datetime

class DBManager:
    def __init__(self, db_path="skin_care.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # [NEW] 사용자 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT
            )
        """)
        
        # [수정] 피부 기록 테이블 (user_id 추가)
        # 기존 테이블이 있다면 삭제하고 다시 만드는 게 개발 단계에선 편합니다.
        # (터미널에서 rm skin_care.db 하세요)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME,
                summary_score INTEGER,
                detail_json TEXT,
                memo TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # 환경 로그 (기존 유지)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS env_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL,
                humidity REAL,
                is_seated INTEGER
            )
        """)
        self.conn.commit()

    # --- [NEW] 사용자 관련 함수 ---
    def register_user(self, username, password, name):
        try:
            self.conn.execute(
                "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                (username, password, name)
            )
            self.conn.commit()
            return True, "가입 성공"
        except sqlite3.IntegrityError:
            return False, "이미 존재하는 아이디입니다."
        except Exception as e:
            return False, f"오류: {e}"

    def login_user(self, username, password):
        cursor = self.conn.execute(
            "SELECT id, name FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "name": user[1]} # 성공 시 정보 반환
        else:
            return None # 실패

    # --- [수정] 기록 저장 (user_id 포함) ---
    def insert_skin_record(self, summary_score, detail_data, user_id=0):
        # user_id=0 은 비회원(Guest)으로 간주
        json_str = json.dumps(detail_data, ensure_ascii=False)
        # self.conn.execute("""
        #     CREATE TABLE IF NOT EXISTS skin_records (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         user_id INTEGER,
        #         timestamp DATETIME,
        #         summary_score INTEGER,
        #         detail_json TEXT,
        #         memo TEXT,
        #         FOREIGN KEY(user_id) REFERENCES users(id)
        #     )
        # """)
        print("insert_skin_record>json_str>>",json_str)
        print("insert_skin_record>summary_score>>",summary_score)
        print("insert_skin_record>user_id>>",user_id)
        
        self.conn.execute(
            "INSERT INTO skin_records (user_id, timestamp, summary_score, detail_json) VALUES (?, ?, ?, ?)",
            (user_id, datetime.now(), summary_score, json_str)
        )
        self.conn.commit()
        print(f"💾 [DB] User({user_id}) 기록 저장 완료")

    def fetch_recent_records(self, limit=10, user_id=None):
        # 특정 유저의 기록만 가져오기 (없으면 전체 혹은 Guest)
        try:
            query = "SELECT id, timestamp, summary_score, detail_json FROM skin_records"
            params = []
            
            if user_id is not None:
                query += " WHERE user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor = self.conn.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                r_id, r_time, r_score, r_json = row
                try: details = json.loads(r_json)
                except: details = {}
                results.append({"id": r_id, "time": r_time, "score": r_score, "details": details})
            return results
        except Exception as e:
            print(f"DB 조회 에러: {e}")
            return []

    def insert_env_log(self, temp, hum, seated):
        self.conn.execute(
            "INSERT INTO env_logs (timestamp, temperature, humidity, is_seated) VALUES (?, ?, ?, ?)",
            (datetime.now(), temp, hum, 1 if seated else 0)
        )
        self.conn.commit()
        
    def close(self):
        self.conn.close()
