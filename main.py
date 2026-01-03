"""메이크어토스트 - 메인 진입점"""
import ttkbootstrap as ttk
from ui import MakeToastApp
import database as db


def main():
    """애플리케이션 시작"""
    # 데이터베이스 초기화 (테이블이 없으면 생성)
    db.init_db()
    
    root = ttk.Window(themename="cosmo")
    app = MakeToastApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
