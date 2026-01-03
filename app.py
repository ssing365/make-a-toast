"""메이크어토스트 - Streamlit 웹 애플리케이션"""
import streamlit as st
import database as db
from datetime import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="Make a Toast",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

# 캐시 버전 초기화
if 'db_cache_version' not in st.session_state:
    st.session_state.db_cache_version = 0

def main():
    """메인 애플리케이션"""
    st.title("🍞 Make a Toast")
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["회차 관리", "참가자 DB", "추천"])
    
    with tab1:
        render_session_tab()
    
    with tab2:
        render_participant_tab()
    
    with tab3:
        render_recommend_tab()

def render_session_tab():
    """회차 관리 탭"""
    st.header("회차 관리")
    
    # 상단: 회차 선택 및 액션 버튼
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    sessions = db.get_all_sessions(st.session_state.db_cache_version)
    session_options = [f"{s['session_date']} {s['session_time']} - {s['theme']}" 
                      for s in sessions]
    
    with col1:
        if session_options:
            selected_idx = st.selectbox(
                "회차 선택",
                range(len(session_options)),
                format_func=lambda x: session_options[x],
                key="session_select"
            )
            if selected_idx is not None:
                st.session_state.current_session_id = sessions[selected_idx]['session_id']
        else:
            st.selectbox("회차 선택", ["회차가 없습니다"], disabled=True)
            st.session_state.current_session_id = None
    
    with col2:
        if st.button("새 회차 생성", key="create_session_btn", width="stretch"):
            st.session_state.show_create_session = True
    
    with col3:
        if st.button("회차 삭제", key="delete_session_btn", width="stretch", type="secondary"):
            if st.session_state.current_session_id:
                st.session_state.show_delete_session = True
            else:
                st.warning("삭제할 회차를 선택해주세요!")
    
    with col4:
        if st.button("엑셀 임포트", key="import_excel_btn", width="stretch"):
            st.session_state.show_import_excel = True
    
    with col5:
        if st.button("새로고침", key="refresh_session_btn", width="stretch"):
            st.rerun()
    
    # 새 회차 생성 다이얼로그
    if st.session_state.get('show_create_session', False):
        with st.expander("새 회차 생성", expanded=True):
            with st.form("create_session_form"):
                session_date = st.date_input("날짜")
                session_time = st.text_input("시간대", value="")
                theme = st.selectbox(
                    "주제",
                    ['운동 좋아하는 사람들', 'MBTI I들의 모임', 'MBTI E들의 모임', '결혼', '기타']
                )
                host = st.text_input("HOST", value="")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("생성", key="create_session_submit", width="stretch"):
                        try:
                            session_id = db.create_session(
                                session_date.strftime("%Y-%m-%d"),
                                session_time,
                                theme,
                                host
                            )
                            st.success("회차가 생성되었습니다!")
                            st.session_state.show_create_session = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"회차 생성 실패: {e}")
                
                with col2:
                    if st.form_submit_button("취소", key="cancel_create_session_form", width="stretch"):
                        st.session_state.show_create_session = False
                        st.rerun()
    
    # 회차 삭제 확인
    if st.session_state.get('show_delete_session', False):
        current_session = next(
            (s for s in sessions if s['session_id'] == st.session_state.current_session_id), 
            None
        )
        if current_session:
            st.warning(f"⚠️ 이 회차를 삭제하시겠습니까?\n\n"
                      f"**날짜:** {current_session['session_date']}\n"
                      f"**주제:** {current_session['theme']}\n\n"
                      f"⚠️ 이 회차의 참가 기록도 모두 삭제됩니다!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("삭제 확인", type="primary", width="stretch"):
                    try:
                        db.delete_session(st.session_state.current_session_id)
                        st.success("회차가 삭제되었습니다.")
                        st.session_state.current_session_id = None
                        st.session_state.show_delete_session = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"회차 삭제 실패: {e}")
            
            with col2:
                if st.button("취소", key="cancel_delete_session", width="stretch"):
                    st.session_state.show_delete_session = False
                    st.rerun()
    
    # 엑셀 임포트
    if st.session_state.get('show_import_excel', False):
        with st.expander("엑셀 파일 임포트", expanded=True):
            uploaded_file = st.file_uploader(
                "엑셀 파일 선택",
                type=['xlsx', 'xls'],
                key="excel_upload"
            )
            
            if uploaded_file:
                if st.button("임포트 실행", type="primary"):
                    try:
                        # 임시 파일로 저장
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_path = tmp_file.name
                        
                        db.import_excel_file(tmp_path)
                        os.unlink(tmp_path)
                        
                        st.success("엑셀 임포트가 완료되었습니다!")
                        st.session_state.show_import_excel = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"임포트 실패:\n{e}")
            
            if st.button("취소", key="cancel_import_excel"):
                st.session_state.show_import_excel = False
                st.rerun()
    
    # 회차 정보 표시
    if st.session_state.current_session_id:
        current_session = next(
            (s for s in sessions if s['session_id'] == st.session_state.current_session_id),
            None
        )
        
        if current_session:
            st.info(f"📅 **{current_session['session_date']}** {current_session['session_time']} | "
                   f"주제: **{current_session['theme']}** | "
                   f"HOST: **{current_session['host']}**")
            
            # 참가자 목록 (남녀 분리)
            participants = db.get_session_participants(st.session_state.current_session_id, st.session_state.db_cache_version)
            
            male_participants = [p for p in participants if p['gender'] == 'M']
            female_participants = [p for p in participants if p['gender'] == 'F']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"남자 참가자 ({len(male_participants)}명)")
                
                if male_participants:
                    male_data = []
                    for p in male_participants:
                        birth_year = p['birth_date'][:4]
                        detail = db.get_participant_detail(p['name'], p['birth_date'], st.session_state.db_cache_version)
                        memo_indicator = "▲" if detail.get('memo') else ""
                        male_data.append({
                            '이름': f"{p['name']}{memo_indicator}",
                            '출생년도': birth_year,
                            '직업': p['job'] or '',
                            'MBTI': p['mbti'] or '',
                            '전화번호': p['phone'] or '',
                            '사는곳': p['location'] or '',
                            '등록경로': p['signup_route'] or '',
                            '_name': p['name'],
                            '_birth': p['birth_date']
                        })
                    
                    df_male = pd.DataFrame(male_data)
                    display_df_male = df_male.drop(columns=['_name', '_birth'])
                    
                    selected_male = st.dataframe(
                        display_df_male,
                        width="stretch",
                        height=400,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    if selected_male.selection.rows:
                        selected_row = df_male.iloc[selected_male.selection.rows[0]]
                        st.session_state.selected_participant = {
                            'name': selected_row['_name'],
                            'birth_date': selected_row['_birth'],
                            'gender': 'M'
                        }
                else:
                    st.info("참가자가 없습니다.")
                
                if st.button("남자 참가자 추가", key="add_male", width="stretch"):
                    st.session_state.show_add_participant = {'gender': 'M', 'session_id': st.session_state.current_session_id}
            
            with col2:
                st.subheader(f"여자 참가자 ({len(female_participants)}명)")
                
                if female_participants:
                    female_data = []
                    for p in female_participants:
                        birth_year = p['birth_date'][:4]
                        detail = db.get_participant_detail(p['name'], p['birth_date'], st.session_state.db_cache_version)
                        memo_indicator = "▲" if detail.get('memo') else ""
                        female_data.append({
                            '이름': f"{p['name']}{memo_indicator}",
                            '출생년도': birth_year,
                            '직업': p['job'] or '',
                            'MBTI': p['mbti'] or '',
                            '전화번호': p['phone'] or '',
                            '사는곳': p['location'] or '',
                            '등록경로': p['signup_route'] or '',
                            '_name': p['name'],
                            '_birth': p['birth_date']
                        })
                    
                    df_female = pd.DataFrame(female_data)
                    display_df_female = df_female.drop(columns=['_name', '_birth'])
                    
                    selected_female = st.dataframe(
                        display_df_female,
                        width="stretch",
                        height=400,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    if selected_female.selection.rows:
                        selected_row = df_female.iloc[selected_female.selection.rows[0]]
                        st.session_state.selected_participant = {
                            'name': selected_row['_name'],
                            'birth_date': selected_row['_birth'],
                            'gender': 'F'
                        }
                else:
                    st.info("참가자가 없습니다.")
                
                if st.button("여자 참가자 추가", key="add_female", width="stretch"):
                    st.session_state.show_add_participant = {'gender': 'F', 'session_id': st.session_state.current_session_id}
            
            # 선택된 참가자 액션
            if st.session_state.get('selected_participant'):
                p = st.session_state.selected_participant
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("상세 정보 보기", key="session_detail_btn", width="stretch"):
                        st.session_state.show_participant_detail = p
                with col2:
                    if st.button("이 참가자 제거", key="session_remove_btn", width="stretch", type="secondary"):
                        st.session_state.show_remove_participant = p
            
            # 중복 체크 버튼
            st.markdown("---")
            if st.button("🔍 중복 체크", width="stretch", type="primary"):
                check_duplicates(st.session_state.current_session_id)
            
            # 참가자 추가 다이얼로그
            if st.session_state.get('show_add_participant'):
                add_participant_dialog(st.session_state.show_add_participant)
            
            # 참가자 제거 확인
            if st.session_state.get('show_remove_participant'):
                p = st.session_state.show_remove_participant
                st.warning(f"⚠️ {p['name']}님을 현재 회차에서 제거하시겠습니까?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("제거 확인", type="primary", width="stretch"):
                        try:
                            db.remove_participant_from_session(
                                st.session_state.current_session_id,
                                p['name'],
                                p['birth_date']
                            )
                            st.success("참가자가 제거되었습니다.")
                            st.session_state.show_remove_participant = None
                            st.session_state.selected_participant = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"제거 실패: {e}")
                with col2:
                    if st.button("취소", key="cancel_remove_participant", width="stretch"):
                        st.session_state.show_remove_participant = None
                        st.rerun()
            
            # 참가자 상세 정보
            if st.session_state.get('show_participant_detail'):
                show_participant_detail_dialog(st.session_state.show_participant_detail)
    else:
        st.info("회차를 선택해주세요.")

def add_participant_dialog(params):
    """참가자 추가 다이얼로그"""
    gender = params['gender']
    session_id = params['session_id']
    
    with st.expander(f"{'남자' if gender == 'M' else '여자'} 참가자 추가", expanded=True):
        with st.form("add_participant_form"):
            name = st.text_input("이름 *", key="add_name")
            birth_year = st.text_input("출생년도 (4자리) *", key="add_birth")
            job = st.text_input("직업", key="add_job")
            mbti = st.text_input("MBTI", key="add_mbti")
            phone = st.text_input("전화번호", key="add_phone")
            location = st.text_input("사는곳", key="add_location")
            signup_route = st.text_input("등록경로", key="add_signup")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("추가", key=f"add_participant_submit_{gender}", width="stretch"):
                    if not name or not birth_year:
                        st.error("이름과 출생년도는 필수입니다!")
                    elif not birth_year.isdigit() or len(birth_year) != 4:
                        st.error("출생년도는 4자리 숫자만 입력 가능합니다! (예: 2000)")
                    else:
                        try:
                            birth_date = f"{birth_year}-01-01"
                            db.add_participant(
                                name=name,
                                birth_date=birth_date,
                                gender=gender,
                                job=job,
                                mbti=mbti,
                                phone=phone,
                                location=location,
                                signup_route=signup_route,
                                memo=""
                            )
                            db.add_attendance(session_id, name, birth_date)
                            st.success("참가자가 추가되었습니다!")
                            st.session_state.show_add_participant = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"추가 실패: {e}")
            
            with col2:
                if st.form_submit_button("취소", key=f"cancel_add_participant_{gender}", width="stretch"):
                    st.session_state.show_add_participant = None
                    st.rerun()

def check_duplicates(session_id):
    """중복 체크 및 표시"""
    duplicates = db.check_duplicate_meetings(session_id, st.session_state.db_cache_version)
    
    if not duplicates:
        st.success("✅ 중복된 매칭이 없습니다!")
        return
    
    st.error("⚠️ 중복 매칭 발견!")
    
    for dup in duplicates:
        sessions_str = ', '.join(map(str, dup['session_dates']))
        st.warning(f"• **{dup['person1']}** ↔ **{dup['person2']}**\n"
                  f"  → {sessions_str}회차에서 만남")

def show_participant_detail_dialog(participant):
    """참가자 상세 정보 다이얼로그"""
    name = participant['name']
    birth_date = participant['birth_date']
    
    with st.expander(f"{name} 상세 정보", expanded=True):
        detail = db.get_participant_detail(name, birth_date, st.session_state.db_cache_version)
        
        birth_year = int(birth_date[:4])
        age = datetime.now().year - birth_year + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **기본 정보**
            - 이름: {detail['name']}
            - 성별: {detail['gender']}
            - 나이: {age}세 ({birth_year})
            - 직업: {detail['job'] or '미기입'}
            - MBTI: {detail['mbti'] or '미기입'}
            """)
        
        with col2:
            st.markdown(f"""
            **연락처 정보**
            - 전화번호: {detail['phone'] or '미기입'}
            - 사는곳: {detail['location'] or '미기입'}
            - 등록경로: {detail['signup_route'] or '미기입'}
            - 첫 방문: {detail['first_visit_date']}
            - 총 방문횟수: {detail['visit_count']}회
            """)
        
        st.markdown("**자기소개**")
        st.text(detail['intro'] or '-')
        
        st.markdown("**매칭 이력**")
        for visit in detail['visit_history']:
            with st.container():
                st.markdown(f"📅 **{visit['session_date']}** - {visit['theme']}")
                if visit['met_people']:
                    people = ', '.join([f"{p['name']}({p['gender']})" for p in visit['met_people']])
                    st.caption(f"만난 사람: {people}")
        
        st.markdown("**메모**")
        memo = st.text_area("메모", value=detail['memo'] or "", height=100, key=f"memo_{name}_{birth_date}")
        
        if st.button("메모 저장", key=f"save_memo_{name}_{birth_date}"):
            db.update_participant_memo(name, birth_date, memo)
            st.success("메모가 저장되었습니다!")
            st.rerun()
        
        if st.button("닫기", key=f"close_detail_{name}_{birth_date}"):
            st.session_state.show_participant_detail = None
            st.rerun()

def render_participant_tab():
    """참가자 DB 탭"""
    st.header("참가자 DB")
    
    # 검색 바
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("검색", key="participant_search", placeholder="이름 또는 직업으로 검색")
    with col2:
        if st.button("검색", key="participant_search_btn", width="stretch"):
            st.session_state.participant_search_term = search_term
    with col3:
        if st.button("전체 보기", width="stretch"):
            st.session_state.participant_search_term = None
            st.rerun()
    
    # 참가자 목록
    if st.session_state.get('participant_search_term'):
        # 검색 로직은 render에서 처리
        pass
    
    participants = db.get_all_participants(st.session_state.db_cache_version)
    
    # 검색 필터 적용
    if st.session_state.get('participant_search_term'):
        search_term = st.session_state.participant_search_term.lower()
        participants = [p for p in participants 
                       if search_term in p['name'].lower() or search_term in (p['job'] or '').lower()]
    
    male_participants = [p for p in participants if p['gender'] == 'M']
    female_participants = [p for p in participants if p['gender'] == 'F']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"남자 ({len(male_participants)}명)")
        if male_participants:
            male_data = []
            for p in male_participants:
                detail = db.get_participant_detail(p['name'], p['birth_date'])
                birth_year = p['birth_date'][:4]
                memo_indicator = "▲" if detail.get('memo') else ""
                male_data.append({
                    '이름': f"{p['name']}{memo_indicator}",
                    '출생년도': birth_year,
                    '직업': p['job'] or '',
                    'MBTI': p['mbti'] or '',
                    '전화번호': p['phone'] or '',
                    '사는곳': p['location'] or '',
                    '등록경로': p['signup_route'] or '',
                    '방문횟수': detail['visit_count'],
                    '_name': p['name'],
                    '_birth': p['birth_date']
                })
            
            df_male = pd.DataFrame(male_data)
            display_df_male = df_male.drop(columns=['_name', '_birth'])
            
            selected_male = st.dataframe(
                display_df_male,
                width="stretch",
                height=500,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if selected_male.selection.rows:
                selected_row = df_male.iloc[selected_male.selection.rows[0]]
                st.session_state.selected_participant_db = {
                    'name': selected_row['_name'],
                    'birth_date': selected_row['_birth']
                }
        else:
            st.info("참가자가 없습니다.")
    
    with col2:
        st.subheader(f"여자 ({len(female_participants)}명)")
        if female_participants:
            female_data = []
            for p in female_participants:
                detail = db.get_participant_detail(p['name'], p['birth_date'])
                birth_year = p['birth_date'][:4]
                memo_indicator = "▲" if detail.get('memo') else ""
                female_data.append({
                    '이름': f"{p['name']}{memo_indicator}",
                    '출생년도': birth_year,
                    '직업': p['job'] or '',
                    'MBTI': p['mbti'] or '',
                    '전화번호': p['phone'] or '',
                    '사는곳': p['location'] or '',
                    '등록경로': p['signup_route'] or '',
                    '방문횟수': detail['visit_count'],
                    '_name': p['name'],
                    '_birth': p['birth_date']
                })
            
            df_female = pd.DataFrame(female_data)
            display_df_female = df_female.drop(columns=['_name', '_birth'])
            
            selected_female = st.dataframe(
                display_df_female,
                width="stretch",
                height=500,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if selected_female.selection.rows:
                selected_row = df_female.iloc[selected_female.selection.rows[0]]
                st.session_state.selected_participant_db = {
                    'name': selected_row['_name'],
                    'birth_date': selected_row['_birth']
                }
        else:
            st.info("참가자가 없습니다.")
    
    # 선택된 참가자 액션
    if st.session_state.get('selected_participant_db'):
        p = st.session_state.selected_participant_db
        col1, col2 = st.columns(2)
        with col1:
            if st.button("상세 정보 보기", key="db_detail", width="stretch"):
                st.session_state.show_participant_detail = p
        with col2:
            if st.button("이 참가자 삭제", key="db_delete", width="stretch", type="secondary"):
                st.session_state.show_delete_participant_db = p
        
        # 참가자 삭제 확인
        if st.session_state.get('show_delete_participant_db'):
            p = st.session_state.show_delete_participant_db
            st.warning(f"⚠️ {p['name']}님을 데이터베이스에서 삭제하시겠습니까?\n(참가 기록도 함께 삭제됩니다)")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("삭제 확인", key="confirm_delete_db", type="primary", width="stretch"):
                    try:
                        db.delete_participant(p['name'], p['birth_date'])
                        st.success("참가자가 삭제되었습니다.")
                        st.session_state.show_delete_participant_db = None
                        st.session_state.selected_participant_db = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"삭제 실패: {e}")
            with col2:
                if st.button("취소", key="cancel_delete_db", width="stretch"):
                    st.session_state.show_delete_participant_db = None
                    st.rerun()
        
        # 상세 정보 표시
        if st.session_state.get('show_participant_detail'):
            show_participant_detail_dialog(st.session_state.show_participant_detail)

def render_recommend_tab():
    """추천 탭"""
    st.header("추천")
    
    # 필터 조건
    sessions = db.get_all_sessions(st.session_state.db_cache_version)
    session_options = [f"{s['session_date']} {s['session_time']} - {s['theme']}" 
                      for s in sessions]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if session_options:
            selected_idx = st.selectbox(
                "회차",
                range(len(session_options)),
                format_func=lambda x: session_options[x],
                key="recommend_session"
            )
            session_id = sessions[selected_idx]['session_id'] if selected_idx is not None else None
        else:
            st.selectbox("회차", ["회차가 없습니다"], disabled=True)
            session_id = None
    
    with col2:
        gender = st.radio("성별", ["M", "F"], horizontal=True, key="recommend_gender")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        birth_year_min = st.text_input("출생년도 (최소)", key="birth_min", placeholder="예: 1990")
    with col2:
        birth_year_max = st.text_input("출생년도 (최대)", key="birth_max", placeholder="예: 1995")
    with col3:
        mbti = st.text_input("MBTI", key="recommend_mbti", placeholder="예: ENFP")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("검색", key="recommend_search_btn", width="stretch"):
            if not session_id:
                st.warning("회차를 선택해주세요!")
            else:
                # 출생년도를 나이로 변환
                age_min = None
                age_max = None
                current_year = datetime.now().year
                
                try:
                    if birth_year_min:
                        age_max = current_year - int(birth_year_min)
                    if birth_year_max:
                        age_min = current_year - int(birth_year_max)
                except ValueError:
                    st.error("출생년도는 4자리 숫자로 입력해주세요!")
                    return
                
                mbti_val = mbti.strip().upper() or None
                
                recommendations = db.get_recommendations(session_id, gender, age_min, age_max, mbti_val)
                st.session_state.recommendations = recommendations
                st.session_state.recommend_sort = "last_visit"
    
    # 정렬 옵션
    if st.session_state.get('recommendations'):
        sort_option = st.radio(
            "정렬",
            ["최근 방문일순", "방문횟수순"],
            key="recommend_sort_radio",
            horizontal=True
        )
        
        recommendations = st.session_state.recommendations.copy()
        
        if sort_option == "최근 방문일순":
            recommendations.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        else:
            recommendations.sort(key=lambda x: x['visit_count'], reverse=True)
        
        # 추천 결과 표시
        if recommendations:
            recommend_data = []
            for p in recommendations:
                birth_year = p['birth_date'][:4]
                detail = db.get_participant_detail(p['name'], p['birth_date'])
                memo_indicator = "▲" if detail.get('memo') else ""
                recommend_data.append({
                    '이름': f"{p['name']}{memo_indicator}",
                    '출생년도': birth_year,
                    '직업': p['job'] or '',
                    'MBTI': p['mbti'] or '',
                    '전화번호': p['phone'] or '',
                    '사는곳': p['location'] or '',
                    '등록경로': p['signup_route'] or '',
                    '최근방문': p['last_visit'] or '-',
                    '방문횟수': p['visit_count'],
                    '_name': p['name'],
                    '_birth': p['birth_date']
                })
            
            df_recommend = pd.DataFrame(recommend_data)
            display_df_recommend = df_recommend.drop(columns=['_name', '_birth'])
            
            selected_recommend = st.dataframe(
                display_df_recommend,
                width="stretch",
                height=500,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if selected_recommend.selection.rows:
                selected_row = df_recommend.iloc[selected_recommend.selection.rows[0]]
                st.session_state.selected_recommend = {
                    'name': selected_row['_name'],
                    'birth_date': selected_row['_birth']
                }
            
            if st.session_state.get('selected_recommend'):
                if st.button("상세 정보 보기", key="recommend_detail", width="stretch"):
                    st.session_state.show_participant_detail = st.session_state.selected_recommend
                
                if st.session_state.get('show_participant_detail'):
                    show_participant_detail_dialog(st.session_state.show_participant_detail)
        else:
            st.info("조건에 맞는 추천 대상이 없습니다.")

if __name__ == "__main__":
    # 데이터베이스 초기화
    db.init_db()
    
    main()

