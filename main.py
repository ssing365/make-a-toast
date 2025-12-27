"""메이크어토스트 - 메인 진입점"""
import ttkbootstrap as ttk
from ui import MakeToastApp


def main():
    """애플리케이션 시작"""
    root = ttk.Window(themename="minty")
    app = MakeToastApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
