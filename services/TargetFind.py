import win32gui
import win32process
import win32ui
import win32con
import pyautogui
import cv2
import numpy as np


class WindowManager:
    """윈도우 창 관리 클래스"""

    @staticmethod
    def find_windows_by_title(partial_title):
        """제목에 특정 문자열이 포함된 모든 창을 탐지"""
        windows = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if partial_title.lower() in title.lower():
                    windows.append((hwnd, title))

        win32gui.EnumWindows(enum_windows_callback, None)
        return windows

    @staticmethod
    def get_window_info(hwnd):
        """윈도우 핸들을 통해 창 정보 추출"""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        class_name = win32gui.GetClassName(hwnd)

        return {
            "hwnd": hwnd,
            "title": win32gui.GetWindowText(hwnd),
            "class_name": class_name,
            "process_id": pid,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }

    @staticmethod
    def capture_window(hwnd):
        """게임 창 캡처"""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, width, height = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitmap = win32ui.CreateBitmap()
        saveBitmap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitmap)

        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        bmpinfo = saveBitmap.GetInfo()
        bmpstr = saveBitmap.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, dtype='uint8')
        img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)

        win32gui.DeleteObject(saveBitmap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


if __name__ == "__main__":
    # 게임 창 탐지
    game_window_title = "Diablo II"  # 게임 창 제목의 일부를 입력
    detected_windows = WindowManager.find_windows_by_title(game_window_title)

    if not detected_windows:
        print(f"'{game_window_title}'와(과) 일치하는 창을 찾을 수 없습니다.")
        exit()

    print(f"탐지된 창 목록:")
    for i, (hwnd, title) in enumerate(detected_windows):
        print(f"[{i}] HWND: {hwnd}, 제목: {title}")

    # 사용자로부터 탐지된 창 선택
    selected_index = int(input("조작할 창의 번호를 선택하세요: "))
    if selected_index < 0 or selected_index >= len(detected_windows):
        print("유효하지 않은 선택입니다.")
        exit()

    selected_hwnd = detected_windows[selected_index][0]

    # 선택된 창 정보 출력
    window_info = WindowManager.get_window_info(selected_hwnd)
    print("선택된 창 정보:")
    for key, value in window_info.items():
        print(f"  {key}: {value}")

    # 선택된 창 캡처 및 디버깅
    print("게임 창을 캡처합니다...")
    captured_image = WindowManager.capture_window(selected_hwnd)

    # OpenCV 창에 캡처된 이미지 표시
    cv2.imshow("Captured Game Window", captured_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
