import cv2
import numpy as np
import mss
import time
import pyautogui
import keyboard
import cv2
import numpy as np
import mss
import time
import win32api
import win32con, win32gui

from main.SendEventTest import send_click_to_window
from services.LogService import  LogHandler
"""
구 클래스
"""
class FindImage:
    template_path = "c:\\games\\target.png"  # 탐지할 아이콘 템플릿 이미지 경로
    center_icon_template_path = "c:\\games\\center_icon.png"  # 본인 아이콘 템플릿 경로
    threshold = 0.7  # 민감도
    logger = LogHandler("FIND")
    def resize_template(self, icon_template, scales):
        """
        템플릿 이미지를 다양한 크기로 조정합니다.
        Args:
            icon_template (numpy.ndarray): 원본 템플릿 이미지.
            scales (list): 크기 조정 비율 리스트 (예: [0.6, 0.8, 1.0, 1.2]).
        Returns:
            list: 크기가 조정된 템플릿 이미지 리스트.
        """
        resized_templates = []
        for scale in scales:
            resized_templates.append(cv2.resize(icon_template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA))
        return resized_templates

    def detect_icons(self, frame, icon_templates, threshold=0.7):
        """
        템플릿 매칭을 사용하여 모든 매칭된 아이콘을 탐지합니다.
        Args:
            frame (numpy.ndarray): 캡처된 화면.
            icon_templates (list): 크기가 조정된 템플릿 이미지 리스트.
            threshold (float): 탐지 민감도.
        Returns:
            list: 탐지된 아이콘들의 중심 좌표 리스트 [(center_x1, center_y1), (center_x2, center_y2), ...].
        """
        detected_positions = []

        for icon_template in icon_templates:
            result = cv2.matchTemplate(frame, icon_template, cv2.TM_CCOEFF_NORMED)

            # threshold 이상의 모든 매칭 위치 가져오기
            locations = np.where(result >= threshold)
            icon_w, icon_h = icon_template.shape[::-1]

            for pt in zip(*locations[::-1]):  # (x, y) 좌표 생성
                center_x = pt[0] + icon_w // 2
                center_y = pt[1] + icon_h // 2
                detected_positions.append((center_x, center_y))

        return detected_positions
    def capture_screen_and_find_icon(self, info, threshold=0.9, scales=[0.6, 0.8, 1.0, 1.2], exclusion_radius =5):
        """
        화면을 캡처하고 특정 아이콘을 탐지합니다.
        Args:
            info (dict): 화면 캡처 영역 정보 (x, y, width, height).
            threshold (float): 탐지 민감도.
            scales (list): 템플릿 크기 조정 비율 리스트.
        """
        # 탐지할 아이콘 템플릿 이미지 로드
        icon_template = cv2.imread(self.template_path, cv2.IMREAD_GRAYSCALE)
        if icon_template is None:
            self.logger.error("탐지할 템플릿 이미지를 로드할 수 없습니다.")
            return
        resized_templates = self.resize_template(icon_template, scales)

        # 화면 캡처 영역 설정
        monitor = {"top": info['x'], "left": info['y'], "width": info['width'], "height": info['height']}
        self.logger.debug(f"캡처 영역: {monitor}")
        _hwnd = info['hwnd']
        monitor_center_y = monitor["left"] + monitor["height"] // 2
        monitor_center_x = monitor["top"] + monitor["width"] // 2
        self.logger.debug(f"Center 좌표 : ({monitor_center_x} , {monitor_center_y})")


        with mss.mss() as sct:
            while True:
                detected_positions = set()
                # 화면 캡처
                frame = np.array(sct.grab(monitor))
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # 아이콘 탐지
                icon_centers = self.detect_icons(gray_frame, resized_templates, threshold)
                self.logger.debug(f"size: {len(icon_centers)}")
                for center_x, center_y in icon_centers:

                    absolute_x = monitor["top"] + center_x # 바꿈
                    absolute_y = monitor["left"] + center_y

                    distance = abs( monitor_center_x-absolute_x) + abs( monitor_center_y -absolute_y)
                    self.logger.debug(f"distance: {distance}, x: {absolute_x}, y : {absolute_y}")
                    if distance <= exclusion_radius:
                        self.logger.debug(f"센터 근처 아이콘 발견: 무시합니다. x:{absolute_x},  :{absolute_y}")
                        continue
                        # 중복 탐지 방지

                    if (center_x, center_y) in detected_positions:
                            self.logger.debug(f"중복 아이콘 탐지로 제외됨: ({center_x}, {center_y})")
                            continue

                    self.logger.debug(f"아이콘 발견: ({absolute_x}, {absolute_y})")
                    detected_positions.add((center_x, center_y))

                        # 절대 좌표 계산 및 드래그

                   # pyautogui.dragTo(x=absolute_x, y=absolute_y, duration=5)

                    start_pos = (monitor_center_x , monitor_center_y)
                    end_pos = (absolute_x,absolute_y)
                    self. post_drag_event(hwnd=_hwnd,start_pos=start_pos, end_pos=end_pos, duration=0.5, minimum_drag_distance=10)

                else:
                    self.logger.debug("탐지된 아이콘 없음.")

                time.sleep(1)

                # ESC 키로 종료
                if keyboard.is_pressed("esc"):
                    self.logger.debug("ESC 키 감지, 종료합니다.")
                    break

    def post_drag_event(self,hwnd, start_pos, end_pos, duration=2.0, minimum_drag_distance=10):
        """
        특정 창에서 드래그 이벤트를 발생시키되, 드래그 시간을 조절합니다.
        Args:
            hwnd (int): 대상 창 핸들.
            start_pos (tuple): 드래그 시작 좌표 (x, y).
            end_pos (tuple): 드래그 종료 좌표 (x, y).
            duration (float): 드래그에 소요되는 시간 (초 단위).
            minimum_drag_distance (int): 최소 드래그 거리 (픽셀 단위).
        """
        try:
            start_x, start_y = start_pos
            end_x, end_y = end_pos

            # 최소 드래그 거리 확인
            distance = abs(start_x - end_x) + abs(start_y - end_y)
            if distance < minimum_drag_distance:
                self.logger.debug(f"드래그 거리가 너무 짧아 무시됩니다. 거리: {distance}")
                return

            # 좌표를 LPARAM 형식으로 변환
            lparam_start = win32api.MAKELONG(start_x, start_y)
            lparam_end = win32api.MAKELONG(int(end_x), int(end_y))

            # 드래그 시작: 마우스 왼쪽 버튼 눌림
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam_start)
            self.logger.debug(f"드래그 시작 좌표: {start_pos}")

            # 이동: 점진적으로 마우스 이동
            steps = 100  # 이동 단계 수 (더 많을수록 부드러움)
            step_delay = duration / steps  # 각 단계 간 딜레이

            for i in range(steps):
                # 각 단계에서의 좌표 계산
                intermediate_x = int(start_x + (end_x - start_x) * (i / steps))
                intermediate_y = int(start_y + (end_y - start_y) * (i / steps))
                lparam_intermediate = win32api.MAKELONG(intermediate_x, intermediate_y)
                win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lparam_intermediate)
                time.sleep(step_delay)  # 단계별 딜레이

            # 드래그 끝: 마우스 왼쪽 버튼 떼기
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, lparam_end)
            self.logger.debug(f"드래그 종료 좌표: {end_pos}")

        except Exception as e:
            self.logger.debug(f"드래그 이벤트 처리 중 오류 발생: {e}")


    def send_click_to_window(self,hwnd, x, y):

        """
        특정 창에 클릭 이벤트를 보냅니다.
        Args:
            hwnd (int): 대상 창의 핸들.
            x, y (int): 클릭할 창 내부 좌표.
        """
        lparam = win32api.MAKELONG(x, y)
        win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)

        win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)


"""
신클래스
"""
class IconDetector:
    def __init__(self):
        pass

    def detect_green_crosses(self, screen_info):
        """
        화면 캡처 내에서 녹색 십자가(+) 탐지
        Args:
            screen_info (dict): 화면 캡처 영역 정보 (x, y, width, height)
        Returns:
            list: 탐지된 녹색 십자의 중심 좌표 리스트 [(x1, y1), (x2, y2), ...]
        """
        with mss.mss() as sct:
            # **[1] 화면 캡처**
            monitor = {
                "top": screen_info['y'],
                "left": screen_info['x'],
                "width": screen_info['width'],
                "height": screen_info['height']
            }

            frame = np.array(sct.grab(monitor))
            image = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # BGRA → BGR 변환

            # **[2] HSV 변환 및 녹색 필터링**
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_green = np.array([35, 100, 50])  # 녹색 하한
            upper_green = np.array([85, 255, 255])  # 녹색 상한
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # **[3] 윤곽선(Contour) 검출**
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detected_positions = []
            for contour in contours:
                if cv2.contourArea(contour) < 50:  # 너무 작은 물체 무시
                    continue

                # **[4] 십자 모양 확인 (비율 체크)**
                rect = cv2.boundingRect(contour)
                aspect_ratio = rect[2] / rect[3]  # 가로/세로 비율
                if 0.8 < aspect_ratio < 1.2:  # 정사각형 (십자일 가능성 높음)
                    center_x = rect[0] + rect[2] // 2
                    center_y = rect[1] + rect[3] // 2

                    # **[5] 탐지된 십자 좌표 저장 및 표시**
                    detected_positions.append((center_x, center_y))
                    cv2.putText(image, "O", (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # **[6] 결과 출력**
            cv2.imshow("Green Crosses Detected", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            return detected_positions
