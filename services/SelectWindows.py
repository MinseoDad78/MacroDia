import sys
import win32gui
import win32process
import psutil
import pyautogui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget, QMessageBox, QInputDialog
)


class DiabloWindowManager:
    """디아블로 창 관리 클래스"""

    @staticmethod
    def find_windows_by_process_name(process_name):
        """주어진 프로세스 이름과 연결된 윈도우 핸들 검색"""
        windows = []

        def enum_windows_callback(hwnd, process_name):
            """윈도우 핸들을 열거하며 프로세스 이름으로 필터링"""
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    if process.name() == process_name:
                        windows.append((hwnd, win32gui.GetWindowText(hwnd)))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        win32gui.EnumWindows(enum_windows_callback, process_name)
        return windows

    @staticmethod
    def move_window(hwnd, x, y):
        """윈도우 핸들을 사용해 창 이동"""
        win32gui.SetWindowPos(hwnd, 0, x, y, 0, 0, 1)

    @staticmethod
    def get_window_info(hwnd):
        """
        주어진 윈도우 핸들의 위치 및 크기 정보를 반환
        pyautogui를 위한 좌표와 크기 반환
        """
        rect = win32gui.GetWindowRect(hwnd)  # 창의 좌표 정보 가져오기
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


class DiabloManagerApp(QWidget):
    """PyQt5 UI를 사용한 디아블로 창 관리 애플리케이션"""

    def __init__(self):
        super().__init__()
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
        self.role_selection.addItems(["Master", "Slave","None"])
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
        button_layout.addWidget(exit_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def detect_windows(self):
        """디아블로 2 창 탐지 (프로세스 이름 기반)"""
        self.window_list_widget.clear()
        process_name = "D2R.exe"  # 디아블로 2의 실행 파일 이름
        windows = DiabloWindowManager.find_windows_by_process_name(process_name)

        if not windows:
            QMessageBox.warning(self, "경고", "디아블로 2 창을 찾을 수 없습니다.")
            return

        for hwnd, title in windows:
            self.window_list_widget.addItem(f"{title} (HWND: {hwnd})")

        QMessageBox.information(self, "창 탐지 완료", f"{len(windows)}개의 디아블로 2 창을 탐지했습니다.")

    def set_roles_and_positions(self):
        """사용자가 선택한 창에 역할 지정 및 위치 배치"""
        selected_items = self.window_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "역할을 지정할 창을 선택하세요.")
            return

        selected_text = selected_items[0].text()
        hwnd = int(selected_text.split("(HWND: ")[-1].rstrip(")"))  # HWND 추출
        selected_role = self.role_selection.currentText()

        # 역할에 따라 창 배치
        if selected_role == "Master":
            DiabloWindowManager.move_window(hwnd, 0, 0)  # 모니터 1 (좌상단)
            QMessageBox.information(self, "Master 설정 완료", f"창 (HWND: {hwnd})를 Master로 설정하고 모니터 1에 배치했습니다.")
        elif selected_role == "Slave":
            DiabloWindowManager.move_window(hwnd, 1920, 0)  # 모니터 2 (우상단)
            QMessageBox.information(self, "Slave 설정 완료", f"창 (HWND: {hwnd})를 Slave로 설정하고 모니터 2에 배치했습니다.")

    def print_window_info(self):
        """선택된 창의 정보를 출력"""
        selected_items = self.window_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "정보를 출력할 창을 선택하세요.")
            return

        selected_text = selected_items[0].text()
        hwnd = int(selected_text.split("(HWND: ")[-1].rstrip(")"))  # HWND 추출

        info = DiabloWindowManager.get_window_info(hwnd)
        QMessageBox.information(
            self,
            "창 정보",
            f"HWND: {info['hwnd']}\nX: {info['x']}\nY: {info['y']}\nWidth: {info['width']}\nHeight: {info['height']}"
        )

        # 예제: pyautogui로 클릭할 좌표 출력
        print(f"PyAutoGUI 좌표: Center X = {info['x'] + info['width'] // 2}, Center Y = {info['y'] + info['height'] // 2}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager_app = DiabloManagerApp()
    manager_app.show()
    sys.exit(app.exec_())
