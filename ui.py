import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import database as db
import openpyxl
import re
from datetime import datetime

class MakeToastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("메이크어토스트 참가 인원 지정 프로그램")
        self.root.geometry("1600x800")
        
        # 탭 생성
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 탭 1: 회차 관리
        self.session_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.session_frame, text="회차 관리")
        self.setup_session_tab()
        
        # 탭 2: 참가자 DB
        self.participant_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.participant_frame, text="참가자 DB")
        self.setup_participant_tab()
        
        # 탭 3: 추천
        self.recommend_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recommend_frame, text="추천")
        self.setup_recommend_tab()
        
        # 현재 선택된 회차 ID
        self.current_session_id = None
    
    def setup_session_tab(self):
        """회차 관리 탭"""
        # 상단: 회차 선택
        top_frame = ttk.Frame(self.session_frame)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(top_frame, text="회차 선택:").pack(side='left', padx=5)
        
        self.session_combo = ttk.Combobox(top_frame, width=40, state='readonly')
        self.session_combo.pack(side='left', padx=5)
        self.session_combo.bind('<<ComboboxSelected>>', self.on_session_selected)
        
        ttk.Button(top_frame, text="새 회차 생성", 
                  command=self.create_new_session).pack(side='left', padx=5)
        ttk.Button(top_frame, text="회차 삭제", 
                  command=self.delete_session).pack(side='left', padx=5)
        ttk.Button(top_frame, text="엑셀 임포트", 
                  command=self.import_excel).pack(side='left', padx=5)
        ttk.Button(top_frame, text="새로고침", 
                  command=self.refresh_sessions).pack(side='left', padx=5)
        
        # 중단: 회차 정보
        info_frame = ttk.LabelFrame(self.session_frame, text="회차 정보")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.session_info_label = ttk.Label(info_frame, text="회차를 선택해주세요")
        self.session_info_label.pack(padx=10, pady=10)
        
        # 하단: 참가자 목록 (남녀 분리)
        list_frame = ttk.LabelFrame(self.session_frame, text="참가자 목록")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 좌우 분할
        left_frame = ttk.Frame(list_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        right_frame = ttk.Frame(list_frame)
        right_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # 왼쪽: 남자
        male_label_frame = ttk.LabelFrame(left_frame, text="남자 참가자")
        male_label_frame.pack(fill='both', expand=True)
        
        columns = ('name', 'birth_date', 'job', 'mbti', 'phone', 'location', 'signup_route')
        self.male_tree = ttk.Treeview(male_label_frame, columns=columns, show='headings', height=15)
        
        self.male_tree.heading('name', text='이름')
        self.male_tree.heading('birth_date', text='출생년도')
        self.male_tree.heading('job', text='직업')
        self.male_tree.heading('mbti', text='MBTI')
        self.male_tree.heading('phone', text='전화번호')
        self.male_tree.heading('location', text='사는곳')
        self.male_tree.heading('signup_route', text='등록경로')
        
        self.male_tree.column('name', width=70)
        self.male_tree.column('birth_date', width=70)
        self.male_tree.column('job', width=80)
        self.male_tree.column('mbti', width=50)
        self.male_tree.column('phone', width=100)
        self.male_tree.column('location', width=80)
        self.male_tree.column('signup_route', width=80)
        
        male_scrollbar = ttk.Scrollbar(male_label_frame, orient='vertical', command=self.male_tree.yview)
        self.male_tree.configure(yscrollcommand=male_scrollbar.set)
        
        self.male_tree.pack(side='left', fill='both', expand=True)
        male_scrollbar.pack(side='right', fill='y')
        
        self.male_tree.bind('<Double-1>', self.on_male_participant_double_click)
        self.male_tree.bind('<Button-3>', lambda e: self.show_participant_context_menu(e, 'M'))
        
        ttk.Button(male_label_frame, text="남자 참가자 추가", 
                  command=lambda: self.add_participant_to_session('M')).pack(pady=5)
        
        # 오른쪽: 여자
        female_label_frame = ttk.LabelFrame(right_frame, text="여자 참가자")
        female_label_frame.pack(fill='both', expand=True)
        
        self.female_tree = ttk.Treeview(female_label_frame, columns=columns, show='headings', height=15)
        
        self.female_tree.heading('name', text='이름')
        self.female_tree.heading('birth_date', text='출생년도')
        self.female_tree.heading('job', text='직업')
        self.female_tree.heading('mbti', text='MBTI')
        self.female_tree.heading('phone', text='전화번호')
        self.female_tree.heading('location', text='사는곳')
        self.female_tree.heading('signup_route', text='등록경로')
        
        self.female_tree.column('name', width=70)
        self.female_tree.column('birth_date', width=70)
        self.female_tree.column('job', width=80)
        self.female_tree.column('mbti', width=50)
        self.female_tree.column('phone', width=100)
        self.female_tree.column('location', width=80)
        self.female_tree.column('signup_route', width=80)
        
        female_scrollbar = ttk.Scrollbar(female_label_frame, orient='vertical', command=self.female_tree.yview)
        self.female_tree.configure(yscrollcommand=female_scrollbar.set)
        
        self.female_tree.pack(side='left', fill='both', expand=True)
        female_scrollbar.pack(side='right', fill='y')
        
        self.female_tree.bind('<Double-1>', self.on_female_participant_double_click)
        self.female_tree.bind('<Button-3>', lambda e: self.show_participant_context_menu(e, 'F'))
        
        ttk.Button(female_label_frame, text="여자 참가자 추가", 
                  command=lambda: self.add_participant_to_session('F')).pack(pady=5)
        
        # 중복 체크 버튼 (하단 중앙에 별도 프레임으로)
        check_frame = ttk.Frame(self.session_frame)
        check_frame.pack(side='bottom', pady=10)
        
        ttk.Button(check_frame, text="🔍 중복 체크", 
                  command=self.check_duplicates, width=20).pack()
        
        # 초기 데이터 로드
        self.refresh_sessions()
    
    def setup_participant_tab(self):
        """참가자 DB 탭"""
        # 검색 바
        search_frame = ttk.Frame(self.participant_frame)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(search_frame, text="검색:").pack(side='left', padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        ttk.Button(search_frame, text="검색", 
                  command=self.search_participants).pack(side='left', padx=5)
        ttk.Button(search_frame, text="전체 보기", 
                  command=self.load_all_participants).pack(side='left', padx=5)
        
        # 참가자 리스트 (남녀 분리)
        list_container = ttk.Frame(self.participant_frame)
        list_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 왼쪽: 남자
        male_frame = ttk.LabelFrame(list_container, text="남자")
        male_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        columns = ('name', 'birth_date', 'job', 'mbti', 'phone', 'location', 'signup_route', 'visit_count')
        self.participant_male_tree = ttk.Treeview(male_frame, 
                                            columns=columns, show='headings')
        
        self.participant_male_tree.heading('name', text='이름')
        self.participant_male_tree.heading('birth_date', text='출생년도')
        self.participant_male_tree.heading('job', text='직업')
        self.participant_male_tree.heading('mbti', text='MBTI')
        self.participant_male_tree.heading('phone', text='전화번호')
        self.participant_male_tree.heading('location', text='사는곳')
        self.participant_male_tree.heading('signup_route', text='등록경로')
        self.participant_male_tree.heading('visit_count', text='방문횟수')
        
        self.participant_male_tree.column('name', width=70)
        self.participant_male_tree.column('birth_date', width=70)
        self.participant_male_tree.column('job', width=80)
        self.participant_male_tree.column('mbti', width=50)
        self.participant_male_tree.column('phone', width=100)
        self.participant_male_tree.column('location', width=70)
        self.participant_male_tree.column('signup_route', width=70)
        self.participant_male_tree.column('visit_count', width=60)
        
        male_scrollbar = ttk.Scrollbar(male_frame, orient='vertical', 
                                 command=self.participant_male_tree.yview)
        self.participant_male_tree.configure(yscrollcommand=male_scrollbar.set)
        
        self.participant_male_tree.pack(side='left', fill='both', expand=True)
        male_scrollbar.pack(side='right', fill='y')
        
        self.participant_male_tree.bind('<Double-1>', self.show_participant_detail)
        self.participant_male_tree.bind('<Button-3>', lambda e: self.show_participant_db_context_menu(e, 'M'))
        
        # 오른쪽: 여자
        female_frame = ttk.LabelFrame(list_container, text="여자")
        female_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.participant_female_tree = ttk.Treeview(female_frame, 
                                            columns=columns, show='headings')
        
        self.participant_female_tree.heading('name', text='이름')
        self.participant_female_tree.heading('birth_date', text='출생년도')
        self.participant_female_tree.heading('job', text='직업')
        self.participant_female_tree.heading('mbti', text='MBTI')
        self.participant_female_tree.heading('phone', text='전화번호')
        self.participant_female_tree.heading('location', text='사는곳')
        self.participant_female_tree.heading('signup_route', text='등록경로')
        self.participant_female_tree.heading('visit_count', text='방문횟수')
        
        self.participant_female_tree.column('name', width=70)
        self.participant_female_tree.column('birth_date', width=70)
        self.participant_female_tree.column('job', width=80)
        self.participant_female_tree.column('mbti', width=50)
        self.participant_female_tree.column('phone', width=100)
        self.participant_female_tree.column('location', width=70)
        self.participant_female_tree.column('signup_route', width=70)
        self.participant_female_tree.column('visit_count', width=60)
        
        female_scrollbar = ttk.Scrollbar(female_frame, orient='vertical', 
                                 command=self.participant_female_tree.yview)
        self.participant_female_tree.configure(yscrollcommand=female_scrollbar.set)
        
        self.participant_female_tree.pack(side='left', fill='both', expand=True)
        female_scrollbar.pack(side='right', fill='y')
        
        self.participant_female_tree.bind('<Double-1>', self.show_participant_detail)
        self.participant_female_tree.bind('<Button-3>', lambda e: self.show_participant_db_context_menu(e, 'F'))
        
        # 초기 데이터 로드
        self.load_all_participants()
    
    def setup_recommend_tab(self):
        """추천 탭"""
        # 필터 패널
        filter_frame = ttk.LabelFrame(self.recommend_frame, text="필터 조건")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(row1, text="회차:").pack(side='left', padx=5)
        self.recommend_session_combo = ttk.Combobox(row1, width=30, state='readonly')
        self.recommend_session_combo.pack(side='left', padx=5)
        
        ttk.Label(row1, text="성별:").pack(side='left', padx=(20, 5))
        self.gender_var = tk.StringVar(value="M")
        ttk.Radiobutton(row1, text="남", variable=self.gender_var, value="M").pack(side='left')
        ttk.Radiobutton(row1, text="여", variable=self.gender_var, value="F").pack(side='left')
        
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(row2, text="출생년도:").pack(side='left', padx=5)
        self.birth_year_min_entry = ttk.Entry(row2, width=10)
        self.birth_year_min_entry.pack(side='left', padx=5)
        self.birth_year_min_entry.insert(0, "예: 1990")
        self.birth_year_min_entry.bind('<FocusIn>', lambda e: self.birth_year_min_entry.delete(0, 'end') if self.birth_year_min_entry.get() == "예: 1990" else None)
        
        ttk.Label(row2, text="~").pack(side='left')
        self.birth_year_max_entry = ttk.Entry(row2, width=10)
        self.birth_year_max_entry.pack(side='left', padx=5)
        self.birth_year_max_entry.insert(0, "예: 1995")
        self.birth_year_max_entry.bind('<FocusIn>', lambda e: self.birth_year_max_entry.delete(0, 'end') if self.birth_year_max_entry.get() == "예: 1995" else None)
        
        ttk.Label(row2, text="MBTI:").pack(side='left', padx=(20, 5))
        self.mbti_entry = ttk.Entry(row2, width=10)
        self.mbti_entry.pack(side='left', padx=5)
        
        ttk.Button(row2, text="검색", command=self.search_recommendations).pack(side='left', padx=20)
        
        # 정렬 옵션
        sort_frame = ttk.Frame(self.recommend_frame)
        sort_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(sort_frame, text="정렬:").pack(side='left', padx=5)
        self.sort_var = tk.StringVar(value="last_visit")
        ttk.Radiobutton(sort_frame, text="최근 방문일순", 
                       variable=self.sort_var, value="last_visit",
                       command=self.sort_recommendations).pack(side='left', padx=5)
        ttk.Radiobutton(sort_frame, text="방문횟수순", 
                       variable=self.sort_var, value="visit_count",
                       command=self.sort_recommendations).pack(side='left', padx=5)
        
        # 추천 결과 리스트
        columns = ('name', 'birth_date', 'job', 'mbti', 'phone',
                  'location', 'signup_route', 'last_visit', 'visit_count')
        self.recommend_tree = ttk.Treeview(self.recommend_frame, 
                                          columns=columns, show='headings')
        
        self.recommend_tree.heading('name', text='이름')
        self.recommend_tree.heading('birth_date', text='출생년도')
        self.recommend_tree.heading('job', text='직업')
        self.recommend_tree.heading('mbti', text='MBTI')
        self.recommend_tree.heading('phone', text='전화번호')
        self.recommend_tree.heading('location', text='사는곳')
        self.recommend_tree.heading('signup_route', text='등록경로')
        self.recommend_tree.heading('last_visit', text='최근방문')
        self.recommend_tree.heading('visit_count', text='방문횟수')
        
        self.recommend_tree.column('name', width=70)
        self.recommend_tree.column('birth_date', width=70)
        self.recommend_tree.column('job', width=80)
        self.recommend_tree.column('mbti', width=50)
        self.recommend_tree.column('phone', width=100)
        self.recommend_tree.column('location', width=70)
        self.recommend_tree.column('signup_route', width=70)
        self.recommend_tree.column('last_visit', width=80)
        self.recommend_tree.column('visit_count', width=70)
        
        scrollbar = ttk.Scrollbar(self.recommend_frame, orient='vertical', 
                                 command=self.recommend_tree.yview)
        self.recommend_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recommend_tree.pack(side='left', fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 더블클릭 상세보기
        self.recommend_tree.bind('<Double-1>', self.show_recommend_detail)
        
        # 회차 목록 로드
        self.refresh_recommend_sessions()
    
    # ===== 이벤트 핸들러들 =====
    
    def refresh_sessions(self):
        """회차 목록 새로고침"""
        sessions = db.get_all_sessions()
        session_list = [f"{s['session_date']} {s['session_time']} - {s['theme']}" 
                       for s in sessions]
        self.session_combo['values'] = session_list
   
        if sessions:
            self.session_combo.current(0)
            self.on_session_selected()
    
    def on_session_selected(self, event=None):
        """회차 선택 시"""
        if not self.session_combo.get():
            return
            
        sessions = db.get_all_sessions()
        selected_idx = self.session_combo.current()
        if selected_idx < 0 or selected_idx >= len(sessions):
            return
            
        session = sessions[selected_idx]
        
        self.current_session_id = session['session_id']
        
        # 회차 정보 표시
        info_text = (f"📅 {session['session_date']} {session['session_time']} | "
                    f"주제: {session['theme']} | "
                    f"HOST: {session['host']}")
        self.session_info_label.config(text=info_text)
        
        self.load_session_participants()
    
    def load_session_participants(self):
        """현재 회차 참가자 목록 로드 (남녀 분리)"""
        # 기존 항목 삭제
        for item in self.male_tree.get_children():
            self.male_tree.delete(item)
        for item in self.female_tree.get_children():
            self.female_tree.delete(item)
        
        if not self.current_session_id:
            return
        
        participants = db.get_session_participants(self.current_session_id)
        
        for p in participants:
            birth_year = p['birth_date'][:4]
            values = (p['name'], birth_year, p['job'], p['mbti'], p['phone'], 
                     p['location'] or '', p['signup_route'] or '')
            tags = (p['name'], p['birth_date'])
            
            if p['gender'] == 'M':
                self.male_tree.insert('', 'end', values=values, tags=tags)
            else:
                self.female_tree.insert('', 'end', values=values, tags=tags)
    
    def check_duplicates(self):
        """중복 체크 및 표시"""
        if not self.current_session_id:
            messagebox.showwarning("경고", "회차를 먼저 선택해주세요!")
            return
        
        duplicates = db.check_duplicate_meetings(self.current_session_id)
        
        if not duplicates:
            messagebox.showinfo("체크 완료", "중복된 매칭이 없습니다! ✅")
            return
        
        # 중복된 사람들 찾아서 빨간색으로 표시
        duplicate_people = set()
        for dup in duplicates:
            duplicate_people.add((dup['person1'], dup['person1_birth']))
            duplicate_people.add((dup['person2'], dup['person2_birth']))
        
        # 남자/여자 트리 모두 순회
        for tree in [self.male_tree, self.female_tree]:
            for item in tree.get_children():
                tags = tree.item(item, 'tags')
                if len(tags) >= 2 and (tags[0], tags[1]) in duplicate_people:
                    tree.item(item, tags=('duplicate',))
            
            # 빨간색 태그 설정
            tree.tag_configure('duplicate', background='#ffcccc')
        
        # 중복 내역 메시지
        msg = "⚠️ 중복 매칭 발견!\n\n"
        for dup in duplicates:
            sessions_str = ', '.join(map(str, dup['session_dates']))
            msg += f"• {dup['person1']} ↔ {dup['person2']}\n"
            msg += f"  → {sessions_str}회차에서 만남\n\n"
        
        messagebox.showwarning("중복 매칭", msg)
    
    def create_new_session(self):
        """새 회차 생성 다이얼로그"""
        from tkcalendar import DateEntry
        
        dialog = tk.Toplevel(self.root)
        dialog.title("새 회차 생성")
        dialog.geometry("400x250")
        
        ttk.Label(dialog, text="날짜:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        date_picker = DateEntry(dialog, width=18, background='darkblue',
                            foreground='white', borderwidth=2, 
                            date_pattern='yyyy-mm-dd')
        date_picker.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="시간대:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        time_entry = ttk.Entry(dialog)
        time_entry.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="주제:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        theme_combo = ttk.Combobox(dialog, values=['운동 좋아하는 사람들', 'MBTI I들의 모임', 'MBTI E들의 모임', '결혼', '기타'], state='readonly')
        theme_combo.grid(row=2, column=1, padx=10, pady=10)
        theme_combo.current(0)
        
        ttk.Label(dialog, text="HOST:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        host_entry = ttk.Entry(dialog)
        host_entry.grid(row=3, column=1, padx=10, pady=10)
        
        def save_session():
            try:
                session_id = db.create_session(
                    date_picker.get(),
                    time_entry.get(),
                    theme_combo.get(),
                    host_entry.get()
                )
                messagebox.showinfo("성공", "회차가 생성되었습니다!")
                dialog.destroy()
                self.refresh_sessions()
                self.refresh_recommend_sessions()
            except Exception as e:
                messagebox.showerror("오류", f"회차 생성 실패: {e}")
        
        ttk.Button(dialog, text="생성", command=save_session).grid(row=4, column=0, 
                                                                columnspan=2, pady=20)
    
    def add_participant_to_session(self, gender):
        """현재 회차에 참가자 추가"""
        if not self.current_session_id:
            messagebox.showwarning("경고", "회차를 먼저 선택해주세요!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'남자' if gender == 'M' else '여자'} 참가자 추가")
        dialog.geometry("400x500")
        
        ttk.Label(dialog, text="이름:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="출생년도:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        birth_entry = ttk.Entry(dialog)
        birth_entry.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="닉네임:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        nickname_entry = ttk.Entry(dialog)
        nickname_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="전화번호:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        phone_entry = ttk.Entry(dialog)
        phone_entry.grid(row=3, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="직업:").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        job_entry = ttk.Entry(dialog)
        job_entry.grid(row=4, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="MBTI:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        mbti_entry = ttk.Entry(dialog)
        mbti_entry.grid(row=5, column=1, padx=10, pady=10)
        
        def save_participant():
            name = name_entry.get().strip()
            birth_year = birth_entry.get().strip()
            
            if not name or not birth_year:
                messagebox.showerror("오류", "이름과 출생년도는 필수입니다!")
                return
            
            birth_date = f"{birth_year}-01-01"
            
            try:
                # 참가자 추가
                db.add_participant(
                    name=name,
                    birth_date=birth_date,
                    gender=gender,
                    job=job_entry.get(),
                    mbti=mbti_entry.get(),
                    phone=phone_entry.get(),
                    memo=""
                )
                
                # 회차에 참가자 추가
                db.add_attendance(self.current_session_id, name, birth_date)
                
                messagebox.showinfo("완료", "참가자가 추가되었습니다!")
                dialog.destroy()
                self.load_session_participants()
            except Exception as e:
                messagebox.showerror("오류", f"추가 실패: {e}")
        
        ttk.Button(dialog, text="추가", command=save_participant).grid(row=6, column=0, 
                                                                    columnspan=2, pady=20)
    
    def import_excel(self):
        """엑셀 파일 임포트"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
        
        response = messagebox.askyesno("확인", 
                                    "엑셀 파일을 임포트하시겠습니까?\n"
                                    "모든 시트가 회차로 변환됩니다.")
        
        if response:
            try:
                db.import_excel_file(file_path)  # 여기! file_path만 전달
                messagebox.showinfo("완료", "엑셀 임포트가 완료되었습니다!")
                self.refresh_sessions()
                self.refresh_recommend_sessions()
                self.load_all_participants()
            except Exception as e:
                messagebox.showerror("오류", f"임포트 실패:\n{e}")
    
    def delete_session(self):
        """현재 선택된 회차 삭제"""
        if not self.current_session_id:
            messagebox.showwarning("경고", "삭제할 회차를 선택해주세요!")
            return
        
        # 확인 메시지
        sessions = db.get_all_sessions()
        current_session = next((s for s in sessions if s['session_id'] == self.current_session_id), None)
        
        if not current_session:
            return
        
        response = messagebox.askyesno("확인", 
                                       f"이 회차를 삭제하시겠습니까?\n"
                                       f"날짜: {current_session['session_date']}\n"
                                       f"주제: {current_session['theme']}\n\n"
                                       f"⚠️ 이 회차의 참가 기록도 모두 삭제됩니다!")
        
        if response:
            try:
                db.delete_session(self.current_session_id)
                messagebox.showinfo("완료", "회차가 삭제되었습니다.")
                self.current_session_id = None
                self.refresh_sessions()
                self.refresh_recommend_sessions()  # 추천 탭도 새로고침
            except Exception as e:
                messagebox.showerror("오류", f"회차 삭제 실패: {e}")
    
    def show_participant_context_menu(self, event, gender):
        """참가자 우클릭 메뉴"""
        tree = self.male_tree if gender == 'M' else self.female_tree
        
        # 클릭한 아이템 선택
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            
            # 컨텍스트 메뉴 생성
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="이 참가자 제거", 
                           command=lambda: self.remove_participant_from_session(tree, item))
            menu.add_separator()
            menu.add_command(label="상세 정보 보기", 
                           command=lambda: self.show_detail_from_item(tree, item))
            
            # 메뉴 표시
            menu.post(event.x_root, event.y_root)
    
    def remove_participant_from_session(self, tree, item):
        """회차에서 참가자 제거"""
        if not self.current_session_id:
            return
        
        tags = tree.item(item, 'tags')
        if len(tags) < 2:
            return
        
        name, birth_date = tags[0], tags[1]
        
        response = messagebox.askyesno("확인", 
                                       f"{name}님을 현재 회차에서 제거하시겠습니까?")
        
        if response:
            try:
                db.remove_participant_from_session(self.current_session_id, name, birth_date)
                messagebox.showinfo("완료", "참가자가 제거되었습니다.")
                self.load_session_participants()
            except Exception as e:
                messagebox.showerror("오류", f"제거 실패: {e}")
    
    def show_detail_from_item(self, tree, item):
        """트리 아이템에서 상세 정보 표시"""
        tags = tree.item(item, 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def on_male_participant_double_click(self, event):
        """남자 참가자 더블클릭 시 상세보기"""
        selection = self.male_tree.selection()
        if not selection:
            return
        
        tags = self.male_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def on_female_participant_double_click(self, event):
        """여자 참가자 더블클릭 시 상세보기"""
        selection = self.female_tree.selection()
        if not selection:
            return
        
        tags = self.female_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def load_all_participants(self):
        """전체 참가자 로드 (남녀 분리)"""
        for item in self.participant_male_tree.get_children():
            self.participant_male_tree.delete(item)
        for item in self.participant_female_tree.get_children():
            self.participant_female_tree.delete(item)
        
        participants = db.get_all_participants()
        
        for p in participants:
            detail = db.get_participant_detail(p['name'], p['birth_date'])
            birth_year = p['birth_date'][:4]
            
            values = (p['name'], birth_year, p['job'], p['mbti'], 
                     p['phone'], p['location'] or '', p['signup_route'] or '', detail['visit_count'])
            tags = (p['name'], p['birth_date'])
            
            if p['gender'] == 'M':
                self.participant_male_tree.insert('', 'end', values=values, tags=tags)
            else:
                self.participant_female_tree.insert('', 'end', values=values, tags=tags)
    
    def search_participants(self):
        """참가자 검색 (남녀 분리)"""
        search_term = self.search_entry.get().lower()
        
        for item in self.participant_male_tree.get_children():
            self.participant_male_tree.delete(item)
        for item in self.participant_female_tree.get_children():
            self.participant_female_tree.delete(item)
        
        participants = db.get_all_participants()
        
        for p in participants:
            if search_term in p['name'].lower() or search_term in (p['job'] or '').lower():
                detail = db.get_participant_detail(p['name'], p['birth_date'])
                birth_year = p['birth_date'][:4]
                
                values = (p['name'], birth_year, p['job'], p['mbti'],
                         p['phone'], p['location'] or '', p['signup_route'] or '', detail['visit_count'])
                tags = (p['name'], p['birth_date'])
                
                if p['gender'] == 'M':
                    self.participant_male_tree.insert('', 'end', values=values, tags=tags)
                else:
                    self.participant_female_tree.insert('', 'end', values=values, tags=tags)
    
    def show_participant_db_context_menu(self, event, gender):
        """참가자 DB 탭 우클릭 메뉴"""
        tree = self.participant_male_tree if gender == 'M' else self.participant_female_tree
        
        # 클릭한 아이템 선택
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            
            # 컨텍스트 메뉴 생성
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="이 참가자 삭제", 
                           command=lambda: self.delete_participant_from_db(tree, item))
            menu.add_separator()
            menu.add_command(label="상세 정보 보기", 
                           command=lambda: self.show_participant_detail_from_tree(tree, item))
            
            # 메뉴 표시
            menu.post(event.x_root, event.y_root)
    
    def delete_participant_from_db(self, tree, item):
        """참가자를 DB에서 삭제"""
        tags = tree.item(item, 'tags')
        if len(tags) < 2:
            return
        
        name, birth_date = tags[0], tags[1]
        
        response = messagebox.askyesno("확인", 
                                       f"{name}님을 데이터베이스에서 삭제하시겠습니까?\n"
                                       f"(참가 기록도 함께 삭제됩니다)")
        
        if response:
            try:
                db.delete_participant(name, birth_date)
                messagebox.showinfo("완료", "참가자가 삭제되었습니다.")
                self.load_all_participants()
            except Exception as e:
                messagebox.showerror("오류", f"삭제 실패: {e}")
    
    def show_participant_detail_from_tree(self, tree, item):
        """트리 아이템에서 상세 정보 표시"""
        tags = tree.item(item, 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def show_participant_detail(self, event):
        """참가자 상세보기 (남녀 트리 모두 지원)"""
        # 어느 트리에서 클릭했는지 확인
        widget = event.widget
        selection = widget.selection()
        if not selection:
            return
        
        tags = widget.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def refresh_recommend_sessions(self):
        """추천 탭 회차 목록 새로고침"""
        sessions = db.get_all_sessions()
        session_list = [f"{s['session_date']} {s['session_time']}" 
                    for s in sessions]
        self.recommend_session_combo['values'] = session_list
        
        if sessions:
            self.recommend_session_combo.current(0)
        else:
            self.recommend_session_combo.set('')
    
    def search_recommendations(self):
        """추천 검색"""
        if not self.recommend_session_combo.get():
            messagebox.showwarning("경고", "회차를 선택해주세요!")
            return
        
        sessions = db.get_all_sessions()
        selected_idx = self.recommend_session_combo.current()
        session_id = sessions[selected_idx]['session_id']
        
        gender = self.gender_var.get()
        
        birth_year_min = None
        birth_year_max = None
        
        try:
            min_val = self.birth_year_min_entry.get().strip()
            if min_val and min_val != "예: 1990":
                birth_year_min = int(min_val)
            
            max_val = self.birth_year_max_entry.get().strip()
            if max_val and max_val != "예: 1995":
                birth_year_max = int(max_val)
        except ValueError:
            messagebox.showerror("오류", "출생년도는 4자리 숫자로 입력해주세요! (예: 1990)")
            return
        
        mbti = self.mbti_entry.get().strip().upper() or None

        # 출생년도를 나이로 변환
        age_min = None
        age_max = None
        current_year = datetime.now().year

        if birth_year_min:
            age_max = current_year - birth_year_min
        if birth_year_max:
            age_min = current_year - birth_year_max

        self.recommendations = db.get_recommendations(session_id, gender, age_min, age_max, mbti)
        
        self.display_recommendations()
    
    def display_recommendations(self):
        """추천 결과 표시"""
        for item in self.recommend_tree.get_children():
            self.recommend_tree.delete(item)
        
        for p in self.recommendations:
            birth_year = p['birth_date'][:4]
            
            self.recommend_tree.insert('', 'end',
                                      values=(p['name'], birth_year, p['job'], p['mbti'], p['phone'],
                                             p['location'] or '', p['signup_route'] or '', 
                                             p['last_visit'] or '-', p['visit_count']),
                                      tags=(p['name'], p['birth_date']))
        
        if not self.recommendations:
            messagebox.showinfo("결과", "조건에 맞는 추천 대상이 없습니다.")
    
    def sort_recommendations(self):
        """추천 결과 정렬"""
        if not hasattr(self, 'recommendations'):
            return
        
        sort_by = self.sort_var.get()
        
        if sort_by == 'last_visit':
            self.recommendations.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        else:
            self.recommendations.sort(key=lambda x: x['visit_count'], reverse=True)
        
        self.display_recommendations()
    
    def show_recommend_detail(self, event):
        """추천 목록에서 상세보기"""
        selection = self.recommend_tree.selection()
        if not selection:
            return
        
        tags = self.recommend_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_window(tags[0], tags[1])
    
    def show_detail_window(self, name, birth_date):
        """참가자 상세 정보 팝업"""
        detail = db.get_participant_detail(name, birth_date)
        
        window = tk.Toplevel(self.root)
        window.title(f"{name} 상세 정보")
        window.geometry("500x600")
        
        # 기본 정보
        info_frame = ttk.LabelFrame(window, text="기본 정보")
        info_frame.pack(fill='x', padx=10, pady=10)
        
        birth_year = int(birth_date[:4])
        age = datetime.now().year - birth_year + 1
        
        info_text = f"""
이름: {detail['name']}
성별: {detail['gender']}
나이: {age}세 ({birth_year})
직업: {detail['job']}
MBTI: {detail['mbti']}
전화번호: {detail['phone']}
사는곳: {detail['location'] or '미기입'}
등록경로: {detail['signup_route'] or '미기입'}
첫 방문: {detail['first_visit_date']}
총 방문횟수: {detail['visit_count']}회
        """
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(padx=10, pady=10)
        
        # 자기소개
        intro_frame = ttk.LabelFrame(window, text="자기소개")
        intro_frame.pack(fill='x', padx=10, pady=5)
        
        intro_text = tk.Text(intro_frame, height=3)
        intro_text.pack(fill='both', expand=True, padx=5, pady=5)
        intro_text.insert('1.0', detail['intro'] or '-')
        intro_text.config(state='disabled')
        
        # 매칭 이력
        history_frame = ttk.LabelFrame(window, text="매칭 이력")
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        history_text = tk.Text(history_frame, height=10)
        history_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        for visit in detail['visit_history']:
            history_text.insert('end', f"📅 {visit['session_date']}\n")
            history_text.insert('end', f"   주제: {visit['theme']}\n")
            
            if visit['met_people']:
                people = ', '.join([f"{p['name']}({p['gender']})" for p in visit['met_people']])
                history_text.insert('end', f"   만난 사람: {people}\n")
            
            history_text.insert('end', "\n")
        
        history_text.config(state='disabled')
        
        # 메모
        memo_frame = ttk.LabelFrame(window, text="메모")
        memo_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        memo_text = tk.Text(memo_frame, height=5)
        memo_text.pack(fill='both', expand=True, padx=5, pady=5)
        memo_text.insert('1.0', detail['memo'] or '')
        
        def save_memo():
            new_memo = memo_text.get('1.0', 'end-1c')
            db.update_participant_memo(name, birth_date, new_memo)
            messagebox.showinfo("저장", "메모가 저장되었습니다!")
        
        ttk.Button(memo_frame, text="메모 저장", command=save_memo).pack(pady=5)


def main():
    root = tk.Tk()
    app = MakeToastApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()