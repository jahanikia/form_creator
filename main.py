# main.py
import sys
sys.dont_write_bytecode = True

import traceback
import customtkinter as ctk
from src.views.main_view import MainView


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = MainView()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 خداحافظ!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {type(e).__name__}: {e}")
        traceback.print_exc()
        input("\nبرای بستن Enter بزن...")
        sys.exit(1)