import sqlite3
import json
from datetime import datetime

<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
class DBManager:
    def __init__(self, db_path="skin_care.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
<<<<<<< Updated upstream
        # 환경 로그 테이블
=======
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
>>>>>>> Stashed changes
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS env_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL,
                humidity REAL,
                is_seated INTEGER
            )
        """)
<<<<<<< Updated upstream

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

=======
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

>>>>>>> Stashed changes
    def insert_env_log(self, temp, hum, seated):
        self.conn.execute(
            "INSERT INTO env_logs (timestamp, temperature, humidity, is_seated) VALUES (?, ?, ?, ?)",
            (datetime.now(), temp, hum, 1 if seated else 0)
        )
        self.conn.commit()
<<<<<<< Updated upstream

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
        print(
            f"💾 [DB] 피부 진단 결과 저장 완료 (ID: {self.conn.execute('SELECT last_insert_rowid()').fetchone()[0]})")

    def close(self):
        self.conn.close()

    # ... (기존 __init__, create_tables, insert 등은 그대로 유지) ...

    # [Update] 1. 메모 수정하기 (가장 많이 쓸 기능)
    def update_skin_memo(self, record_id, new_memo):
        """
        특정 ID의 피부 진단 기록에 있는 메모를 수정합니다.
        record_id: 수정할 기록의 ID (int)
        new_memo: 새로운 메모 내용 (str)
        """
        try:
            self.conn.execute(
                "UPDATE skin_records SET memo = ? WHERE id = ?",
                (new_memo, record_id)
            )
            self.conn.commit()
            print(f"🔄 [DB] ID {record_id} 메모 수정 완료")
            return True
        except Exception as e:
            print(f"❌ [DB] 메모 수정 실패: {e}")
            return False

    # [Update] 2. 진단 결과 자체를 수정하기 (재진단 등으로 데이터가 바뀔 때)
    def update_skin_data(self, record_id, summary_score, detail_data):
        """
        특정 ID의 점수와 상세 데이터를 통째로 업데이트합니다.
        """
        try:
            json_str = json.dumps(detail_data, ensure_ascii=False)
            self.conn.execute(
                "UPDATE skin_records SET summary_score = ?, detail_json = ? WHERE id = ?",
                (summary_score, json_str, record_id)
            )
            self.conn.commit()
            print(f"🔄 [DB] ID {record_id} 데이터 업데이트 완료")
            return True
        except Exception as e:
            print(f"❌ [DB] 데이터 업데이트 실패: {e}")
            return False

    # [Delete] 특정 기록 삭제하기
    def delete_skin_record(self, record_id):
        """
        특정 ID의 피부 진단 기록을 삭제합니다.
        """
        try:
            self.conn.execute(
                "DELETE FROM skin_records WHERE id = ?",
                (record_id,)
            )
            self.conn.commit()
            print(f"🗑️ [DB] ID {record_id} 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ [DB] 삭제 실패: {e}")
            return False

    # [Delete] (선택사항) 모든 기록 초기화 - 개발 중에만 쓰는 게 좋아!
    def clear_all_records(self):
        """모든 피부 기록을 삭제합니다 (주의!)"""
        self.conn.execute("DELETE FROM skin_records")
        # ID 카운트도 1부터 다시 시작하게 초기화 (SQLite 특성)
        self.conn.execute(
            "DELETE FROM sqlite_sequence WHERE name='skin_records'")
        self.conn.commit()
        print("⚠️ [DB] 모든 피부 기록이 초기화되었습니다.")

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
                    "time": r_time,  # 문자열 그대로 사용 (YYYY-MM-DD HH:MM:SS.ssssss)
                    "score": r_score,
                    "details": details
                })
            return results
        except Exception as e:
            print(f"DB 조회 에러: {e}")
            return []
=======
        
    def close(self):
        self.conn.close()
>>>>>>> Stashed changes
