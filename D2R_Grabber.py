import tkinter as tk
from tkinter import messagebox, ttk
import undetected_chromedriver as uc
import pyperclip
import threading
import time

class D2RTokenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("D2R 토큰 추출기 v1.3")
        self.root.geometry("450x380")
        self.root.resizable(False, False)
        self.driver = None

        self.create_widgets()

    def create_widgets(self):
        # 제목
        tk.Label(self.root, text="디아2 레저렉션 ST 토큰 추출기", 
                 font=("Malgun Gothic", 14, "bold"), pady=15).pack()

        # 지역 선택 프레임
        frame = tk.LabelFrame(self.root, text="서버 지역 선택", padx=10, pady=10)
        frame.pack(padx=20, pady=5, fill="x")

        self.region_var = tk.StringVar(value="kr")
        tk.Radiobutton(frame, text="아시아 (KR)", variable=self.region_var, value="kr").pack(side="left", expand=True)
        tk.Radiobutton(frame, text="북미 (US)", variable=self.region_var, value="us").pack(side="left", expand=True)
        tk.Radiobutton(frame, text="유럽 (EU)", variable=self.region_var, value="eu").pack(side="left", expand=True)

        # 시작 버튼
        self.start_btn = tk.Button(self.root, text="브라우저 열기 및 추출 시작", command=self.start_thread, 
                                   bg="#0078D7", fg="white", font=("Malgun Gothic", 10, "bold"), pady=8)
        self.start_btn.pack(pady=10, fill="x", padx=20)

        # 토큰 표시 영역
        tk.Label(self.root, text="추출된 토큰:", font=("Malgun Gothic", 9)).pack(anchor="w", padx=20)
        
        self.token_entry = tk.Entry(self.root, font=("Consolas", 10), fg="blue")
        self.token_entry.pack(padx=20, pady=5, fill="x")
        self.token_entry.insert(0, "추출 대기 중...")
        self.token_entry.config(state="readonly")

        # 개별 복사 버튼
        self.copy_btn = tk.Button(self.root, text="클립보드에 다시 복사", command=self.manual_copy, state="disabled")
        self.copy_btn.pack(pady=5)

        # 상태 표시바
        self.status_var = tk.StringVar(value="대기 중...")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w").pack(side="bottom", fill="x")

    def focus_window(self):
        """창을 맨 앞으로 가져오고 포커스를 줌"""
        self.root.deiconify() # 최소화되어 있다면 복구
        self.root.attributes('-topmost', True) # 잠시 맨 위로 설정
        self.root.focus_force() # 강제 포커스
        self.root.attributes('-topmost', False) # 맨 위 설정 해제 (다른 창 사용 방해 금지)
        
        # 텍스트 박스 포커스 및 전체 선택
        self.token_entry.config(state="normal")
        self.token_entry.focus_set()
        self.token_entry.selection_range(0, tk.END)
        self.token_entry.config(state="readonly")

    def manual_copy(self):
        token = self.token_entry.get()
        if token and token != "추출 대기 중...":
            pyperclip.copy(token)
            messagebox.showinfo("복사 완료", "토큰이 클립보드에 다시 복사되었습니다.")

    def start_thread(self):
        self.start_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.token_entry.config(state="normal")
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, "로그인 대기 중...")
        self.token_entry.config(state="readonly")
        
        threading.Thread(target=self.extract_token_logic, daemon=True).start()

    def extract_token_logic(self):
        region = self.region_var.get()
        login_url = f"https://{region}.battle.net/login/ko/?externalChallenge=login&app=OSI"
        
        try:
            self.status_var.set(f"[{region.upper()}] 브라우저 실행 중...")
            self.driver = uc.Chrome()
            self.driver.get(login_url)

            token = None
            while True:
                try:
                    current_url = self.driver.current_url
                    if "ST=" in current_url:
                        token = current_url.split("ST=")[1].split("&")[0]
                        break
                    if not self.driver.window_handles: break
                except: break
                time.sleep(0.5)

            if token:
                # 1. 텍스트 박스 업데이트
                self.root.after(0, lambda: self._update_success_ui(token))
                pyperclip.copy(token)
            else:
                self.status_var.set("추출 중단됨.")

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"문제가 발생했습니다:\n{e}"))
        finally:
            self.cleanup_driver()
            self.root.after(0, lambda: self.start_btn.config(state="normal"))

    def _update_success_ui(self, token):
        """추출 성공 시 UI 업데이트 및 포커스 (메인 스레드에서 실행)"""
        self.token_entry.config(state="normal")
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, token)
        self.token_entry.config(state="readonly")
        
        self.copy_btn.config(state="normal")
        self.status_var.set("추출 성공! 토큰이 선택되었습니다.")
        
        # 창 포커스 작업
        self.focus_window()
        messagebox.showinfo("성공", "토큰 추출 완료!\n프로그램 창의 텍스트가 자동 선택되었습니다.")

    def cleanup_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except: pass
            finally: self.driver = None

if __name__ == "__main__":
    root = tk.Tk()
    app = D2RTokenApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup_driver(), root.destroy()))
    root.mainloop()