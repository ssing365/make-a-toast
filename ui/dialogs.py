"""다이얼로그 및 팝업 윈도우들"""
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime
from tkcalendar import DateEntry
import database as db


class AddParticipantDialog:
    """참가자 추가 다이얼로그"""
    
    def __init__(self, parent, gender, session_id):
        self.parent = parent
        self.gender = gender
        self.session_id = session_id
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"{'남자' if gender == 'M' else '여자'} 참가자 추가")
        self.window.geometry("600x800")
        
        self.setup_ui()
    
    def setup_ui(self):
        """다이얼로그 UI 생성"""
        # 이름 (필수)
        ttk.Label(self.window, text="이름: ", foreground='red').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_entry = ttk.Entry(self.window, width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 출생년도 (필수)
        ttk.Label(self.window, text="출생년도: ", foreground='red').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.birth_entry = ttk.Entry(self.window, width=30)
        self.birth_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 직업
        ttk.Label(self.window, text="직업:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.job_entry = ttk.Entry(self.window, width=30)
        self.job_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # MBTI
        ttk.Label(self.window, text="MBTI:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.mbti_entry = ttk.Entry(self.window, width=30)
        self.mbti_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # 전화번호
        ttk.Label(self.window, text="전화번호:").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.phone_entry = ttk.Entry(self.window, width=30)
        self.phone_entry.grid(row=4, column=1, padx=10, pady=10)
        
        # 사는곳
        ttk.Label(self.window, text="사는곳:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.location_entry = ttk.Entry(self.window, width=30)
        self.location_entry.grid(row=5, column=1, padx=10, pady=10)
        
        # 등록경로
        ttk.Label(self.window, text="등록경로:").grid(row=6, column=0, padx=10, pady=10, sticky='w')
        self.signup_route_entry = ttk.Entry(self.window, width=30)
        self.signup_route_entry.grid(row=6, column=1, padx=10, pady=10)
        
        ttk.Button(self.window, text="추가", command=self.save_participant).grid(row=7, column=0, 
                                                                    columnspan=2, pady=20)
    
    def save_participant(self):
        """참가자 저장"""
        name = self.name_entry.get().strip()
        birth_year = self.birth_entry.get().strip()
        
        if not name or not birth_year:
            messagebox.showerror("오류", "이름과 출생년도는 필수입니다!")
            return
        
        # 출생년도는 4자리 숫자만 허용
        if not birth_year.isdigit() or len(birth_year) != 4:
            messagebox.showerror("오류", "출생년도는 4자리 숫자만 입력 가능합니다! (예: 2000)")
            return
        
        birth_date = f"{birth_year}-01-01"
        
        try:
            # 참가자 추가
            db.add_participant(
                name=name,
                birth_date=birth_date,
                gender=self.gender,
                job=self.job_entry.get(),
                mbti=self.mbti_entry.get(),
                phone=self.phone_entry.get(),
                location=self.location_entry.get(),
                signup_route=self.signup_route_entry.get(),
                memo=""
            )
            
            # 회차에 참가자 추가
            db.add_attendance(self.session_id, name, birth_date)
            
            messagebox.showinfo("완료", "참가자가 추가되었습니다!")
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("오류", f"추가 실패: {e}")


class ParticipantDetailWindow:
    """참가자 상세 정보 팝업"""
    
    def __init__(self, parent, name, birth_date):
        self.parent = parent
        self.name = name
        self.birth_date = birth_date
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"{name} 상세 정보")
        self.window.geometry("1000x1200")
        
        self.setup_ui()
    
    def setup_ui(self):
        """상세정보 윈도우 UI 생성"""
        detail = db.get_participant_detail(self.name, self.birth_date)
        
        # 기본 정보
        info_frame = ttk.LabelFrame(self.window, text="기본 정보")
        info_frame.pack(fill='x', padx=10, pady=10)
        
        birth_year = int(self.birth_date[:4])
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
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(anchor='nw', fill='x', padx=10, pady=10)
        
        # 자기소개
        intro_frame = ttk.LabelFrame(self.window, text="자기소개")
        intro_frame.pack(fill='x', padx=10, pady=5)
        
        intro_text = tk.Text(intro_frame, height=3)
        intro_text.pack(fill='both', expand=True, padx=5, pady=5)
        intro_text.insert('1.0', detail['intro'] or '-')
        intro_text.config(state='disabled')
        
        # 매칭 이력
        history_frame = ttk.LabelFrame(self.window, text="매칭 이력")
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
        memo_frame = ttk.LabelFrame(self.window, text="메모")
        memo_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.memo_text = tk.Text(memo_frame, height=5)
        self.memo_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 기본 내용이 없다면 placeholder 표시
        if detail['memo']:
            self.memo_text.insert('1.0', detail['memo'])
            self.placeholder_active = False
        else:
            self.memo_text.insert('1.0', "이 참가자에 대해 기록할 사항을 여기 메모하세요")
            self.memo_text.config(fg='gray')
            self.placeholder_active = True
        
        # 메모 입력 시 placeholder 제거
        self.memo_text.bind('<FocusIn>', self.on_memo_focus_in)
        self.memo_text.bind('<FocusOut>', self.on_memo_focus_out)
        
        ttk.Button(memo_frame, text="메모 저장", command=self.save_memo).pack(pady=5)
    
    def save_memo(self):
        """메모 저장"""
        new_memo = self.memo_text.get('1.0', 'end-1c')
        
        # placeholder 텍스트는 저장하지 않음
        if new_memo == "이 참가자에 대해 기록할 사항을 여기 메모하세요":
            new_memo = ""
        
        db.update_participant_memo(self.name, self.birth_date, new_memo)
        messagebox.showinfo("저장", "메모가 저장되었습니다!")
    
    def on_memo_focus_in(self, event):
        """메모 입력창 포커스 시"""
        if self.placeholder_active:
            self.memo_text.delete('1.0', 'end')
            self.memo_text.config(fg='black')
            self.placeholder_active = False
    
    def on_memo_focus_out(self, event):
        """메모 입력창 포커스 해제 시"""
        content = self.memo_text.get('1.0', 'end-1c')
        if not content:
            self.memo_text.insert('1.0', "이 참가자에 대해 기록할 사항을 여기 메모하세요")
            self.memo_text.config(fg='gray')
            self.placeholder_active = True
