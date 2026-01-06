"""메이크어토스트 - Streamlit 웹 애플리케이션 (UI 복구 완료)"""
import streamlit as st
import database as db
from datetime import datetime
import pandas as pd
import tempfile
import os

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

# ---------------------------------------------------------
# 1. 회차 관리 탭
# ---------------------------------------------------------
def render_session_tab():
    st.header("회차 관리")
    
    # 상단 액션 바
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    sessions = db.get_all_sessions()
    session_options = [f"{s['session_date']} {s['session_time']} - {s['theme']}" for s in sessions]
    
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
        if st.button("새 회차 생성", use_container_width=True):
            create_session_dialog()
            
    with col3:
        if st.button("회차 삭제", type="primary", use_container_width=True):
            if st.session_state.current_session_id:
                delete_session_dialog(st.session_state.current_session_id, sessions)
            else:
                st.warning("삭제할 회차를 선택해주세요!")
                
    with col4:
        if st.button("엑셀 임포트", use_container_width=True):
            import_excel_dialog()
            
    with col5:
        if st.button("새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 현재 회차 정보 및 참가자 관리
    if st.session_state.current_session_id:
        render_current_session_info(sessions)

@st.dialog("새 회차 생성")
def create_session_dialog():
    with st.form("create_session_form"):
        session_date = st.date_input("날짜")
        session_time = st.text_input("시간대 (예: 19:30)", value="19:30")
        
        # 🔥 [복구 완료] 드롭다운 메뉴 복구
        theme = st.selectbox(
            "주제",
            ['운동 좋아하는 사람들', 'MBTI I들의 모임', 'MBTI E들의 모임', '결혼', '기타']
        )
        
        # '기타' 선택 시 직접 입력창 보여주기 (옵션)
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

def render_current_session_info(sessions):
    curr = next((s for s in sessions if s['session_id'] == st.session_state.current_session_id), None)
    if not curr: return

    st.info(f"📅 **{curr['session_date']}** {curr['session_time']} | 주제: **{curr['theme']}** | HOST: **{curr['host']}**")

    # 참가자 목록 가져오기
    participants = db.get_session_participants(curr['session_id'])
    
    # 🔥 [복구 완료] 좌우 분할 UI
    males = [p for p in participants if p['gender'] == 'M']
    females = [p for p in participants if p['gender'] == 'F']

    col1, col2 = st.columns(2)

    # 남자 참가자 영역
    with col1:
        st.subheader(f"남자 ({len(males)}명)")
        render_participant_table(males, 'M')
        if st.button("남자 참가자 추가", key="add_m", use_container_width=True):
            add_participant_dialog('M', curr['session_id'])

    # 여자 참가자 영역
    with col2:
        st.subheader(f"여자 ({len(females)}명)")
        render_participant_table(females, 'F')
        if st.button("여자 참가자 추가", key="add_f", use_container_width=True):
            add_participant_dialog('F', curr['session_id'])
    
    st.markdown("---")
    if st.button("🔍 중복 만남 체크", type="primary", use_container_width=True):
        check_duplicates(curr['session_id'])

def render_participant_table(participants, gender_code):
    if not participants:
        st.info("참가자가 없습니다.")
        return

    data = []
    for p in participants:
        data.append({
            '이름': p['name'],
            '년생': p['birth_date'][:4],
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

    st.subheader(f"{detail['name']} ({detail['birth_date'][:4]})")
    c1, c2 = st.columns(2)
    c1.markdown(f"**직업:** {detail['job']}\n\n**MBTI:** {detail['mbti']}\n\n**지역:** {detail['location']}")
    c2.markdown(f"**전화:** {detail['phone']}\n\n**방문:** {detail['visit_count']}회\n\n**첫방문:** {detail['first_visit_date']}")
    
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
# 2. 참가자 DB 탭 (UI 복구: 좌우 분할)
# ---------------------------------------------------------
def render_participant_tab():
    st.header("참가자 DB")
    
    search = st.text_input("검색 (이름, 직업)", placeholder="엔터키를 누르면 검색됩니다.")
    
    all_p = db.get_all_participants()
    if search:
        all_p = [p for p in all_p if search in p['name'] or (p['job'] and search in p['job'])]

    # 🔥 [복구 완료] 좌우 분할하여 표시
    males = [p for p in all_p if p['gender'] == 'M']
    females = [p for p in all_p if p['gender'] == 'F']

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"남자 ({len(males)}명)")
        render_db_table(males, 'db_m')
    
    with col2:
        st.subheader(f"여자 ({len(females)}명)")
        render_db_table(females, 'db_f')

def render_db_table(participants, key_suffix):
    if not participants:
        st.info("데이터가 없습니다.")
        return

    data = []
    for p in participants:
        data.append({
            '이름': p['name'],
            '생년': p['birth_date'][:4],
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
# 3. 추천 탭
# ---------------------------------------------------------
def render_recommend_tab():
    st.header("참가자 추천")
    
    sessions = db.get_all_sessions()
    opts = [f"{s['session_date']} - {s['theme']}" for s in sessions]
    
    c1, c2 = st.columns([3, 1])
    if opts:
        sel_idx = c1.selectbox("기준 회차 (이 회차 멤버와 안 만난 사람 추천)", range(len(opts)), format_func=lambda x: opts[x])
        gender = c2.radio("추천 성별", ['M', 'F'], horizontal=True)
    else:
        c1.selectbox("회차", ["없음"])
        return
    
    if c1.button("추천 검색 실행", type="primary"):
        sid = sessions[sel_idx]['session_id']
        recs = db.get_recommendations(sid, gender)
        
        if not recs:
            st.info("조건에 맞는 추천 대상이 없습니다.")
        else:
            recs.sort(key=lambda x: x['visit_count'], reverse=True)
            
            data = []
            for r in recs:
                data.append({
                    '이름': r['name'],
                    '나이': f"{datetime.now().year - int(r['birth_date'][:4])}세",
                    '직업': r['job'],
                    'MBTI': r['mbti'],
                    '방문': f"{r['visit_count']}회",
                    '마지막': r['last_visit'],
                    '_full': r
                })
            
            df = pd.DataFrame(data)
            event = st.dataframe(df.drop(columns=['_full']), use_container_width=True, on_select="rerun", selection_mode="single-row")
            
            if event.selection.rows:
                sel = df.iloc[event.selection.rows[0]]['_full']
                if st.button("상세 정보 보기"):
                    show_detail_dialog(sel['name'], sel['birth_date'])

if __name__ == "__main__":
    db.init_db()
    main()