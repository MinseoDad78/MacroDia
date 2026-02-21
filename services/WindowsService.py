import sys
import time
import ctypes
import win32gui, win32con , win32api
import win32process
import psutil
import pyautogui

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget, QMessageBox, QInputDialog
)
import win32gui
import win32con
import win32process
import psutil
from services.ImageSearch import  IconDetector
from services.LogService import  LogHandler
class WindowsService:
    """Windows 창 관리 서비스 클래스"""
    logger = LogHandler("WindowsService")
    @staticmethod
    def find_windows_by_process_name(process_name):
        """주어진 프로세스 이름과 연결된 윈도우 핸들 검색"""
        windows = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    if process.name() == process_name:
                        windows.append((hwnd, win32gui.GetWindowText(hwnd)))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        win32gui.EnumWindows(enum_windows_callback, None)
        return windows
    # DPI Aware 설정
    def set_dpi_awareness():
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()  # 시스템 DPI Aware (구형 OS 호환용)
                except Exception:
                    pass  # 실패해도 무시

  # DPI 보정용 함수
    def _get_dpi_scale(hwnd):
            hdc = win32gui.GetDC(hwnd)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            dpi_scale = dpi_x / 96.0  # 기본 DPI 96 기준
            win32gui.ReleaseDC(hwnd, hdc)
            return dpi_scale
    
    
    @staticmethod
    def move_window(hwnd, x, y):
        """윈도우 핸들을 사용해 창 이동"""
        win32gui.SetWindowPos(hwnd, 0, x, y, 0, 0, 1)

    @staticmethod
    def minimize_window(hwnd):
        """윈도우 창 최소화"""
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    @staticmethod
    def _get_window_inf2(hwnd):
        """주어진 윈도우 핸들의 위치 및 크기 정보를 반환"""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y

        return {
            "hwnd": hwnd,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
    
# DPI-aware 윈도우 위치 정보 반환
    def _get_window_info(self, hwnd):
            """DPI 스케일 고려한 윈도우 좌표 및 크기 반환"""
            self.set_dpi_awareness()  # 한 번만 호출해도 됨

            rect = win32gui.GetWindowRect(hwnd)
            dpi_scale = self._get_dpi_scale(hwnd)

            x, y, right, bottom = rect
            width = (right - x) / dpi_scale
            height = (bottom - y) / dpi_scale
            x /= dpi_scale
            y /= dpi_scale

            return {
                "hwnd": hwnd,
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height)
            }
    
    def get_adjusted_window_info(hwnd):
        """창이 속한 모니터 기준으로 보정된 좌표 반환"""
        
        # 1️⃣ 현재 창의 절대 좌표 가져오기
        rect = win32gui.GetWindowRect(hwnd)
        x, y, right, bottom = rect
        width, height = right - x, bottom - y

        # 2️⃣ 창이 위치한 모니터 찾기
        monitor_handle = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        monitor_info = win32api.GetMonitorInfo(monitor_handle)

        # 3️⃣ 모니터의 기준 좌표 가져오기
        monitor_left = monitor_info['Monitor'][0]
        monitor_top = monitor_info['Monitor'][1]

        # 4️⃣ 창 좌표 보정 (모니터 기준 상대 좌표로 변환)
        adjusted_x = x - monitor_left
        adjusted_y = y - monitor_top

        # 5️⃣ 캡처 영역 설정
        capture_region = {
            "hwnd": hwnd,
            "adjusted_x": adjusted_x,
            "adjusted_y": adjusted_y,
            "x" : x,
            "y" : y,
            "width": width,
            "height": height,
            "monitor_index": monitor_handle,  # 창이 속한 모니터 ID
            "monitor_left": monitor_left,
            "monitor_top": monitor_top
        }

        # **출력 로그**
        print("\n🖥️ 현재 창이 속한 모니터 정보:")
        print(f"   ▶ 모니터 핸들: {monitor_handle}")
        print(f"   ▶ 모니터 전체 좌표: {monitor_info['Monitor']} (left, top, right, bottom)")
        print(f"   ▶ 작업 영역: {monitor_info['Work']} (left, top, right, bottom)")
        print(f"   ▶ 주 모니터 여부: {'YES' if monitor_info.get('Flags', 0) == 1 else 'NO'}")
        print(f"\n🖥️ 창 좌표 보정 결과:")
        print(f"   ▶ 원본 창 좌표: (X: {x}, Y: {y}, Width: {width}, Height: {height})")
        print(f"   ▶ 모니터 기준 변환 좌표: (X: {adjusted_x}, Y: {adjusted_y})")
        print(f"   ▶ 캡처 영역 (보정된 값): {capture_region}")

        return capture_region
   
    @staticmethod
    def set_role(hwnd, role):
        """
        주어진 창 핸들에 역할을 설정 (Master/Slave/None)
        Master: 모니터 1 (좌상단)으로 이동
        Slave: 모니터 2 (우상단)으로 이동
        None: 창 최소화
        """
        if role == "Master":
            WindowsService.move_window(hwnd, 0, 0)  # 모니터 1 좌상단
            return "Master 역할로 설정하고 모니터 1에 배치했습니다."
        elif role == "Slave":
            WindowsService.move_window(hwnd, 1920, 0)  # 모니터 2 우상단
            return "Slave 역할로 설정하고 모니터 2에 배치했습니다."
        elif role == "None":
            WindowsService.minimize_window(hwnd)  # 창 최소화
            return "창을 최소화했습니다."
        else:
            raise ValueError(f"유효하지 않은 역할: {role}")


class DiabloManagerApp(QWidget):
    logger = LogHandler("FIND")
    """PyQt5 UI를 사용한 디아블로 창 관리 애플리케이션"""

    def __init__(self):
        super().__init__()
        self.window_roles = {}  # 각 창의 역할을 저장 (hwnd: role)
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Diablo 2 Master-Slave Manager")
        self.setGeometry(300, 300, 500, 300)

        layout = QVBoxLayout()

        # 라벨
        label = QLabel("디아블로 2 창 관리 도구")
        layout.addWidget(label)

        # 창 리스트 표시
        self.window_list_widget = QListWidget()
        layout.addWidget(self.window_list_widget)

        # 역할 선택 콤보박스
        role_layout = QHBoxLayout()
        self.role_selection = QComboBox()
        self.role_selection.addItems(["Master", "Slave", "None"])
        role_layout.addWidget(QLabel("역할 선택:"))
        role_layout.addWidget(self.role_selection)
        layout.addLayout(role_layout)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 창 탐지 버튼
        detect_button = QPushButton("디아블로 2 창 탐지")
        detect_button.clicked.connect(self.detect_windows)
        button_layout.addWidget(detect_button)

        # 역할 설정 및 배치 버튼
        set_button = QPushButton("역할 및 배치 설정")
        set_button.clicked.connect(self.set_roles_and_positions)
        button_layout.addWidget(set_button)

        # 창 정보 출력 버튼
        info_button = QPushButton("창 정보 출력")
        info_button.clicked.connect(self.print_window_info)
        button_layout.addWidget(info_button)

        # 종료 버튼
        exit_button = QPushButton("종료")
        exit_button.clicked.connect(self.close)


        layout.addLayout(button_layout)
        self.setLayout(layout)

        button_layout.addWidget(exit_button)
        self.detect_windows_detail( True)

    def detect_windows(self):
        self.detect_windows_detail(False)

    def detect_windows_detail(self, isInit):
        """디아블로 2 창 탐지 (프로세스 이름 기반)"""
        self.window_list_widget.clear()
        process_name = "D2R.exe"  # 디아블로 2의 실행 파일 이름
        windows = WindowsService.find_windows_by_process_name(process_name)

        if not windows :
            QMessageBox.warning(self, "경고", "디아블로 2 창을 찾을 수 없습니다.")
            return

        for hwnd, title in windows:
            role = self.window_roles.get(hwnd, "None")  # 역할 정보 가져오기 (기본값: None)
            self.window_list_widget.addItem(f"{title} (HWND: {hwnd}) [Role: {role}]")
        if not isInit :
            QMessageBox.information(self, "창 탐지 완료", f"{len(windows)}개의 디아블로 2 창을 탐지했습니다.")

    def set_roles_and_positions(self):
        """사용자가 선택한 창에 역할 지정 및 위치 배치"""
        selected_items = self.window_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "역할을 지정할 창을 선택하세요.")
            return

        selected_text = selected_items[0].text()
        hwnd = int(selected_text.split("(HWND: ")[-1].split(")")[0])  # HWND 추출
        selected_role = self.role_selection.currentText()

        # 역할에 따라 창 배치/최소화
        try:
            message = WindowsService.set_role(hwnd, selected_role)
            self.window_roles[hwnd] = selected_role  # 역할 업데이트
            self.detect_windows()  # 창 목록 갱신
            QMessageBox.information(self, f"{selected_role} 설정 완료", f"창 (HWND: {hwnd}) {message}")
        except ValueError as e:
            QMessageBox.warning(self, "오류", str(e))

    def print_window_info(self):
        """선택된 창의 정보를 출력"""
        selected_items = self.window_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "정보를 출력할 창을 선택하세요.")
            return

        selected_text = selected_items[0].text()
        hwnd = int(selected_text.split("(HWND: ")[-1].split(")")[0])  # HWND 추출

        info = WindowsService.get_adjusted_window_info(hwnd)
        template_path =  "C:\\Dev\\Test\\target.png" # 녹색 십자(+) 템플릿 이미지 "c:\\games\\target.png"  # 탐지할 아이콘 템플릿 이미지 경로

        self.logger.debug(f"창이 위치한 모니터: {info['monitor_index']}")
        self.logger.debug(f"창 좌표 (모니터 기준): X={info['x']}, Y={info['y']}")
        self.logger.debug(f"창 크기: Width={info['width']}, Height={info['height']}")
        #fi = FindImage()
        #fi.capture_screen_and_find_icon(info=info, threshold=0.9, scales=[0.6,0.8,1.0,1.2,1.4,1.6,1.8])

        detector = IconDetector()

        # 화면 캡처 영역 정보
        screen_info = {
            "x": info['x'],  # 캡처 시작 X 좌표
            "y": info['y'],  # 캡처 시작 Y 좌표
            "width": info['width'],  # 캡처 영역 너비
            "height": info['height'],  # 캡처 영역 높이
        }


        win32gui.SetForegroundWindow(hwnd)
        self.logger.info("FOREGROUND WINDOW",hwnd)
        time.sleep(1)
     # 특정 아이콘 탐지 실행
        
        try:
            detector.capture_screen_and_find_icons(screen_info, template_path, threshold=0.5 , scales= [0.5, 0.7, 1.0, 1.3,1.5,1.7,2.0])
        except Exception as e:
            self.logger.error("아이콘 탐지 중 오류가 발생했습니다.",e)
        QMessageBox.information(
            self,
            "창 정보",
            f"HWND: {info['hwnd']}\nX: {info['x']}\nY: {info['y']}\nWidth: {info['width']}\nHeight: {info['height']}"
        )
#self, info, template_path, threshold=0.6, scales=[0.6, 0.8, 1.0, 1.2]):