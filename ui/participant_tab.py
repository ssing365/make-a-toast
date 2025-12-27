"""참가자 DB 탭 관련 기능"""
from tkinter import ttk, messagebox
import database as db


class ParticipantTab:
    """참가자 DB 탭"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # UI 컴포넌트
        self.search_entry = None
        self.participant_male_tree = None
        self.participant_female_tree = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """참가자 DB 탭 UI 생성"""
        # 검색 바
        search_frame = ttk.Frame(self.parent)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(search_frame, text="검색:").pack(side='left', padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        ttk.Button(search_frame, text="검색", 
                  command=self.search_participants).pack(side='left', padx=5)
        ttk.Button(search_frame, text="전체 보기", bootstyle="primary-outline", 
                  command=self.load_all_participants).pack(side='left', padx=5)
        
        # 참가자 리스트 (남녀 분리)
        list_container = ttk.Frame(self.parent)
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
            memo_indicator = "▲" if detail.get('memo') else ""
            name_display = f"{p['name']}{memo_indicator}"
            
            values = (name_display, birth_year, p['job'], p['mbti'], 
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
                memo_indicator = "▲" if detail.get('memo') else ""
                name_display = f"{p['name']}{memo_indicator}"
                
                values = (name_display, birth_year, p['job'], p['mbti'],
                         p['phone'], p['location'] or '', p['signup_route'] or '', detail['visit_count'])
                tags = (p['name'], p['birth_date'])
                
                if p['gender'] == 'M':
                    self.participant_male_tree.insert('', 'end', values=values, tags=tags)
                else:
                    self.participant_female_tree.insert('', 'end', values=values, tags=tags)
    
    def show_participant_db_context_menu(self, event, gender):
        """참가자 DB 탭 우클릭 메뉴"""
        import tkinter as tk
        
        tree = self.participant_male_tree if gender == 'M' else self.participant_female_tree
        
        # 클릭한 아이템 선택
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            
            # 컨텍스트 메뉴 생성
            menu = tk.Menu(self.parent, tearoff=0)
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
        from .dialogs import ParticipantDetailWindow
        
        tags = tree.item(item, 'tags')
        if len(tags) >= 2:
            ParticipantDetailWindow(self.parent, tags[0], tags[1])
    
    def show_participant_detail(self, event):
        """참가자 상세보기 (남녀 트리 모두 지원)"""
        from .dialogs import ParticipantDetailWindow
        
        # 어느 트리에서 클릭했는지 확인
        widget = event.widget
        selection = widget.selection()
        if not selection:
            return
        
        tags = widget.item(selection[0], 'tags')
        if len(tags) >= 2:
            ParticipantDetailWindow(self.parent, tags[0], tags[1])
