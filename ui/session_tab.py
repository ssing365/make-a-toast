"""세션(회차) 탭 관련 기능"""
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import database as db


class SessionTab:
    """회차 관리 탭"""
    
    def __init__(self, parent, on_session_changed=None, on_data_changed=None):
        self.parent = parent
        self.on_session_changed = on_session_changed
        self.on_data_changed = on_data_changed  # 참가자 추가/삭제 시 호출될 콜백
        self.current_session_id = None
        
        # UI 컴포넌트
        self.session_combo = None
        self.session_info_label = None
        self.male_tree = None
        self.female_tree = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """세션 탭 UI 생성"""
        # 상단: 회차 선택
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="회차 선택:").pack(side=LEFT, padx=5)
        
        self.session_combo = ttk.Combobox(top_frame, width=60, state='readonly')
        self.session_combo.pack(side=LEFT, padx=5)
        self.session_combo.bind('<<ComboboxSelected>>', self.on_session_selected)
        
        ttk.Button(top_frame, text="새 회차 생성",
                  command=self.create_new_session).pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="회차 삭제", bootstyle="danger-outline",
                  command=self.delete_session).pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="엑셀 임포트", 
                  command=self.import_excel).pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="새로고침",
                  command=self.refresh_sessions).pack(side=LEFT, padx=5)
        
        # 중단: 회차 정보
        info_frame = ttk.Labelframe(self.parent, text="회차 정보")
        info_frame.pack(fill=X, padx=10, pady=5)
        
        self.session_info_label = ttk.Label(info_frame, text="회차를 선택해주세요")
        self.session_info_label.pack(padx=10, pady=10)
        
        # 하단: 참가자 목록 (남녀 분리)
        list_frame = ttk.Labelframe(self.parent, text="참가자 목록")
        list_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # 좌우 분할 (높이 고정: 약 280px)
        left_frame = ttk.Frame(list_frame, height=350)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        left_frame.pack_propagate(False)  # 높이 고정
        
        right_frame = ttk.Frame(list_frame, height=350)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        right_frame.pack_propagate(False)  # 높이 고정
        
        # 왼쪽: 남자
        male_label_frame = ttk.Labelframe(left_frame, text="남자 참가자")
        male_label_frame.pack(fill=BOTH, expand=False, padx=0, pady=0)
        
        columns = ('name', 'birth_date', 'job', 'mbti', 'phone', 'location', 'signup_route')
        self.male_tree = ttk.Treeview(male_label_frame, columns=columns, show='headings', height=8, bootstyle="primary")
        
        self.male_tree.heading('name', text='이름')
        self.male_tree.heading('birth_date', text='출생년도')
        self.male_tree.heading('job', text='직업')
        self.male_tree.heading('mbti', text='MBTI')
        self.male_tree.heading('phone', text='전화번호')
        self.male_tree.heading('location', text='사는곳')
        self.male_tree.heading('signup_route', text='등록경로')
        
        self.male_tree.column('name', width=50)
        self.male_tree.column('birth_date', width=40)
        self.male_tree.column('job', width=100)
        self.male_tree.column('mbti', width=50)
        self.male_tree.column('phone', width=100)
        self.male_tree.column('location', width=80)
        self.male_tree.column('signup_route', width=80)
        
        self.male_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=0, pady=0)
        
        # Scrollbar는 필요할 때만 표시
        male_scrollbar = ttk.Scrollbar(male_label_frame, orient=VERTICAL, command=self.male_tree.yview)
        self.male_tree.configure(yscrollcommand=male_scrollbar.set)
        male_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.male_tree.bind('<Double-1>', self.on_male_participant_double_click)
        self.male_tree.bind('<Button-3>', lambda e: self.show_participant_context_menu(e, 'M'))
        
        # 남자 참가자 추가 버튼 (트리 아래에 배치)
        male_button_frame = ttk.Frame(left_frame)
        male_button_frame.pack(fill=X, padx=0, pady=5)
        ttk.Button(male_button_frame, text="남자 참가자 추가",
                  command=lambda: self.add_participant_to_session('M')).pack()
        
        # 오른쪽: 여자
        female_label_frame = ttk.Labelframe(right_frame, text="여자 참가자")
        female_label_frame.pack(fill=BOTH, expand=False, padx=0, pady=0)
        
        self.female_tree = ttk.Treeview(female_label_frame, columns=columns, show='headings', height=8, bootstyle="primary")
        
        self.female_tree.heading('name', text='이름')
        self.female_tree.heading('birth_date', text='출생년도')
        self.female_tree.heading('job', text='직업')
        self.female_tree.heading('mbti', text='MBTI')
        self.female_tree.heading('phone', text='전화번호')
        self.female_tree.heading('location', text='사는곳')
        self.female_tree.heading('signup_route', text='등록경로')
        
        self.female_tree.column('name', width=50)
        self.female_tree.column('birth_date', width=40)
        self.female_tree.column('job', width=100)
        self.female_tree.column('mbti', width=50)
        self.female_tree.column('phone', width=100)
        self.female_tree.column('location', width=80)
        self.female_tree.column('signup_route', width=80)
        
        self.female_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=0, pady=0)
        
        # Scrollbar는 필요할 때만 표시
        female_scrollbar = ttk.Scrollbar(female_label_frame, orient=VERTICAL, command=self.female_tree.yview)
        self.female_tree.configure(yscrollcommand=female_scrollbar.set)
        female_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.female_tree.bind('<Double-1>', self.on_female_participant_double_click)
        self.female_tree.bind('<Button-3>', lambda e: self.show_participant_context_menu(e, 'F'))
        
        # 여자 참가자 추가 버튼 (트리 아래에 배치)
        female_button_frame = ttk.Frame(right_frame)
        female_button_frame.pack(fill=X, padx=0, pady=5)
        ttk.Button(female_button_frame, text="여자 참가자 추가",
                  command=lambda: self.add_participant_to_session('F')).pack()
        
        # 중복 체크 버튼 (하단 중앙에 별도 프레임으로)
        check_frame = ttk.Frame(self.parent)
        check_frame.pack(side='bottom', pady=10)
        
        ttk.Button(check_frame, text="🔍 중복 체크", bootstyle=WARNING,
                  command=self.check_duplicates, width=20).pack()
        
        # 초기 데이터 로드
        self.refresh_sessions()
    
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
        
        if self.on_session_changed:
            self.on_session_changed(self.current_session_id)
    
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
            detail = db.get_participant_detail(p['name'], p['birth_date'])
            memo_indicator = "▲" if detail.get('memo') else ""
            name_display = f"{p['name']}{memo_indicator}"
            
            values = (name_display, birth_year, p['job'], p['mbti'], p['phone'], 
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
        dialog = tk.Toplevel(self.parent)
        dialog.title("새 회차 생성")
        dialog.geometry("600x800")
        
        ttk.Label(dialog, text="날짜 (YYYY-MM-DD):").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.grid(row=0, column=1, padx=10, pady=10)
        date_entry.insert(0, "2025-12-27")
        
        ttk.Label(dialog, text="시간대:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        time_entry = ttk.Entry(dialog, width=30)
        time_entry.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="주제:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        theme_combo = ttk.Combobox(dialog, values=['운동 좋아하는 사람들', 'MBTI I들의 모임', 'MBTI E들의 모임', '결혼', '기타'], state='readonly', width=28)
        theme_combo.grid(row=2, column=1, padx=10, pady=10)
        theme_combo.current(0)
        
        ttk.Label(dialog, text="HOST:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        host_entry = ttk.Entry(dialog, width=30)
        host_entry.grid(row=3, column=1, padx=10, pady=10)
        
        def save_session():
            try:
                session_id = db.create_session(
                    date_entry.get(),
                    time_entry.get(),
                    theme_combo.get(),
                    host_entry.get()
                )
                messagebox.showinfo("성공", "회차가 생성되었습니다!")
                dialog.destroy()
                self.refresh_sessions()
            except Exception as e:
                messagebox.showerror("오류", f"회차 생성 실패: {e}")
        
        ttk.Button(dialog, text="생성", command=save_session, bootstyle=SUCCESS).grid(row=4, column=0, 
                                                                columnspan=2, pady=20)
    
    def add_participant_to_session(self, gender):
        """현재 회차에 참가자 추가"""
        from .dialogs import AddParticipantDialog
        
        if not self.current_session_id:
            messagebox.showwarning("경고", "회차를 먼저 선택해주세요!")
            return
        
        dialog = AddParticipantDialog(self.parent, gender, self.current_session_id)
        self.parent.wait_window(dialog.window)
        self.load_session_participants()
        
        # 다른 탭 업데이트
        if self.on_data_changed:
            self.on_data_changed()
    
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
                db.import_excel_file(file_path)
                messagebox.showinfo("완료", "엑셀 임포트가 완료되었습니다!")
                self.refresh_sessions()
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
            menu = tk.Menu(self.parent, tearoff=0)
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
                
                # 다른 탭 업데이트
                if self.on_data_changed:
                    self.on_data_changed()
            except Exception as e:
                messagebox.showerror("오류", f"제거 실패: {e}")
    
    def show_detail_from_item(self, tree, item):
        """트리 아이템에서 상세 정보 표시"""
        from .dialogs import ParticipantDetailWindow
        
        tags = tree.item(item, 'tags')
        if len(tags) >= 2:
            ParticipantDetailWindow(self.parent, tags[0], tags[1])
    
    def on_male_participant_double_click(self, event):
        """남자 참가자 더블클릭 시 상세보기"""
        selection = self.male_tree.selection()
        if not selection:
            return
        
        tags = self.male_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_from_item(self.male_tree, selection[0])
    
    def on_female_participant_double_click(self, event):
        """여자 참가자 더블클릭 시 상세보기"""
        selection = self.female_tree.selection()
        if not selection:
            return
        
        tags = self.female_tree.item(selection[0], 'tags')
        if len(tags) >= 2:
            self.show_detail_from_item(self.female_tree, selection[0])
