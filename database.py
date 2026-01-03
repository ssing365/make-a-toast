"""
데이터베이스 연결 및 CRUD 함수
PostgreSQL (Supabase) 지원
"""
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import openpyxl
import re
import streamlit as st

# PostgreSQL 연결 시도
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
except ImportError:
    USE_POSTGRES = False
    import sqlite3

def validate_connection(conn):
    try:
        # conn.closed가 0이면 연결이 열려있는 상태입니다.
        return conn.closed == 0
    except:
        return False

def clear_cache():
    """데이터 변경 시 캐시 무효화"""
    try:
        # 세션 상태에 캐시 버전 관리
        if 'db_cache_version' not in st.session_state:
            st.session_state.db_cache_version = 0
        st.session_state.db_cache_version += 1
        
        # 캐시 무효화
        get_all_participants.clear()
        get_all_sessions.clear()
        get_session_participants.clear()
        check_duplicate_meetings.clear()
        get_participant_detail.clear()
    except:
        pass

# validate 옵션을 추가합니다.
@st.cache_resource(ttl=3600, validate=validate_connection)
def get_connection():
    """DB 연결 - PostgreSQL 또는 SQLite"""
    if USE_POSTGRES:
        try:
            # Streamlit이 있는 경우 (배포 환경)
            import streamlit as st
            try:
                # DATABASE_URL이 있으면 사용
                db_url = st.secrets.get("DATABASE_URL")
                if db_url:
                    conn = psycopg2.connect(db_url)
                    return conn
            except:
                pass
            
            # 개별 정보로 구성
            supabase_url = st.secrets.get("SUPABASE_URL", "")
            supabase_password = st.secrets.get("SUPABASE_PASSWORD", "")
            
            if supabase_url and supabase_password:
                # URL에서 호스트 추출
                # https://liosvqxdsgamwypwhnri.supabase.co -> db.liosvqxdsgamwypwhnri.supabase.co
                host = supabase_url.replace("https://", "").replace("http://", "").replace(".supabase.co", "")
                db_url = f"postgresql://postgres:{supabase_password}@db.{host}.supabase.co:5432/postgres"
                conn = psycopg2.connect(db_url)
                return conn
        except Exception as e:
            # 로컬 개발 시 환경 변수 사용
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                return conn
            raise Exception(f"PostgreSQL 연결 실패: {e}")
    else:
        # SQLite fallback (로컬 개발용)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_NAME = os.path.join(BASE_DIR, "maketoast.db")
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    """커서 생성 (PostgreSQL은 RealDictCursor 사용)"""
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        return cursor

def init_db():
    """DB 초기화 - 테이블 생성 (이미 Supabase에서 생성했다면 스킵)"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        if USE_POSTGRES:
            # PostgreSQL: 테이블이 이미 있으면 스킵 (Supabase에서 이미 생성했을 수 있음)
            # CREATE TABLE IF NOT EXISTS는 PostgreSQL에서도 작동
            queries = [
                """
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
                """,
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id SERIAL PRIMARY KEY,
                    session_date TEXT NOT NULL,
                    session_time TEXT,
                    theme TEXT,
                    host TEXT,
                    status TEXT DEFAULT '준비중'
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id SERIAL PRIMARY KEY,
                    participant_name TEXT NOT NULL,
                    participant_birth TEXT NOT NULL,
                    session_id INTEGER NOT NULL,
                    attended BOOLEAN DEFAULT TRUE,
                    payment_status TEXT,
                    FOREIGN KEY (participant_name, participant_birth) 
                        REFERENCES participants(name, birth_date),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
                """
            ]
            
            for query in queries:
                cursor.execute(query)
            conn.commit()
            print("✅ DB 초기화 완료! (PostgreSQL)")
        else:
            # SQLite
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date TEXT NOT NULL,
                    session_time TEXT,
                    theme TEXT,
                    host TEXT,
                    status TEXT DEFAULT '준비중'
                )
            """)
            
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
            print("✅ DB 초기화 완료! (SQLite)")
    except Exception as e:
        conn.rollback()
        print(f"⚠️ DB 초기화 중 오류 (테이블이 이미 존재할 수 있음): {e}")
    finally:
        pass #conn.close()()

def add_participant(name: str, birth_date: str, gender: str, 
                   job: str = "", mbti: str = "", phone: str = "", 
                   location: str = "", signup_route: str = "", memo: str = ""):
    """참가자 추가"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO participants 
                (name, birth_date, gender, job, mbti, phone, location, signup_route, first_visit_date, memo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name, birth_date) DO NOTHING
            """, (name, birth_date, gender, job, mbti, phone, location, signup_route, 
                  datetime.now().strftime("%Y-%m-%d"), memo))
        else:
            cursor.execute("""
                INSERT INTO participants 
                (name, birth_date, gender, job, mbti, phone, location, signup_route, first_visit_date, memo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, birth_date, gender, job, mbti, phone, location, signup_route, 
                  datetime.now().strftime("%Y-%m-%d"), memo))
        
        conn.commit()
        clear_cache()
        print(f"✅ {name} 추가 완료!")
        return True
    except Exception as e:
        conn.rollback()
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            print(f"❌ {name} ({birth_date})는 이미 존재합니다.")
        else:
            print(f"❌ 오류: {e}")
        return False
    finally:
        pass #conn.close()()

def create_session(session_date, session_time, theme, host=""):
    """회차 생성"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO sessions 
                (session_date, session_time, theme, host)
                VALUES (%s, %s, %s, %s)
                RETURNING session_id
            """, (session_date, session_time, theme, host))
            session_id = cursor.fetchone()['session_id']
        else:
            cursor.execute("""
                INSERT INTO sessions 
                (session_date, session_time, theme, host)
                VALUES (?, ?, ?, ?)
            """, (session_date, session_time, theme, host))
            session_id = cursor.lastrowid
        
        conn.commit()
        clear_cache()
        print(f"✅ 회차 생성 완료! (날짜: {session_date}, ID: {session_id})")
        return session_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pass #conn.close()()

def add_attendance(session_id: int, participant_name: str, participant_birth: str):
    """회차에 참가자 추가"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO attendance (session_id, participant_name, participant_birth)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (session_id, participant_name, participant_birth))
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO attendance (session_id, participant_name, participant_birth)
                VALUES (?, ?, ?)
            """, (session_id, participant_name, participant_birth))
        
        conn.commit()
        clear_cache()
        print(f"✅ {participant_name} -> {session_id}회차 추가!")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pass #conn.close()()

@st.cache_data(ttl=10, show_spinner=False)
def get_all_participants(_cache_version: int = 0) -> List[Dict]:
    """모든 참가자 조회"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    cursor.execute("""
        SELECT name, birth_date, gender, job, mbti, phone, location, signup_route, first_visit_date, memo
        FROM participants
        ORDER BY name
    """)
    
    rows = cursor.fetchall()
    pass #conn.close()()
    
    return [dict(row) for row in rows]

@st.cache_data(ttl=10, show_spinner=False)
def get_all_sessions(_cache_version: int = 0) -> List[Dict]:
    """모든 회차 조회 (날짜순 정렬)"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    cursor.execute("""
        SELECT session_id, session_date, session_time, 
               theme, host, status
        FROM sessions
        ORDER BY session_date DESC, session_time DESC
    """)
    
    rows = cursor.fetchall()
    pass #conn.close()()
    
    return [dict(row) for row in rows]

@st.cache_data(ttl=10, show_spinner=False)
def get_session_participants(session_id: int, _cache_version: int = 0) -> List[Dict]:
    """특정 회차의 참가자 목록"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    if USE_POSTGRES:
        cursor.execute("""
            SELECT p.name, p.birth_date, p.gender, p.job, p.mbti, p.phone,
                   p.location, p.signup_route, a.attendance_id, a.payment_status
            FROM attendance a
            JOIN participants p ON a.participant_name = p.name 
                                AND a.participant_birth = p.birth_date
            WHERE a.session_id = %s
        """, (session_id,))
    else:
        cursor.execute("""
            SELECT p.name, p.birth_date, p.gender, p.job, p.mbti, p.phone,
                   p.location, p.signup_route, a.attendance_id, a.payment_status
            FROM attendance a
            JOIN participants p ON a.participant_name = p.name 
                                AND a.participant_birth = p.birth_date
            WHERE a.session_id = ?
        """, (session_id,))
    
    rows = cursor.fetchall()
    pass #conn.close()()
    
    return [dict(row) for row in rows]

@st.cache_data(ttl=10, show_spinner=False)
def check_duplicate_meetings(session_id: int, _cache_version: int = 0) -> List[Dict]:
    """
    현재 회차 참가자들 중 과거에 만난 적 있는 사람들 찾기
    반환: [{'person1': '김철수', 'person1_birth': '1992', 
           'person2': '이영희', 'person2_birth': '1994',
           'session_dates': ['2024-11-15', '2024-12-01']}]
    """
    conn = get_connection()
    cursor = get_cursor(conn)
    
    # 현재 회차 참가자들
    current_participants = get_session_participants(session_id, st.session_state.get('db_cache_version', 0))
    
    duplicates = []
    
    # 모든 조합 체크 (i < j로 중복 방지)
    for i in range(len(current_participants)):
        for j in range(i + 1, len(current_participants)):
            p1_name = current_participants[i]['name']
            p1_birth = current_participants[i]['birth_date']
            p2_name = current_participants[j]['name']
            p2_birth = current_participants[j]['birth_date']
            
            # 두 사람이 함께 참가했던 회차 찾기
            if USE_POSTGRES:
                cursor.execute("""
                    SELECT DISTINCT s.session_date
                    FROM attendance a1
                    JOIN attendance a2 ON a1.session_id = a2.session_id
                    JOIN sessions s ON a1.session_id = s.session_id
                    WHERE a1.participant_name = %s AND a1.participant_birth = %s
                      AND a2.participant_name = %s AND a2.participant_birth = %s
                      AND a1.session_id != %s
                """, (p1_name, p1_birth, p2_name, p2_birth, session_id))
                met_dates = [row['session_date'] for row in cursor.fetchall()]
            else:
                cursor.execute("""
                    SELECT DISTINCT s.session_date
                    FROM attendance a1
                    JOIN attendance a2 ON a1.session_id = a2.session_id
                    JOIN sessions s ON a1.session_id = s.session_id
                    WHERE a1.participant_name = ? AND a1.participant_birth = ?
                      AND a2.participant_name = ? AND a2.participant_birth = ?
                      AND a1.session_id != ?
                """, (p1_name, p1_birth, p2_name, p2_birth, session_id))
                met_dates = [row[0] for row in cursor.fetchall()]
            
            if met_dates:
                duplicates.append({
                    'person1': p1_name,
                    'person1_birth': p1_birth,
                    'person2': p2_name,
                    'person2_birth': p2_birth,
                    'session_dates': met_dates
                })
    
    pass #conn.close()()
    return duplicates

@st.cache_data(ttl=10, show_spinner=False)
def get_participant_detail(name: str, birth_date: str, _cache_version: int = 0) -> Dict:
    """참가자 상세 정보 (매칭 이력 포함)"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    # 기본 정보
    if USE_POSTGRES:
        cursor.execute("""
            SELECT * FROM participants
            WHERE name = %s AND birth_date = %s
        """, (name, birth_date))
    else:
        cursor.execute("""
            SELECT * FROM participants
            WHERE name = ? AND birth_date = ?
        """, (name, birth_date))
    
    row = cursor.fetchone()
    if not row:
        pass #conn.close()()
        return {}
    
    participant = dict(row)
    
    # 참가 이력
    if USE_POSTGRES:
        cursor.execute("""
            SELECT s.session_id, s.session_date, s.session_time, s.theme
            FROM attendance a
            JOIN sessions s ON a.session_id = s.session_id
            WHERE a.participant_name = %s AND a.participant_birth = %s
            ORDER BY s.session_date DESC
        """, (name, birth_date))
    else:
        cursor.execute("""
            SELECT s.session_id, s.session_date, s.session_time, s.theme
            FROM attendance a
            JOIN sessions s ON a.session_id = s.session_id
            WHERE a.participant_name = ? AND a.participant_birth = ?
            ORDER BY s.session_date DESC
        """, (name, birth_date))
    
    participant['visit_history'] = [dict(row) for row in cursor.fetchall()]
    participant['visit_count'] = len(participant['visit_history'])
    
    # 각 회차에서 만난 사람들
    for visit in participant['visit_history']:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT p.name, p.gender
                FROM attendance a
                JOIN sessions s ON a.session_id = s.session_id
                JOIN participants p ON a.participant_name = p.name 
                                    AND a.participant_birth = p.birth_date
                WHERE s.session_id = %s
                  AND NOT (p.name = %s AND p.birth_date = %s)
            """, (visit['session_id'], name, birth_date))
        else:
            cursor.execute("""
                SELECT p.name, p.gender
                FROM attendance a
                JOIN sessions s ON a.session_id = s.session_id
                JOIN participants p ON a.participant_name = p.name 
                                    AND a.participant_birth = p.birth_date
                WHERE s.session_id = ?
                  AND NOT (p.name = ? AND p.birth_date = ?)
            """, (visit['session_id'], name, birth_date))
        
        visit['met_people'] = [dict(row) for row in cursor.fetchall()]
    
    pass #conn.close()()
    return participant

def get_recommendations(session_id: int, gender: str, 
                       age_min: int = None, age_max: int = None,
                       mbti: str = None) -> List[Dict]:
    """추천 참가자 목록 (현재 회차 참가자들과 안 만난 사람)"""
    from datetime import datetime
    
    conn = get_connection()
    cursor = get_cursor(conn)
    
    # 현재 회차 참가자들 (캐시 무시하고 직접 조회)
    if USE_POSTGRES:
        cursor.execute("""
            SELECT p.name, p.birth_date, p.gender, p.job, p.mbti, p.phone,
                   p.location, p.signup_route, a.attendance_id, a.payment_status
            FROM attendance a
            JOIN participants p ON a.participant_name = p.name 
                                AND a.participant_birth = p.birth_date
            WHERE a.session_id = %s
        """, (session_id,))
    else:
        cursor.execute("""
            SELECT p.name, p.birth_date, p.gender, p.job, p.mbti, p.phone,
                   p.location, p.signup_route, a.attendance_id, a.payment_status
            FROM attendance a
            JOIN participants p ON a.participant_name = p.name 
                                AND a.participant_birth = p.birth_date
            WHERE a.session_id = ?
        """, (session_id,))
    
    current_participants = [dict(row) for row in cursor.fetchall()]
    current_names_births = [(p['name'], p['birth_date']) for p in current_participants]
    
    # 필터 조건 구성
    if USE_POSTGRES:
        query = "SELECT * FROM participants WHERE gender = %s"
        params = [gender]
        
        if age_min or age_max:
            current_year = datetime.now().year
            if age_min:
                birth_year_max = current_year - age_min
                query += " AND CAST(SUBSTRING(birth_date, 1, 4) AS INTEGER) <= %s"
                params.append(birth_year_max)
            if age_max:
                birth_year_min = current_year - age_max
                query += " AND CAST(SUBSTRING(birth_date, 1, 4) AS INTEGER) >= %s"
                params.append(birth_year_min)
        
        if mbti:
            query += " AND mbti LIKE %s"
            params.append(f"%{mbti}%")
    else:
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
            query += " AND mbti LIKE ?"
            params.append(f"%{mbti}%")
    
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
            if USE_POSTGRES:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM attendance a1
                    JOIN attendance a2 ON a1.session_id = a2.session_id
                    WHERE a1.participant_name = %s AND a1.participant_birth = %s
                      AND a2.participant_name = %s AND a2.participant_birth = %s
                """, (c_name, c_birth, p_name, p_birth))
                row = cursor.fetchone()
                count = row['count'] if row else 0
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM attendance a1
                    JOIN attendance a2 ON a1.session_id = a2.session_id
                    WHERE a1.participant_name = ? AND a1.participant_birth = ?
                      AND a2.participant_name = ? AND a2.participant_birth = ?
                """, (c_name, c_birth, p_name, p_birth))
                row = cursor.fetchone()
                count = row[0] if row else 0
            
            if count > 0:
                has_met = True
                break
        
        if not has_met:
            # 방문 횟수와 최근 방문일 추가
            if USE_POSTGRES:
                cursor.execute("""
                    SELECT COUNT(*) as visit_count, MAX(s.session_date) as last_visit
                    FROM attendance a
                    JOIN sessions s ON a.session_id = s.session_id
                    WHERE a.participant_name = %s AND a.participant_birth = %s
                """, (c_name, c_birth))
                row = cursor.fetchone()
                visit_count = row['visit_count'] if row else 0
                last_visit = row['last_visit'] if row else None
            else:
                cursor.execute("""
                    SELECT COUNT(*), MAX(s.session_date)
                    FROM attendance a
                    JOIN sessions s ON a.session_id = s.session_id
                    WHERE a.participant_name = ? AND a.participant_birth = ?
                """, (c_name, c_birth))
                row = cursor.fetchone()
                visit_count = row[0] if row else 0
                last_visit = row[1] if row else None
            
            candidate['visit_count'] = visit_count
            candidate['last_visit'] = last_visit
            
            recommendations.append(candidate)
    
    pass #conn.close()()
    return recommendations

def update_participant_memo(name: str, birth_date: str, memo: str):
    """참가자 메모 업데이트"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    if USE_POSTGRES:
        cursor.execute("""
            UPDATE participants
            SET memo = %s
            WHERE name = %s AND birth_date = %s
        """, (memo, name, birth_date))
    else:
        cursor.execute("""
            UPDATE participants
            SET memo = ?
            WHERE name = ? AND birth_date = ?
        """, (memo, name, birth_date))
    
    conn.commit()
    clear_cache()
    pass #conn.close()()

def delete_session(session_id: int):
    """회차 삭제 (참가 기록도 함께 삭제, 다른 회차 참가 이력 없는 참가자도 삭제)"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        # 먼저 이 회차에 참가한 참가자 목록 가져오기
        if USE_POSTGRES:
            cursor.execute("""
                SELECT DISTINCT participant_name, participant_birth
                FROM attendance
                WHERE session_id = %s
            """, (session_id,))
        else:
            cursor.execute("""
                SELECT DISTINCT participant_name, participant_birth
                FROM attendance
                WHERE session_id = ?
            """, (session_id,))
        
        participants_in_session = cursor.fetchall()
        
        # 참가 기록 먼저 삭제
        if USE_POSTGRES:
            cursor.execute("DELETE FROM attendance WHERE session_id = %s", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        else:
            cursor.execute("DELETE FROM attendance WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        # 다른 회차 참가 이력이 없는 참가자 삭제
        for participant in participants_in_session:
            if USE_POSTGRES:
                p_name = participant['participant_name']
                p_birth = participant['participant_birth']
                
                # 다른 회차 참가 이력 확인
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM attendance
                    WHERE participant_name = %s AND participant_birth = %s
                """, (p_name, p_birth))
                row = cursor.fetchone()
                count = row['count'] if row else 0
                
                # 참가 이력이 없으면 참가자 삭제
                if count == 0:
                    cursor.execute("""
                        DELETE FROM participants
                        WHERE name = %s AND birth_date = %s
                    """, (p_name, p_birth))
            else:
                p_name = participant[0]
                p_birth = participant[1]
                
                # 다른 회차 참가 이력 확인
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM attendance
                    WHERE participant_name = ? AND participant_birth = ?
                """, (p_name, p_birth))
                count = cursor.fetchone()[0]
                
                # 참가 이력이 없으면 참가자 삭제
                if count == 0:
                    cursor.execute("""
                        DELETE FROM participants
                        WHERE name = ? AND birth_date = ?
                    """, (p_name, p_birth))
        
        conn.commit()
        clear_cache()
        print(f"✅ {session_id}회차 삭제 완료!")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pass #conn.close()()

def remove_participant_from_session(session_id: int, participant_name: str, participant_birth: str):
    """특정 회차에서 참가자 제거"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    if USE_POSTGRES:
        cursor.execute("""
            DELETE FROM attendance 
            WHERE session_id = %s 
              AND participant_name = %s 
              AND participant_birth = %s
        """, (session_id, participant_name, participant_birth))
    else:
        cursor.execute("""
            DELETE FROM attendance 
            WHERE session_id = ? 
              AND participant_name = ? 
              AND participant_birth = ?
        """, (session_id, participant_name, participant_birth))
    
    conn.commit()
    clear_cache()
    pass #conn.close()()
    print(f"✅ {participant_name} 제거 완료!")

def delete_participant(participant_name: str, participant_birth: str):
    """참가자를 DB에서 완전히 삭제 (참가 기록도 함께 삭제)"""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    try:
        # 참가 기록 먼저 삭제
        if USE_POSTGRES:
            cursor.execute("""
                DELETE FROM attendance 
                WHERE participant_name = %s AND participant_birth = %s
            """, (participant_name, participant_birth))
            
            cursor.execute("""
                DELETE FROM participants 
                WHERE name = %s AND birth_date = %s
            """, (participant_name, participant_birth))
        else:
            cursor.execute("""
                DELETE FROM attendance 
                WHERE participant_name = ? AND participant_birth = ?
            """, (participant_name, participant_birth))
            
            cursor.execute("""
                DELETE FROM participants 
                WHERE name = ? AND birth_date = ?
            """, (participant_name, participant_birth))
        
        conn.commit()
        clear_cache()
        print(f"✅ {participant_name} 삭제 완료!")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pass #conn.close()()

def import_excel_file(file_path):
    """엑셀 파일에서 모든 시트를 읽어 회차별로 DB에 저장"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    total_participants = 0
    processed_sessions = 0
    
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        
        # "의 사본" 제거
        sheet_name_clean = sheet_name.replace("의 사본", "").strip()
        
        print(f"\n{'='*60}")
        print(f"처리중: {sheet_name_clean}")
        print(f"{'='*60}")
        
        # 1. 시트명에서 날짜 추출
        date_match = re.search(r'(\d{4})(\d{2})(\d{2})', sheet_name_clean)
        if not date_match:
            print(f"⚠️ 시트명에서 날짜를 찾을 수 없음, 스킵")
            continue
        
        year, month, day = date_match.groups()
        session_date = f"{year}-{month}-{day}"
        
        # 2. A1 셀에서 시간 추출
        a1_cell = sheet['A1'].value
        session_time = "미정"
        theme = "미정"
        
        if a1_cell:
            a1_str = str(a1_cell).strip()
            
            # 시간 추출 (예: "7:30PM", "7:30 PM")
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', a1_str, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                meridiem = time_match.group(3).upper()
                
                if meridiem == 'PM' and hour != 12:
                    hour += 12
                elif meridiem == 'AM' and hour == 12:
                    hour = 0
                
                session_time = f"{hour:02d}:{minute:02d}"
            
            # 주제 추출
            theme_match = re.search(r'-\s*(.+)$', a1_str)
            if theme_match:
                theme = theme_match.group(1).strip()
            else:
                theme = a1_str
        
        # 3. N2 셀에서 HOST 추출
        n2_cell = sheet['N2'].value
        host = str(n2_cell).strip() if n2_cell else "미정"
        
        print(f"날짜: {session_date}")
        print(f"시간: {session_time}")
        print(f"주제: {theme}")
        print(f"HOST: {host}")
        
        # 4. 회차 생성
        try:
            session_id = create_session(
                session_date=session_date,
                session_time=session_time,
                theme=theme,
                host=host
            )
            processed_sessions += 1
        except Exception as e:
            print(f"❌ 회차 생성 실패: {e}")
            continue
        
        # 5. 참가자 데이터 읽기
        participant_count = 0
        skipped_count = 0
        
        for row_idx in range(2, sheet.max_row + 1):
            row = sheet[row_idx]
            
            try:
                gender = str(row[0].value).strip() if row[0].value else ""
                nickname = str(row[1].value).strip() if row[1].value else ""
                name = str(row[2].value).strip() if row[2].value else ""
                phone = str(row[3].value).strip() if row[3].value else ""
                location = str(row[6].value).strip() if row[6].value else ""
                birth_year = str(row[7].value).strip() if row[7].value else ""
                job = str(row[8].value).strip() if row[8].value else ""
                mbti = str(row[9].value).strip() if row[9].value else ""
                intro = str(row[10].value).strip() if row[10].value else ""
                signup_route = str(row[11].value).strip() if row[11].value else ""
            except IndexError:
                continue
            
            if not name or not birth_year or birth_year == "-":
                continue
            
            if gender in ['남', '남자', 'M', 'm', 'male', '男']:
                gender = 'M'
            elif gender in ['여', '여자', 'F', 'f', 'female', '女']:
                gender = 'F'
            else:
                skipped_count += 1
                continue
            
            birth_year_clean = re.sub(r'\D', '', birth_year)
            
            if len(birth_year_clean) != 4:
                skipped_count += 1
                continue
            
            birth_date = f"{birth_year_clean}-01-01"
            
            phone_clean = ""
            if phone and phone != "-":
                phone_clean = re.sub(r'\D', '', phone)
            
            conn = get_connection()
            cursor = get_cursor(conn)
            
            try:
                if USE_POSTGRES:
                    cursor.execute("""
                        INSERT INTO participants 
                        (name, birth_date, gender, nickname, phone, location, job, mbti, 
                         intro, signup_route, first_visit_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name, birth_date) DO NOTHING
                    """, (name, birth_date, gender, nickname, phone_clean, location, job, mbti,
                          intro, signup_route, session_date))
                    
                    cursor.execute("""
                        INSERT INTO attendance 
                        (session_id, participant_name, participant_birth)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (session_id, name, birth_date))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO participants 
                        (name, birth_date, gender, nickname, phone, location, job, mbti, 
                         intro, signup_route, first_visit_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (name, birth_date, gender, nickname, phone_clean, location, job, mbti,
                          intro, signup_route, session_date))
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO attendance 
                        (session_id, participant_name, participant_birth)
                        VALUES (?, ?, ?)
                    """, (session_id, name, birth_date))
                
                conn.commit()
                participant_count += 1
                
            except Exception as e:
                skipped_count += 1
                conn.rollback()
            finally:
                pass #conn.close()()
        
        print(f"✅ 참가자 {participant_count}명 추가 (스킵: {skipped_count}명)")
        total_participants += participant_count
    
    # 엑셀 임포트 완료 후 캐시 무효화
    clear_cache()
    
    print(f"\n{'='*60}")
    print(f"🎉 전체 임포트 완료!")
    print(f"총 {processed_sessions}개 회차, {total_participants}명 참가자")
    print(f"{'='*60}")
