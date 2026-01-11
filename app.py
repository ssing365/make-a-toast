"""메이크어토스트 - Streamlit 웹 애플리케이션 (UI 복구 완료)"""
import streamlit as st
import database as db
from datetime import datetime
import pandas as pd
import tempfile
import os
import re
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

st.set_page_config(
    page_title="Make a Toast",
    page_icon="🍷",
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
    st.markdown("## 🍷 Make a Toast")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["회차 관리", "참가자 추천", "참가자 DB"])
    
    with tab1:
        render_session_tab()
    
    with tab2:
        render_recommend_tab()
    
    with tab3:
        render_participant_tab()

# ---------------------------------------------------------
# 1. 회차 관리 탭
# ---------------------------------------------------------
def render_session_tab():
    # 🎨 [CSS] 이제 복잡한 테이블 CSS는 다 버리고, 기본 여백만 조절합니다.
    st.markdown("""
    <style>
        /* 탭 폰트 */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }
        /* 셀렉트 박스 */
        div[data-baseweb="select"] > div {
            background-color: #fff0eb !important;
            border-color: #ffccbc !important;
        }
    </style>
    """, unsafe_allow_html=True)

    sessions = db.get_all_sessions()
    session_options = [f"📅 {s['session_date']} {s['session_time']} | 주제: {s['theme']} | {s['host']}" for s in sessions]

    # 회차 선택 레이아웃
    col_sel, col_add, col_del, col_imp = st.columns([7.2, 1.2, 1.2, 1.2])

    with col_sel:
        if session_options:
            selected_idx = st.selectbox(
                "회차 선택", range(len(session_options)),
                format_func=lambda x: session_options[x],
                key="session_select", label_visibility="collapsed",
            )
            if selected_idx is not None:
                st.session_state.current_session_id = sessions[selected_idx]['session_id']
        else:
            st.selectbox("회차 선택", ["회차가 없습니다"], disabled=True, label_visibility="collapsed")
            st.session_state.current_session_id = None
    
    with col_add:
        if st.button("회차 추가", use_container_width=True):
            create_session_dialog()
    with col_del:
        if st.button("회차 삭제", use_container_width=True):
            if st.session_state.current_session_id:
                delete_session_dialog(st.session_state.current_session_id, sessions)
            else:
                st.warning("선택무")
    with col_imp:
        if st.button("엑셀 넣기", use_container_width=True):
            import_excel_dialog()

    if st.session_state.current_session_id:
        render_current_session_info(sessions)

@st.dialog("새 회차 생성")
def create_session_dialog():
    with st.form("create_session_form"):
        session_date = st.date_input("날짜")
        session_time = st.text_input("시간대", value="19:30")
        
        theme = st.selectbox(
            "주제",
            [ '❤️결혼을 전제로❤️ 진지하고 섬세한 미팅', 
             '#오운완 ❤️운동하는남녀❤️를 위해 준비한 미팅 ', 
             '❤️MBTI-E❤️를 위해 준비한 아주 섬세한 미팅',
             '❤️MBTI-I❤️를 위해 준비한 아주 섬세한 미팅',
             '❤️MBTI-N❤️을 위해 준비한 아주 섬세한 미팅 ',
              '❤️MBTI-S❤️를 위해 준비한 아주 섬세한 미팅', '기타']
        )
        
        custom_theme = ""
        if theme == '기타':
            custom_theme = st.text_input("주제 직접 입력")

        host = st.text_input("HOST", value="")
        
        if st.form_submit_button("생성"):
            final_theme = custom_theme if theme == '기타' else theme
            try:
                db.create_session(session_date.strftime("%Y-%m-%d"), session_time, final_theme, host)
                st.success("회차가 생성되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"생성 실패: {e}")

@st.dialog("회차 삭제")
def delete_session_dialog(session_id, sessions):
    target = next((s for s in sessions if s['session_id'] == session_id), None)
    if target:
        st.warning(f"⚠️ 정말 삭제하시겠습니까?\n\n📅 {target['session_date']} - {target['theme']}\n\n(참가 기록도 모두 삭제됩니다)")
        if st.button("네, 삭제합니다", type="primary"):
            db.delete_session(session_id)
            st.success("삭제되었습니다.")
            st.session_state.current_session_id = None
            st.rerun()

@st.dialog("엑셀 임포트")
def import_excel_dialog():
    uploaded_file = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls'])
    if uploaded_file and st.button("임포트 실행", type="primary"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            
            with st.spinner("엑셀 데이터 분석 중..."):
                db.import_excel_file(tmp_path)
            
            os.unlink(tmp_path)
            st.success("완료되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

def render_participant_table(participants, gender_code):
    if not participants:
        st.info("참가자가 없습니다.")
        return

    # 데이터 가공
    data = []
    for p in participants:
        # 📝 메모가 있으면 이름 옆에 아이콘 표시
        memo_mark = " 📝" if p.get('memo') and str(p['memo']).strip() else ""
        
        data.append({
            '이름': f"{p['name']}{memo_mark}",
            '출생년도': p['birth_date'][:4],
            '직업': p['job'],
            'MBTI': p['mbti'],
            '지역': p['location'],
            '_full_data': p 
        })
    
    df = pd.DataFrame(data)

    event = st.dataframe(
        df.drop(columns=['_full_data']),
        use_container_width=True,
        height=300,
        hide_index=True, # 5. 참가자 테이블 컬럼 정리 (인덱스 숨김)
        selection_mode="single-row",
        on_select="rerun",
        key=f"table_{gender_code}"
    )

    if event.selection.rows:
        idx = event.selection.rows[0]
        selected = df.iloc[idx]['_full_data']
        # 선택된 참가자 액션 버튼
        c1, c2 = st.columns(2)
        if c1.button("상세 정보", key=f"det_{gender_code}_{idx}"):
            show_detail_dialog(selected['name'], selected['birth_date'])
        if c2.button("제거", key=f"rem_{gender_code}_{idx}"):
            remove_participant_dialog(selected, st.session_state.current_session_id)

def render_current_session_info(sessions):
    """현재 회차 정보 및 통합 참가자 테이블 (AgGrid 적용: 행 클릭 선택)"""
    curr = next((s for s in sessions if s['session_id'] == st.session_state.current_session_id), None)
    if not curr: return

    participants = db.get_session_participants(curr['session_id'])

    # 🔥 [추가] 성별 고정 정렬: 남자(M) 우선, 그 다음 이름순
    if participants:
        participants.sort(key=lambda x: (0 if x['gender'] == 'M' else 1, x['name']))

    act_c1, _, act_c2, _, act_c3 = st.columns([7.7, 0.1, 2, 0.1, 2])
    
    with act_c1:
        if st.button("🔍 중복 만남 체크", type="primary", use_container_width=True):
            check_duplicates(curr['session_id'])
    with act_c2:
        if st.button("➕ 남자 참가자 추가", use_container_width=True):
            add_participant_dialog('M', curr['session_id'])
    with act_c3:
        if st.button("➕ 여자 참가자 추가", use_container_width=True):
            add_participant_dialog('F', curr['session_id'])

    # ---------------------------------------------------------
    # 1. AgGrid (행 클릭이 가능한 엑셀 같은 표)
    # ---------------------------------------------------------
    if not participants:
        st.info("아직 등록된 참가자가 없습니다.")
    else:
        # 통계 표시
        m_count = len([p for p in participants if p['gender'] == 'M'])
        f_count = len([p for p in participants if p['gender'] == 'F'])
        st.caption(f"총 {len(participants)}명 (남 {m_count} / 여 {f_count})")

        # 데이터프레임 변환
        data = []
        for p in participants:
            memo_txt = str(p.get('memo', '')).strip()
            memo_mark = "📝" if memo_txt and memo_txt != 'None' else ""
            
            data.append({
                '성별': "남" if p['gender'] == 'M' else "여",
                '이름': f"{p['name']} {memo_mark}",
                '출생년도': p['birth_date'][:4],
                '전화번호': p['phone'] if p['phone'] else "-",
                '사는곳': p['location'] if p['location'] else "-",
                '직업': p['job'] if p['job'] else "-",
                'MBTI': p['mbti'] if p['mbti'] else "-",
                '방문': f"{p.get('visit_count', 0)}회",
                '경로': p['signup_route'] if p['signup_route'] else "-",
                '_full_name': p['name'],       
                '_full_birth': p['birth_date'] 
            })
        
        df = pd.DataFrame(data)

        # AgGrid 옵션 설정
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_column("_full_name", hide=True)
        gb.configure_column("_full_birth", hide=True)
        gb.configure_selection(selection_mode='single', use_checkbox=False, pre_selected_rows=[])
        gb.configure_grid_options(domLayout='autoHeight')
        gridOptions = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED, 
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True, 
            theme='streamlit', 
            key='aggrid_table'
        )

        # ---------------------------------------------------------
        # 2. 선택된 행 액션 바
        # ---------------------------------------------------------
        selected = grid_response['selected_rows']
        
        if selected is not None and len(selected) > 0:
            if isinstance(selected, pd.DataFrame):
                sel_row = selected.iloc[0] 
            else:
                sel_row = selected[0]      
            
            t_name = sel_row.get('_full_name') or sel_row.get('이름').split(' ')[0]
            t_birth = sel_row.get('_full_birth')

            target_p = next((p for p in participants if p['name'] == t_name and p['birth_date'] == t_birth), None)
            
            if target_p:
                with st.container(border=True):
                    c_msg, c_btn1, c_btn2 = st.columns([6, 2, 2])
                    with c_msg:
                        st.markdown(f"##### 👉 **{target_p['name']} ({target_p['birth_date'][:4]})**")
                    with c_btn1:
                        if st.button("ℹ️ 상세 정보", use_container_width=True):
                            show_detail_dialog(target_p['name'], target_p['birth_date'])
                    with c_btn2:
                        if st.button("🗑️ 명단 제외", type="primary", use_container_width=True):
                            remove_participant_dialog(target_p, st.session_state.current_session_id)

@st.dialog("참가자 추가")
def add_participant_dialog(gender, session_id):
    st.write(f"**{'남자' if gender=='M' else '여자'} 참가자 추가**")
    with st.form("add_p_form"):
        name = st.text_input("이름 *")
        birth_year = st.text_input("출생년도 (4자리) *")
        phone = st.text_input("전화번호 (숫자만)")
        job = st.text_input("직업")
        mbti = st.text_input("MBTI")
        location = st.text_input("사는곳")
        route = st.text_input("가입경로")
        
        if st.form_submit_button("추가하기"):
            if not name or len(birth_year) != 4:
                st.error("이름과 출생년도(4자리)는 필수입니다.")
            else:
                b_date = f"{birth_year}-01-01"
                db.add_participant(name, b_date, gender, job, mbti, phone, location, route)
                db.add_attendance(session_id, name, b_date)
                st.success("추가되었습니다!")
                st.rerun()

@st.dialog("참가자 제거")
def remove_participant_dialog(p, session_id):
    st.warning(f"{p['name']}님을 이번 회차에서 제거합니까?")
    if st.button("제거 확인", type="primary"):
        db.remove_participant_from_session(session_id, p['name'], p['birth_date'])
        st.success("제거되었습니다.")
        st.rerun()

@st.dialog("상세 정보")
def show_detail_dialog(name, birth_date):
    detail = db.get_participant_detail(name, birth_date)
    if not detail:
        st.error("정보를 찾을 수 없습니다.")
        return

    birth_year = detail['birth_date'][:4]
    
    st.subheader(f"{detail['name']} ({birth_year})")
    
    st.markdown("---") 

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"**출생년도:** {birth_year}")
        st.markdown(f"**직업:** {detail['job']}")
        st.markdown(f"**MBTI:** {detail['mbti']}")
        st.markdown(f"**지역:** {detail['location']}")
    
    with c2:
        st.markdown(f"**전화:** {detail['phone']}")
        st.markdown(f"**방문:** {detail['visit_count']}회")
        st.markdown(f"**첫방문:** {detail['first_visit_date']}")
        st.markdown(f"**경로:** {detail['signup_route']}")
    
    st.markdown("---")
    st.markdown("**📝 메모**")
    new_memo = st.text_area("관리자 메모", value=detail['memo'] or "")
    if st.button("메모 저장"):
        db.update_participant_memo(name, birth_date, new_memo)
        st.success("저장됨")
        st.rerun()

    st.markdown("---")
    st.markdown("**📅 방문 이력**")
    for v in detail['visit_history']:
        with st.expander(f"{v['session_date']} - {v['theme']}"):
            met = [f"{m['name']}" for m in v['met_people']]
            st.caption(f"만난 사람: {', '.join(met)}")

def check_duplicates(session_id):
    with st.spinner("중복 검사 중..."):
        dups = db.check_duplicate_meetings(session_id)
    
    if not dups:
        st.success("✅ 중복 만남이 없습니다!")
    else:
        st.error(f"⚠️ {len(dups)}개의 중복 만남 발견!")
        for d in dups:
            st.warning(f"{d['person1']} ↔ {d['person2']} ({', '.join(d['session_dates'])})")

# ---------------------------------------------------------
# 2. 참가자 DB 탭
# ---------------------------------------------------------
def render_participant_tab():
    
    # 검색어를 session_state에 저장하지 않으면 입력하다가 날아갈 수 있음
    if 'db_search_term' not in st.session_state:
        st.session_state.db_search_term = ""

    # 검색 입력창
    search = st.text_input("검색 (이름, 직업)", value=st.session_state.db_search_term, placeholder="엔터키를 누르면 검색됩니다.")
    st.session_state.db_search_term = search # 입력값 유지
    
    all_p = db.get_all_participants()
    if search:
        all_p = [p for p in all_p if search in p['name'] or (p['job'] and search in p['job'])]

    males = [p for p in all_p if p['gender'] == 'M']
    females = [p for p in all_p if p['gender'] == 'F']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### 남자 ({len(males)}명)")
        render_db_table(males, 'db_m')
    
    with col2:
        st.markdown(f"#### 여자 ({len(females)}명)")
        render_db_table(females, 'db_f')

# 1. render_db_table 중복 정의 제거 및 통합 (메모 아이콘 기능 포함)
def render_db_table(participants, key_suffix):
    if not participants:
        st.info("데이터가 없습니다.")
        return

    data = []
    for p in participants:
        # 📝 메모 아이콘 표시 기능 복구
        memo_mark = "📝" if p.get('memo') and str(p['memo']).strip() else ""
        
        data.append({
            '이름': f"{p['name']}{memo_mark}",
            '출생년도': p['birth_date'][:4],
            '직업': p['job'],
            'MBTI': p['mbti'],
            '지역': p['location'],
            '_full': p
        })
    
    df = pd.DataFrame(data)
    event = st.dataframe(
        df.drop(columns=['_full']), 
        use_container_width=True, 
        height=600, 
        hide_index=True, # 5. 참가자 테이블 컬럼 정리
        on_select="rerun", 
        selection_mode="single-row",
        key=f"table_{key_suffix}"
    )

    if event.selection.rows:
        sel = df.iloc[event.selection.rows[0]]['_full']
        c1, c2 = st.columns(2)
        if c1.button("상세 정보", key=f"d_det_{key_suffix}"):
            show_detail_dialog(sel['name'], sel['birth_date'])
        if c2.button("영구 삭제", type="primary", key=f"d_del_{key_suffix}"):
            delete_participant_dialog(sel)

@st.dialog("참가자 영구 삭제")
def delete_participant_dialog(p):
    st.error(f"⚠️ {p['name']}님을 DB에서 완전히 삭제합니다.\n\n모든 회차의 참가 기록이 함께 사라지며, 복구할 수 없습니다.")
    if st.button("삭제 확인"):
        db.delete_participant(p['name'], p['birth_date'])
        st.success("삭제되었습니다.")
        st.rerun()

# ---------------------------------------------------------
# 2. 추천 탭
# ---------------------------------------------------------
def render_recommend_tab():
    
    # 1. 세션 상태에 결과 저장소 만들기
    if 'recommend_results' not in st.session_state:
        st.session_state.recommend_results = None
    
    sessions = db.get_all_sessions()
    opts = [f"{s['session_date']} - {s['theme']}" for s in sessions]
    
    c1, c2 = st.columns([3, 1])
    if opts:
        sel_idx = c1.selectbox("⬇️ 기준 회차 멤버와 안 만난 사람 리스트업", range(len(opts)), format_func=lambda x: opts[x])
        
        # 성별 변환 (화면: 남자/여자 -> DB: M/F)
        gender_kor = c2.radio("추천 성별", ['남자', '여자'], horizontal=True)
        gender = 'M' if gender_kor == '남자' else 'F'
    else:
        c1.selectbox("회차", ["없음"])
        return

    f1, f2, f3 = st.columns(3)
    birth_min = f1.text_input("최소 출생년도 (예: 1980)")
    birth_max = f2.text_input("최대 출생년도 (예: 1990)")
    mbti_filter = f3.text_input("MBTI 검색 (예: E, I, N)")

    sort_option = st.radio("정렬 기준", ["최근 방문일 순", "방문 횟수 순"], horizontal=True)
    
    # 2. 버튼 누르면 -> 결과를 session_state에 저장
    if st.button("추천 검색 실행", type="primary", use_container_width=True):
        sid = sessions[sel_idx]['session_id']
        curr_year = datetime.now().year
        age_min, age_max = None, None
        if birth_max: age_min = curr_year - int(birth_max)
        if birth_min: age_max = curr_year - int(birth_min)

        # DB 조회 (최적화된 쿼리 사용)
        st.session_state.recommend_results = db.get_recommendations(sid, gender, age_min, age_max, mbti_filter)
        
        if not st.session_state.recommend_results:
            st.info("조건에 맞는 추천 대상이 없습니다.")

    # 3. 결과가 저장되어 있으면 표 그리기
    if st.session_state.recommend_results:
        recs = st.session_state.recommend_results 
        
        # 정렬 적용
        if sort_option == "최근 방문일 순":
            recs.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        else:
            recs.sort(key=lambda x: x['visit_count'], reverse=True)
        
        data = []
        for r in recs:
            memo_mark = " 📝" if r.get('memo') and str(r['memo']).strip() else ""
            
            # 🔥 [수정] 전화번호, 사는곳, 등록경로 컬럼 추가
            data.append({
                '이름': f"{r['name']}{memo_mark}",
                '출생년도': r['birth_date'][:4],
                '전화번호': r['phone'] if r['phone'] else "-",         # 추가됨
                '사는곳': r['location'] if r['location'] else "-",    # 추가됨
                '직업': r['job'],
                'MBTI': r['mbti'],
                '방문 횟수': f"{r['visit_count']}회",
                '최근 방문일': r['last_visit'],
                '등록경로': r['signup_route'] if r['signup_route'] else "-", # 추가됨
                '_full': r
            })
        
        df = pd.DataFrame(data)
        
        # 4. 표 그리기
        event = st.dataframe(
            df.drop(columns=['_full']), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun", 
            selection_mode="single-row"
        )
        
        if event.selection.rows:
            sel = df.iloc[event.selection.rows[0]]['_full']
            # 버튼이 표 바로 아래에 생김
            if st.button("ℹ️ 상세 정보 보기", use_container_width=True):
                show_detail_dialog(sel['name'], sel['birth_date'])

def check_password():
    """비밀번호 체크 함수"""
    if st.secrets.get("general", {}).get("dev_mode", False):
        return True
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    # 로그인 화면
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔒 접속 권한 확인")
        
        # 💡 [핵심] st.form으로 감싸면 엔터키가 먹힙니다!
        with st.form(key="login_form"):
            password = st.text_input("비밀번호를 입력하세요", type="password")
            
            # 폼 제출 버튼 (엔터 치면 이 버튼이 눌린 효과)
            submit_button = st.form_submit_button("접속하기", type="primary", use_container_width=True)
            
            if submit_button:
                # 1. 한글 입력 감지
                if re.search('[가-힣]', password):
                    st.warning("⚠️ 한글 키가 켜져 있습니다. 영문으로 변경해주세요.")
                
                # 2. 대소문자 무시하고 비밀번호 체크
                elif password.lower() == st.secrets["general"]["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")
                    
    return False

if __name__ == "__main__":
    # 데이터베이스 초기화
    db.init_db()
    
    # 비밀번호가 맞을 때만 main() 실행
    if check_password():
        main()