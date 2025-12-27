import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import openpyxl
import re

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
    
    # 참가자 마스터 테이블
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
    
    # 회차 정보 테이블 (session_number 제거)
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

def create_session(session_date, session_time, theme, host=""):
    """회차 생성 (session_number 제거)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions 
        (session_date, session_time, theme, host)
        VALUES (?, ?, ?, ?)
    """, (session_date, session_time, theme, host))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ 회차 생성 완료! (날짜: {session_date}, ID: {session_id})")
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
    """모든 회차 조회 (날짜순 정렬)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, session_date, session_time, 
               theme, host, status
        FROM sessions
        ORDER BY session_date DESC, session_time DESC
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
    반환: [{'person1': '김철수', 'person1_birth': '1992', 
           'person2': '이영희', 'person2_birth': '1994',
           'session_dates': ['2024-11-15', '2024-12-01']}]
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
                    'session_dates': met_dates  # 이 부분 수정!
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

def delete_participant(participant_name: str, participant_birth: str):
    """참가자를 DB에서 완전히 삭제 (참가 기록도 함께 삭제)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 참가 기록 먼저 삭제
    cursor.execute("""
        DELETE FROM attendance 
        WHERE participant_name = ? AND participant_birth = ?
    """, (participant_name, participant_birth))
    
    # 참가자 삭제
    cursor.execute("""
        DELETE FROM participants 
        WHERE name = ? AND birth_date = ?
    """, (participant_name, participant_birth))
    
    conn.commit()
    conn.close()
    print(f"✅ {participant_name} 삭제 완료!")

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
        
        # 2. 시트명에서 시간 추출
        time_match = re.search(r'(\d+)\s*(am|pm)', sheet_name_clean, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            meridiem = time_match.group(2).lower()
            if meridiem == 'pm' and hour != 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
            session_time = f"{hour:02d}:00"
        else:
            session_time = "미정"
        
        # 3. A1 셀에서 주제 추출
        a1_cell = sheet['A1'].value
        theme = "미정"
        if a1_cell:
            a1_str = str(a1_cell).strip()
            theme_match = re.search(r'-\s*(.+)$', a1_str)
            if theme_match:
                theme = theme_match.group(1).strip()
            else:
                theme = a1_str
        
        # 4. N2 셀에서 HOST 추출
        n2_cell = sheet['N2'].value
        host = str(n2_cell).strip() if n2_cell else "미정"
        
        print(f"날짜: {session_date}")
        print(f"시간: {session_time}")
        print(f"주제: {theme}")
        print(f"HOST: {host}")
        
        # 5. 회차 생성
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
        
        # 6. 참가자 데이터 읽기 (동일)
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
            cursor = conn.cursor()
            
            try:
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
            finally:
                conn.close()
        
        print(f"✅ 참가자 {participant_count}명 추가 (스킵: {skipped_count}명)")
        total_participants += participant_count
    
    print(f"\n{'='*60}")
    print(f"🎉 전체 임포트 완료!")
    print(f"총 {processed_sessions}개 회차, {total_participants}명 참가자")
    print(f"{'='*60}")