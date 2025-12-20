import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import openpyxl
import re
from datetime import datetime

DB_NAME = "maketoast.db"

def get_connection():
    """DB 연결"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 딕셔너리처럼 접근 가능
    return conn

def init_db():
    """DB 초기화 - 테이블 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 참가자 마스터 테이블 (수정됨)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            nickname TEXT,
            phone TEXT,
            location TEXT,
            job TEXT,
            mbti TEXT,
            intro TEXT,
            signup_route TEXT,
            first_visit_date TEXT,
            memo TEXT,
            PRIMARY KEY (name, birth_date)
        )
    """)
    
    # 회차 정보 테이블 (수정)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_number INTEGER,
            session_date TEXT NOT NULL,
            session_time TEXT,
            theme TEXT,
            host TEXT,
            status TEXT DEFAULT '준비중'
        )
    """)
    
    # 참가 이력 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_name TEXT NOT NULL,
            participant_birth TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            attended BOOLEAN DEFAULT 1,
            payment_status TEXT,
            FOREIGN KEY (participant_name, participant_birth) 
                REFERENCES participants(name, birth_date),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ DB 초기화 완료!")

def add_participant(name: str, birth_date: str, gender: str, 
                   job: str = "", mbti: str = "", phone: str = "", memo: str = ""):
    """참가자 추가"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO participants 
            (name, birth_date, gender, job, mbti, phone, first_visit_date, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, birth_date, gender, job, mbti, phone, datetime.now().strftime("%Y-%m-%d"), memo))
        
        conn.commit()
        print(f"✅ {name} 추가 완료!")
        return True
    except sqlite3.IntegrityError:
        print(f"❌ {name} ({birth_date})는 이미 존재합니다.")
        return False
    finally:
        conn.close()

def create_session(session_number: int, session_date: str, session_time: str,
                  theme: str = "", target_age_range: str = ""):
    """회차 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions 
        (session_number, session_date, session_time, theme, target_age_range)
        VALUES (?, ?, ?, ?, ?)
    """, (session_number, session_date, session_time, theme, target_age_range))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ {session_number}회차 생성 완료! (ID: {session_id})")
    return session_id

def add_attendance(session_id: int, participant_name: str, participant_birth: str):
    """회차에 참가자 추가"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO attendance (session_id, participant_name, participant_birth)
        VALUES (?, ?, ?)
    """, (session_id, participant_name, participant_birth))
    
    conn.commit()
    conn.close()
    print(f"✅ {participant_name} -> {session_id}회차 추가!")

def insert_dummy_data():
    """테스트용 더미 데이터"""
    # 참가자 추가
    add_participant("김철수", "1992-03-15", "M", "개발자", "ENFP", "010-1234-5678")
    add_participant("이영희", "1994-07-20", "F", "디자이너", "INFJ", "010-2345-6789")
    add_participant("박민수", "1991-11-03", "M", "마케터", "ESTP", "010-3456-7890")
    add_participant("최지은", "1995-05-12", "F", "교사", "ISFJ", "010-4567-8901")
    add_participant("정다은", "1993-09-08", "F", "기획자", "ENFJ", "010-5678-9012")
    add_participant("한동훈", "1990-12-25", "M", "변호사", "INTJ", "010-6789-0123")
    
    # 회차 생성
    session1 = create_session(1, "2024-11-15", "금저", "운동 좋아하는 사람들", "28-35세")
    session2 = create_session(2, "2024-11-22", "토오전", "MBTI I들의 모임", "25-33세")
    
    # 1회차 참가자
    add_attendance(session1, "김철수", "1992-03-15")
    add_attendance(session1, "이영희", "1994-07-20")
    add_attendance(session1, "박민수", "1991-11-03")
    add_attendance(session1, "최지은", "1995-05-12")
    
    # 2회차 참가자 (김철수, 이영희 중복!)
    add_attendance(session2, "김철수", "1992-03-15")  # 중복!
    add_attendance(session2, "이영희", "1994-07-20")  # 중복!
    add_attendance(session2, "정다은", "1993-09-08")
    add_attendance(session2, "한동훈", "1990-12-25")

if __name__ == "__main__":
    init_db()
    
    # 더미 데이터 넣기 (최초 1회만 실행)
    response = input("더미 데이터를 넣을까요? (y/n): ")
    if response.lower() == 'y':
        insert_dummy_data()

def get_all_participants() -> List[Dict]:
    """모든 참가자 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, birth_date, gender, job, mbti, phone, first_visit_date, memo
        FROM participants
        ORDER BY name
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_all_sessions() -> List[Dict]:
    """모든 회차 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, session_number, session_date, session_time, 
               theme, target_age_range, status
        FROM sessions
        ORDER BY session_date DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_session_participants(session_id: int) -> List[Dict]:
    """특정 회차의 참가자 목록"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.name, p.birth_date, p.gender, p.job, p.mbti, p.phone,
               a.attendance_id, a.payment_status
        FROM attendance a
        JOIN participants p ON a.participant_name = p.name 
                            AND a.participant_birth = p.birth_date
        WHERE a.session_id = ?
    """, (session_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def check_duplicate_meetings(session_id: int) -> List[Dict]:
    """
    현재 회차 참가자들 중 과거에 만난 적 있는 사람들 찾기
    반환: [{'person1': '김철수', 'person1_birth': '1992-03-15', 
           'person2': '이영희', 'person2_birth': '1994-07-20',
           'met_sessions': [1, 3, 5]}]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 현재 회차 참가자들
    current_participants = get_session_participants(session_id)
    
    duplicates = []
    
    # 모든 조합 체크 (i < j로 중복 방지)
    for i in range(len(current_participants)):
        for j in range(i + 1, len(current_participants)):
            p1_name = current_participants[i]['name']
            p1_birth = current_participants[i]['birth_date']
            p2_name = current_participants[j]['name']
            p2_birth = current_participants[j]['birth_date']
            
            # 두 사람이 함께 참가했던 회차 찾기
            cursor.execute("""
                SELECT DISTINCT s.session_number
                FROM attendance a1
                JOIN attendance a2 ON a1.session_id = a2.session_id
                JOIN sessions s ON a1.session_id = s.session_id
                WHERE a1.participant_name = ? AND a1.participant_birth = ?
                  AND a2.participant_name = ? AND a2.participant_birth = ?
                  AND a1.session_id != ?
            """, (p1_name, p1_birth, p2_name, p2_birth, session_id))
            
            met_sessions = [row[0] for row in cursor.fetchall()]
            
            if met_sessions:
                duplicates.append({
                    'person1': p1_name,
                    'person1_birth': p1_birth,
                    'person2': p2_name,
                    'person2_birth': p2_birth,
                    'met_sessions': met_sessions
                })
    
    conn.close()
    return duplicates

def get_participant_detail(name: str, birth_date: str) -> Dict:
    """참가자 상세 정보 (매칭 이력 포함)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 기본 정보
    cursor.execute("""
        SELECT * FROM participants
        WHERE name = ? AND birth_date = ?
    """, (name, birth_date))
    
    participant = dict(cursor.fetchone())
    
    # 참가 이력
    cursor.execute("""
        SELECT s.session_number, s.session_date, s.theme
        FROM attendance a
        JOIN sessions s ON a.session_id = s.session_id
        WHERE a.participant_name = ? AND a.participant_birth = ?
        ORDER BY s.session_date DESC
    """, (name, birth_date))
    
    participant['visit_history'] = [dict(row) for row in cursor.fetchall()]
    participant['visit_count'] = len(participant['visit_history'])
    
    # 각 회차에서 만난 사람들
    for visit in participant['visit_history']:
        cursor.execute("""
            SELECT p.name, p.gender
            FROM attendance a
            JOIN sessions s ON a.session_id = s.session_id
            JOIN participants p ON a.participant_name = p.name 
                                AND a.participant_birth = p.birth_date
            WHERE s.session_number = ?
              AND NOT (p.name = ? AND p.birth_date = ?)
        """, (visit['session_number'], name, birth_date))
        
        visit['met_people'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return participant

def get_recommendations(session_id: int, gender: str, 
                       age_min: int = None, age_max: int = None,
                       mbti: str = None) -> List[Dict]:
    """추천 참가자 목록 (현재 회차 참가자들과 안 만난 사람)"""
    from datetime import datetime
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 현재 회차 참가자들
    current_participants = get_session_participants(session_id)
    current_names_births = [(p['name'], p['birth_date']) for p in current_participants]
    
    # 필터 조건 구성
    query = "SELECT * FROM participants WHERE gender = ?"
    params = [gender]
    
    if age_min or age_max:
        current_year = datetime.now().year
        if age_min:
            birth_year_max = current_year - age_min
            query += " AND CAST(substr(birth_date, 1, 4) AS INTEGER) <= ?"
            params.append(birth_year_max)
        if age_max:
            birth_year_min = current_year - age_max
            query += " AND CAST(substr(birth_date, 1, 4) AS INTEGER) >= ?"
            params.append(birth_year_min)
    
    if mbti:
        query += " AND mbti = ?"
        params.append(mbti)
    
    cursor.execute(query, params)
    candidates = [dict(row) for row in cursor.fetchall()]
    
    # 현재 회차 참가자들과 한번이라도 만난 사람 제외
    recommendations = []
    
    for candidate in candidates:
        c_name = candidate['name']
        c_birth = candidate['birth_date']
        
        # 이미 현재 회차에 있는 사람 제외
        if (c_name, c_birth) in current_names_births:
            continue
        
        # 현재 회차 참가자들과 만난 적 있는지 체크
        has_met = False
        for p_name, p_birth in current_names_births:
            cursor.execute("""
                SELECT COUNT(*) FROM attendance a1
                JOIN attendance a2 ON a1.session_id = a2.session_id
                WHERE a1.participant_name = ? AND a1.participant_birth = ?
                  AND a2.participant_name = ? AND a2.participant_birth = ?
            """, (c_name, c_birth, p_name, p_birth))
            
            if cursor.fetchone()[0] > 0:
                has_met = True
                break
        
        if not has_met:
            # 방문 횟수와 최근 방문일 추가
            cursor.execute("""
                SELECT COUNT(*), MAX(s.session_date)
                FROM attendance a
                JOIN sessions s ON a.session_id = s.session_id
                WHERE a.participant_name = ? AND a.participant_birth = ?
            """, (c_name, c_birth))
            
            visit_count, last_visit = cursor.fetchone()
            candidate['visit_count'] = visit_count
            candidate['last_visit'] = last_visit
            
            recommendations.append(candidate)
    
    conn.close()
    return recommendations

def update_participant_memo(name: str, birth_date: str, memo: str):
    """참가자 메모 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE participants
        SET memo = ?
        WHERE name = ? AND birth_date = ?
    """, (memo, name, birth_date))
    
    conn.commit()
    conn.close()

def delete_session(session_id: int):
    """회차 삭제 (참가 기록도 함께 삭제)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 참가 기록 먼저 삭제
    cursor.execute("DELETE FROM attendance WHERE session_id = ?", (session_id,))
    
    # 회차 삭제
    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    
    conn.commit()
    conn.close()
    print(f"✅ {session_id}회차 삭제 완료!")

def remove_participant_from_session(session_id: int, participant_name: str, participant_birth: str):
    """특정 회차에서 참가자 제거"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM attendance 
        WHERE session_id = ? 
          AND participant_name = ? 
          AND participant_birth = ?
    """, (session_id, participant_name, participant_birth))
    
    conn.commit()
    conn.close()
    print(f"✅ {participant_name} 제거 완료!")