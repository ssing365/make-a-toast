"""메인 애플리케이션 클래스"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .session_tab import SessionTab
from .participant_tab import ParticipantTab
from .recommend_tab import RecommendTab


class MakeToastApp:
    """메이크어토스트 메인 애플리케이션"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Make a Toast")
        self.root.geometry("1800x1000")
        
        # 탭 생성
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 탭 2: 참가자 DB (먼저 생성 - 나중에 추가)
        self.participant_frame = ttk.Frame(self.notebook)
        self.participant_tab = ParticipantTab(self.participant_frame)
        
        # 탭 3: 추천 (먼저 생성 - 나중에 추가)
        self.recommend_frame = ttk.Frame(self.notebook)
        self.recommend_tab = RecommendTab(self.recommend_frame)
        
        # 탭 1: 회차 관리 (첫 번째로 추가)
        self.session_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.session_frame, text="회차 관리")
        self.session_tab = SessionTab(
            self.session_frame, 
            on_session_changed=self.on_session_changed,
            on_data_changed=self.on_participant_data_changed
        )
        
        # 나머지 탭들 추가
        self.notebook.add(self.participant_frame, text="참가자 DB")
        self.notebook.add(self.recommend_frame, text="추천")
    
    def on_session_changed(self, session_id):
        """회차가 변경되었을 때 콜백"""
        # 필요시 다른 탭의 상태 업데이트
        self.recommend_tab.refresh_recommend_sessions()
    
    def on_participant_data_changed(self):
        """참가자 데이터 변경 시 모든 탭 업데이트"""
        # 참가자 DB 탭 새로고침
        self.participant_tab.load_all_participants()
        # 추천 탭 회차 목록 새로고침
        self.recommend_tab.refresh_recommend_sessions()
