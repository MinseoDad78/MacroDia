import tkinter as tk
from tkinter import messagebox
import os
import json
import subprocess

class D2RManagerWithLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("D2R 모드 자동 설정 & 실행")
        self.root.geometry("480x580")

        # 경로 및 파일 이름 설정
        self.config_path = os.path.join(os.getenv('APPDATA'), 'Battle.net', 'Battle.net.config')
        self.btnet_exe_name = "Battle.net.exe"
        self.launcher_name = "Diablo II Resurrected Launcher.exe"
        self.base_game_path = ""
        self.mods_path = ""
        self.mods_data = [] # (폴더명, 유효성여부) 저장용

        # UI 구성
        self.status_label = tk.Label(root, text="경로 탐색 중...", fg="blue", pady=10)
        self.status_label.pack()

        self.listbox = tk.Listbox(root, width=60, height=15, font=("Malgun Gothic", 10))
        self.listbox.pack(pady=10, padx=15)

        self.apply_btn = tk.Button(root, text="설정 적용 및 배틀넷 실행", 
                                  command=self.check_and_apply, state=tk.DISABLED, 
                                  bg="#0078d7", fg="white", height=2)
        self.apply_btn.pack(pady=10, fill=tk.X, padx=50)

        # 자동 탐색 실행
        self.auto_discover()

    def apply_strikethrough(self, text):
        """텍스트에 유니코드 취소선을 입히는 함수"""
        return ''.join([u'{}\u0336'.format(c) for c in text])

    def auto_discover(self):
        """설정 파일에서 게임 경로를 찾고 모드 목록을 로드함"""
        if not os.path.exists(self.config_path):
            self.status_label.config(text="Battle.net.config를 찾을 수 없습니다.", fg="red")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 설치 경로 추출 및 정규화
            raw_path = config_data.get("Client", {}).get("Install", {}).get("DefaultInstallPath", "")
            if not raw_path:
                raise ValueError("설치 경로 정보를 찾을 수 없습니다.")

            self.base_game_path = os.path.join(raw_path.replace("\\/", "\\"), "Diablo II Resurrected")
            self.mods_path = os.path.join(self.base_game_path, "mods")

            if os.path.exists(self.mods_path):
                self.load_mod_list()
                self.status_label.config(text=f"탐색 성공: {self.base_game_path}", fg="green")
                self.apply_btn.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="mods 폴더를 찾을 수 없습니다.", fg="red")
                
        except Exception as e:
            self.status_label.config(text=f"오류: {str(e)}", fg="red")

    def load_mod_list(self):
        """유효성 검사를 포함하여 모드 리스트 로드"""
        self.listbox.delete(0, tk.END)
        self.mods_data = []
        
        # 하위 폴더 목록 가져오기
        subfolders = [f for f in os.listdir(self.mods_path) if os.path.isdir(os.path.join(self.mods_path, f))]
        
        for folder in subfolders:
            mod_folder_path = os.path.join(self.mods_path, folder)
            # 유효성 체크: 폴더명과 동일한 .mpq 파일 혹은 폴더가 존재하는지 확인
            is_valid = os.path.exists(os.path.join(mod_folder_path, f"{folder}.mpq"))
            
            self.mods_data.append((folder, is_valid))

            if is_valid:
                self.listbox.insert(tk.END, f"  {folder}")
            else:
                # 유효하지 않으면 취소선 적용 및 색상 변경
                display_text = f"  {self.apply_strikethrough(folder)} (구성 요소 부족)"
                self.listbox.insert(tk.END, display_text)
                self.listbox.itemconfig(tk.END, {'fg': 'gray'})

    def is_battlenet_running(self):
        try:
            output = subprocess.check_output('tasklist', shell=True).decode('cp949')
            return self.btnet_exe_name.lower() in output.lower()
        except: return False

    def check_and_apply(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("알림", "모드를 선택해주세요.")
            return

        # 선택한 항목의 유효성 재확인
        folder_name, is_valid = self.mods_data[selection[0]]
        if not is_valid:
            messagebox.showerror("오류", f"'{folder_name}'은 유효한 모드 구조가 아닙니다.\n내부에 {folder_name}.mpq 파일이나 폴더가 필요합니다.")
            return

        if self.is_battlenet_running():
            if messagebox.askyesno("확인", "배틀넷이 실행 중입니다. 종료 후 적용할까요?"):
                os.system(f"taskkill /f /im {self.btnet_exe_name}")
            else: return

        if self.apply_config(folder_name):
            self.launch_game()

    def apply_config(self, selected_mod):
        new_args = f"-mod {selected_mod} -txt"

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # D2R의 설정 키인 'osi' 또는 'osiris' 확인 (버전에 따라 다를 수 있음)
            game_key = 'osi' if 'osi' in data.get('Games', {}) else 'osiris'
            
            if 'Games' not in data: data['Games'] = {}
            if game_key not in data['Games']: data['Games'][game_key] = {}
            
            data['Games'][game_key]['AdditionalLaunchArguments'] = new_args
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {e}")
            return False

    def launch_game(self):
        launcher_path = os.path.join(self.base_game_path, self.launcher_name)
        if os.path.exists(launcher_path):
            os.startfile(launcher_path)
            self.root.after(1000, self.root.destroy)
        else:
            messagebox.showerror("실행 실패", f"런처를 찾을 수 없습니다:\n{launcher_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = D2RManagerWithLauncher(root)
    root.mainloop()