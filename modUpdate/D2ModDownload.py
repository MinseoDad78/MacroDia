import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from googleapiclient.discovery import build
import zipfile
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import D2Key
import json
import time
import os
import sys

API_KEY = D2Key.API_KEY
FOLDER_ID = '1LyN7qFHUcljVEQKzmlaEZGVOgN3Nuz7b' # 최상위 폴더 ID

# ==========================================
# 디아블로 2 경로 자동 탐색 로직
# ==========================================
def get_d2_mods_path():
    config_path = os.path.join(os.getenv('APPDATA', ''), 'Battle.net', 'Battle.net.config')
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        raw_path = config_data.get("Client", {}).get("Install", {}).get("DefaultInstallPath", "")
        if not raw_path:
            return None
        base_game_path = os.path.join(raw_path.replace("\\/", "\\"), "Diablo II Resurrected")
        mods_path = os.path.join(base_game_path, "mods")
        os.makedirs(mods_path, exist_ok=True)
        return mods_path
    except Exception:
        return None

# ==========================================
# 기본 로직 (목록 불러오기 등)
# ==========================================
def fetch_and_display():
    status_var.set("모드 목록을 불러오는 중입니다...")
    root.update_idletasks()
    for item in tree.get_children():
        tree.delete(item)
    try:
        service = build('drive', 'v3', developerKey=API_KEY)
        query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, pageSize=100, fields="nextPageToken, files(id, name)", orderBy="name").execute()
        items = results.get('files', [])
        if not items:
            status_var.set("해당 위치에 모드가 없습니다.")
            return
        for item in items:
            if item.get('name').lower() == 'index':
                continue
            tree.insert('', 'end', values=(item.get('name'), '⚔️ 모드', item.get('id')))
        status_var.set(f"조회 완료: 총 {len(items)-1 if any(i.get('name').lower()=='index' for i in items) else len(items)}개의 모드를 찾았습니다.")
    except Exception as e:
        status_var.set("조회 오류 발생")
        messagebox.showerror("오류", f"데이터를 가져오는 중 문제가 발생했습니다.\n\n{e}")

def get_all_files_recursive(service, folder_id, current_path=""):
    items = []
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        for attempt in range(5):
            try:
                results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)", pageSize=100, pageToken=page_token).execute()
                break
            except Exception:
                time.sleep(2 ** attempt)
        for item in results.get('files', []):
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                sub_path = f"{current_path}{item['name']}/"
                items.extend(get_all_files_recursive(service, item['id'], sub_path))
            else:
                items.append({
                    "id": item['id'],
                    "zip_path": f"{current_path}{item['name']}",
                    "mimeType": item['mimeType']
                })
        page_token = results.get('nextPageToken', None)
        if not page_token:
            break
    return items

# ==========================================
# 전체 인덱스 로컬 생성 (관리자 전용)
# ==========================================
def generate_all_indexes():
    items = tree.get_children()
    if not items:
        messagebox.showwarning("알림", "먼저 [1. 모드 목록 불러오기]를 눌러 목록을 띄워주세요.")
        return
    if not messagebox.askyesno("확인", f"총 {len(items)}개 디렉토리의 인덱스를 내 PC에 생성하시겠습니까?\n(시간이 다소 소요될 수 있습니다.)"):
        return
    threading.Thread(target=process_generate_indexes_bg, args=(items,), daemon=True).start()

def process_generate_indexes_bg(tree_items):
    try:
        service = build('drive', 'v3', developerKey=API_KEY)
        total = len(tree_items)
        for index, item_id in enumerate(tree_items, 1):
            item_values = tree.item(item_id)['values']
            folder_name = item_values[0]
            folder_id = item_values[2]
            
            root.after(0, lambda n=folder_name, i=index, t=total: status_var.set(f"[{n}] 정밀 스캔 중... ({i}/{t})"))
            all_files = get_all_files_recursive(service, folder_id)
            filtered_files = [f for f in all_files if not f['zip_path'].endswith('_index.json')]
            
            filename = f"{folder_name}_index.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_files, f, ensure_ascii=False, indent=4)
                
        root.after(0, lambda: status_var.set("전체 인덱스 생성 완료!"))
        root.after(0, lambda: messagebox.showinfo("완료", "모든 인덱스 파일이 프로그램이 있는 폴더에 생성되었습니다.\n\n구글 드라이브의 [index] 폴더 안에 모두 업로드해주세요."))
    except Exception as e:
        root.after(0, lambda: status_var.set("인덱스 생성 실패"))
        root.after(0, lambda e=e: messagebox.showerror("오류", f"인덱스 생성 중 오류가 발생했습니다.\n\n{e}"))

# ==========================================
# 💡 다중 선택 및 순차 다운로드 로직
# ==========================================
def download_as_zip():
    selected_items = tree.selection() # 여러 개 선택한 리스트를 가져옵니다.
    if not selected_items:
        messagebox.showwarning("선택 필요", "먼저 설치할 모드를 하나 이상 선택해 주세요.\n(Shift나 Ctrl 키를 누르고 클릭하면 다중 선택이 가능합니다)")
        return
    
    mods_path = get_d2_mods_path()
    if mods_path:
        extract_path = mods_path
    else:
        messagebox.showwarning("경로 탐색 실패", "디아블로 2 설치 경로를 자동으로 찾을 수 없습니다.\n직접 저장할 위치(mods 폴더)를 선택해 주세요.")
        extract_path = filedialog.askdirectory(title="mods 폴더 선택")
        if not extract_path:
            return
            
    # 여러 개의 모드를 순서대로 처리하기 위해 리스트 전체를 넘깁니다.
    threading.Thread(target=process_download_bg, args=(selected_items, extract_path), daemon=True).start()

def process_download_bg(selected_items, extract_path):
    try:
        service = build('drive', 'v3', developerKey=API_KEY)
        total_mods = len(selected_items)
        
        # 선택된 모드들을 순서대로 루프(Loop) 돕니다.
        for mod_idx, item_id in enumerate(selected_items, 1):
            item_values = tree.item(item_id)['values']
            folder_name = item_values[0]
            folder_id = item_values[2]
            
            save_path = os.path.join(extract_path, f"{folder_name}.zip")
            all_files = []
            index_filename = f"{folder_name}_index.json"
            
            root.after(0, lambda n=folder_name, c=mod_idx, t=total_mods: status_var.set(f"[{c}/{t}] [{n}] 설치 준비 중..."))
            
            query_idx_folder = f"'{FOLDER_ID}' in parents and name='index' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            res_idx = service.files().list(q=query_idx_folder, fields="files(id)", pageSize=1).execute()
            idx_folders = res_idx.get('files', [])
            
            index_found = False
            if idx_folders:
                index_folder_id = idx_folders[0]['id']
                query_file = f"'{index_folder_id}' in parents and name='{index_filename}' and trashed=false"
                res_file = service.files().list(q=query_file, fields="files(id)", pageSize=1).execute()
                idx_files = res_file.get('files', [])
                
                if idx_files:
                    index_found = True
                    index_id = idx_files[0]['id']
                    index_url = f"https://drive.google.com/uc?export=download&id={index_id}"
                    response = requests.get(index_url)
                    if response.status_code == 200:
                        all_files = json.loads(response.content)

            if not index_found:
                root.after(0, lambda n=folder_name: status_var.set(f"[{n}] 인덱스 없음. 직접 탐색 중(시간 소요)..."))
                all_files = get_all_files_recursive(service, folder_id)
                
            download_targets = [f for f in all_files if not f.get('mimeType', '').startswith('application/vnd.google-apps.')]
            
            if not download_targets:
                continue

            total_files = len(download_targets)
            downloaded_count = 0
            zip_lock = threading.Lock()

            def download_single_file(f, zipf):
                f_id = f['id']
                zip_path = f"{folder_name}/{f['zip_path']}"
                download_url = f"https://drive.google.com/uc?export=download&id={f_id}"
                response = requests.get(download_url)
                if response.status_code == 200:
                    with zip_lock:
                        zipf.writestr(zip_path, response.content)
                return zip_path

            root.after(0, lambda n=folder_name, c=mod_idx, t=total_mods: status_var.set(f"[{c}/{t}] [{n}] 고속 다운로드 시작..."))

            # 임시 ZIP 생성
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                with ThreadPoolExecutor(max_workers=30) as executor:
                    futures = {executor.submit(download_single_file, f, zipf): f for f in download_targets}
                    for future in as_completed(futures):
                        downloaded_count += 1
                        root.after(0, lambda n=folder_name, d=downloaded_count, tf=total_files: status_var.set(f"[{n}] 다운로드 중... ({d}/{tf})"))
                    
            # 압축 풀기
            root.after(0, lambda n=folder_name: status_var.set(f"[{n}] 게임 폴더에 압축 해제 중..."))
            with zipfile.ZipFile(save_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                
            # 임시 파일 청소
            try:
                os.remove(save_path)
            except Exception:
                pass
                
        # 큐(Queue) 전체 순회 완료
        root.after(0, lambda: status_var.set("모든 선택 모드 자동 설치 완료!"))
        root.after(0, lambda: messagebox.showinfo("설치 완료", f"선택하신 총 {total_mods}개의 모드가 성공적으로 설치되었습니다!"))

    except Exception as e:
        root.after(0, lambda: status_var.set("설치 실패"))
        root.after(0, lambda e=e: messagebox.showerror("오류", f"설치 진행 중 오류가 발생했습니다.\n\n{e}"))

# ==========================================
# UI 화면 구성 및 인자(Argument) 체크
# ==========================================
root = tk.Tk()
root.title("구글 드라이브 D2R 모드 자동 설치기")
root.geometry("750x450")

top_frame = tk.Frame(root)
top_frame.pack(pady=10, fill=tk.X, padx=15)

fetch_btn = tk.Button(top_frame, text="1. 모드 목록 불러오기", command=fetch_and_display, width=18, height=2)
fetch_btn.pack(side=tk.LEFT, padx=(0, 5))

download_btn = tk.Button(top_frame, text="2. 선택 모드 자동 설치", command=download_as_zip, width=20, height=2, bg="#4CAF50", fg="white", font=("", 9, "bold"))
download_btn.pack(side=tk.LEFT, padx=(0, 5))

# 💡 명령어 인자값을 확인하여 'admin' 키워드가 있을 때만 버튼을 렌더링합니다.
is_admin = len(sys.argv) > 1 and sys.argv[1].lower() == 'admin'

index_btn = tk.Button(top_frame, text="3. 전체 인덱스 로컬 생성", command=generate_all_indexes, width=22, height=2, bg="#333333", fg="white")
if is_admin:
    index_btn.pack(side=tk.LEFT)

status_var = tk.StringVar()
status_var.set("버튼을 눌러 조회를 시작하세요.")
status_label = tk.Label(top_frame, textvariable=status_var, fg="#555555")
status_label.pack(side=tk.LEFT, padx=15)

bottom_frame = tk.Frame(root)
bottom_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

scrollbar = ttk.Scrollbar(bottom_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

columns = ("Name", "Type", "ID")
# 다중 선택이 가능하도록 selectmode='extended' 명시 (기본값이긴 하지만 명확하게)
tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set, selectmode="extended")
tree.heading("Name", text="모드 이름")
tree.heading("Type", text="유형")
tree.column("Name", width=500, anchor=tk.W)
tree.column("Type", width=100, anchor=tk.CENTER)
tree.column("ID", width=0, stretch=tk.NO)
tree["displaycolumns"] = ("Name", "Type")
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=tree.yview)

root.mainloop()