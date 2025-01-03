import cv2
import numpy as np
import mss
import time
import win32api
import win32con

def find_window_by_title(partial_title):
    """
    창 제목을 기준으로 창 핸들을 찾습니다.
    Args:
        partial_title (str): 창 제목의 일부.

    Returns:
        int: 창 핸들(Window Handle).
    """
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle(partial_title)
    if windows:
        return windows[0]._hWnd  # 첫 번째 일치하는 창의 핸들 반환
    return None

def detect_icon(frame, icon_template, threshold=0.8):
    """
    아이콘을 화면에서 탐지합니다.

    Args:
        frame (numpy.ndarray): 캡처된 화면.
        icon_template (numpy.ndarray): 아이콘 템플릿 이미지.
        threshold (float): 템플릿 매칭 임계값.

    Returns:
        tuple: 탐지된 아이콘의 중심 좌표 (center_x, center_y), 또는 None.
    """
    result = cv2.matchTemplate(frame, icon_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        icon_w, icon_h = icon_template.shape[::-1]
        center_x = max_loc[0] + icon_w // 2
        center_y = max_loc[1] + icon_h // 2
        return center_x, center_y  # 아이콘 중심 좌표 반환
    return None

def send_click_to_window(hwnd, x, y):
    """
    특정 창에 클릭 이벤트를 보냅니다.
    Args:
        hwnd (int): 대상 창의 핸들.
        x, y (int): 클릭할 창 내부 좌표.
    """
    lparam = win32api.MAKELONG(x, y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.1)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)

def track_and_chase_icon(template_path, process_name="Diablo II:"):
    """
    화면에서 특정 아이콘을 추적하여 마우스 동작을 수행합니다.

    Args:
        template_path (str): 아이콘 템플릿 이미지 경로.
        process_name (str): 대상 창 제목.
    """
    # Slave 창 핸들 찾기
    hwnd = find_window_by_title(process_name)
    if not hwnd:
        print(f"'{process_name}' 창을 찾을 수 없습니다.")
        return

    print(f"'{process_name}' 창을 제어합니다 (HWND: {hwnd}).")

    # 아이콘 템플릿 로드
    icon_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if icon_template is None:
        print("템플릿 이미지를 로드할 수 없습니다.")
        return

    # 화면 캡처 초기화
    with mss.mss() as sct:
        monitor = {"top": 100, "left": 100, "width": 800, "height": 600}

        while True:
            # 화면 캡처
            frame = np.array(sct.grab(monitor))
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

            # 아이콘 탐지
            icon_center = detect_icon(gray_frame, icon_template)
            if icon_center:
                center_x, center_y = icon_center
                print(f"아이콘 발견: ({center_x}, {center_y})")

                # 마우스 이동 및 클릭
                send_click_to_window(hwnd, center_x, center_y)

            else:
                print("아이콘을 찾을 수 없습니다.")

            time.sleep(0.1)  # 반복 주기 설정
