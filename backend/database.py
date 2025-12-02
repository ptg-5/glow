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
