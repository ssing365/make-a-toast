"""추천 탭 관련 기능"""
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime
import database as db


class RecommendTab:
    """추천 탭"""
    
    def __init__(self, parent, get_sessions_callback=None):
        self.parent = parent
        self.get_sessions_callback = get_sessions_callback
        self.recommendations = []
        
        # UI 컴포넌트
        self.recommend_session_combo = None
        self.gender_var = None
        self.birth_year_min_entry = None
        self.birth_year_max_entry = None
        self.mbti_entry = None
        self.sort_var = None
        self.recommend_tree = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """추천 탭 UI 생성"""
        # 필터 패널
        filter_frame = ttk.LabelFrame(self.parent, text="필터 조건")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(row1, text="회차:").pack(side='left', padx=5)
        self.recommend_session_combo = ttk.Combobox(row1, width=60, state='readonly')
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
        sort_frame = ttk.Frame(self.parent)
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
        self.recommend_tree = ttk.Treeview(self.parent, 
                                          columns=columns, show='headings', bootstyle="primary")
        
        self.recommend_tree.heading('name', text='이름')
        self.recommend_tree.heading('birth_date', text='출생년도')
        self.recommend_tree.heading('job', text='직업')
        self.recommend_tree.heading('mbti', text='MBTI')
        self.recommend_tree.heading('phone', text='전화번호')
        self.recommend_tree.heading('location', text='사는곳')
        self.recommend_tree.heading('signup_route', text='등록경로')
        self.recommend_tree.heading('last_visit', text='최근방문')
        self.recommend_tree.heading('visit_count', text='방문횟수')
        
        self.recommend_tree.column('name', width=50)
        self.recommend_tree.column('birth_date', width=40)
        self.recommend_tree.column('job', width=90)
        self.recommend_tree.column('mbti', width=50)
        self.recommend_tree.column('phone', width=100)
        self.recommend_tree.column('location', width=80)
        self.recommend_tree.column('signup_route', width=50)
        self.recommend_tree.column('last_visit', width=80)
        self.recommend_tree.column('visit_count', width=70)
        
        scrollbar = ttk.Scrollbar(self.parent, orient='vertical', 
                                 command=self.recommend_tree.yview)
        self.recommend_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recommend_tree.pack(side='left', fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 더블클릭 상세보기
        self.recommend_tree.bind('<Double-1>', self.show_recommend_detail)
        
        # 회차 목록 로드
        self.refresh_recommend_sessions()
    
    def refresh_recommend_sessions(self):
        """추천 탭 회차 목록 새로고침"""
        sessions = db.get_all_sessions()
        session_list = [f"{s['session_date']} {s['session_time']} - {s['theme']}" 
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
            detail = db.get_participant_detail(p['name'], p['birth_date'])
            memo_indicator = "▲" if detail.get('memo') else ""
            name_display = f"{p['name']}{memo_indicator}"
            
            self.recommend_tree.insert('', 'end',
                                      values=(name_display, birth_year, p['job'], p['mbti'], p['phone'],
                                             p['location'] or '', p['signup_route'] or '', 
                                             p['last_visit'] or '-', p['visit_count']),
                                      tags=(p['name'], p['birth_date']))
        
        if not self.recommendations:
            messagebox.showinfo("결과", "조건에 맞는 추천 대상이 없습니다.")
    
    def sort_recommendations(self):
        """추천 결과 정렬"""
        if not self.recommendations:
            return
        
        sort_by = self.sort_var.get()
        
        if sort_by == 'last_visit':
            self.recommendations.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        else:
            self.recommendations.sort(key=lambda x: x['visit_count'], reverse=True)
        
        self.display_recommendations()
    
    def show_recommend_detail(self, event):
        """추천 목록에서 상세보기"""
        from .dialogs import ParticipantDetailWindow
        
        selection = self.recommend_tree.selection()
        if not selection:
            return
        
        tags = self.recommend_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            ParticipantDetailWindow(self.parent, tags[0], tags[1])
