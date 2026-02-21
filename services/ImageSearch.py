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
신클래스
2025-03-10 IconDetectorTest.py 을 변경하여 추가함
"""
class IconDetector:

    logger = LogHandler("FIND")
    
    def __init__(self):
        pass

        

    def _detect_green_crosses(self, gray_frame, resized_templates, threshold=0.6):
        """
        녹색 십자가(+)를 탐지하는 함수.
        
        Args:
            gray_frame (numpy.ndarray): Grayscale 변환된 화면.
            icon_templates (list): 크기 조정된 템플릿 이미지 리스트.
            threshold (float): 탐지 민감도.
            min_size (int): 최소 크기 제한 (글자 등의 작은 요소 필터링).
        
        Returns:
            list: 탐지된 십자의 중심 좌표 리스트 [(center_x1, center_y1), (center_x2, center_y2), ...].
        """
        detected_positions = []

        for resized_template in resized_templates:
           
          
            # **[2] 템플릿 매칭 실행**
            result = cv2.matchTemplate(gray_frame, resized_template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)

            # **[3] 탐지된 위치 저장**
            h, w = resized_template.shape
            for pt in zip(*locations[::-1]):  # 템플릿과 일치하는 위치 찾기
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                detected_positions.append((center_x, center_y))

        return detected_positions
    
    def capture_screen_and_find_icons(self, info, template_path, threshold=0.6, scales=[0.6, 0.8, 1.0, 1.2]):
        """
        화면을 실시간 캡처하고 모든 녹색 십자(+) 아이콘을 탐지합니다.
        Args:
            info (dict): 화면 캡처 영역 정보 (x, y, width, height).
            template_path (str): 십자 모양 템플릿 이미지 경로.
            threshold (float): 탐지 민감도.
            scales (list): 템플릿 크기 조정 비율 리스트.
        Returns:
            list: 탐지된 십자의 중심 좌표 리스트.
        """

        self.logger.info("아이콘 탐지를 시작합니다.")
        # **탐지할 아이콘 템플릿 로드 (+)**
        icon_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if icon_template is None:
            self.logger.error("탐지할 템플릿 이미지를 로드할 수 없습니다.")
            return []

        resized_templates = [cv2.resize(icon_template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) for scale in scales]

        # **화면 캡처 영역 설정**
        monitor = {"top": info['y'], "left": info['x'], "width": info['width'], "height": info['height']}
        self.logger.info(f"캡처 영역: {monitor}")

        # **캡처 화면의 중심 좌표 계산**
        monitor_center_x = monitor["left"] + monitor["width"] // 2
        monitor_center_y = monitor["top"] + monitor["height"] // 2
        self.logger.info(f"Center 좌표: ({monitor_center_x}, {monitor_center_y})")

        with mss.mss() as sct:
          # while True:
                detected_positions = set()

                # **[1] 화면 캡처**
                frame = np.array(sct.grab(monitor))
             # 🎯 **BGRA → BGR 변환 (알파 채널 제거)**
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                 # **[2] BGR → HSV 변환 후 녹색 필터링**
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_green = np.array([40, 50, 50])  # 녹색 하한값
                upper_green = np.array([85, 255, 255])  # 녹색 상한값
        
                green_mask = cv2.inRange(hsv, lower_green, upper_green)

                # **[3] 녹색 영역만 남기고 배경 제거**
                filtered_frame = cv2.bitwise_and(frame, frame, mask=green_mask)

                # **[4] Grayscale 변환**
                gray_frame = cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2GRAY)

                # **[3] 템플릿 매칭을 통해 아이콘 탐지**
                detected_positions = self._detect_green_crosses(gray_frame, resized_templates, threshold)

                self.logger.info(f"탐지된 아이콘 수: {len(detected_positions)}")
                # **[4] 탐지된 십자 위치 화면에 표시**
                for (center_x, center_y) in detected_positions:
                    cv2.circle(frame, (center_x, center_y), 10, (0, 0, 255), 2)  # 탐지된 위치에 빨간 원 표시

                cv2.imshow("Detected Green Crosses", frame)
               
                # **ESC 키를 누르면 종료**
                
               # if cv2.waitKey(1) & 0xFF == 27:
                #   break
                
 
        #cv2.destroyAllWindows()
        return detected_positions

"""


# 실행 예제
if __name__ == "__main__":
    screen_info = {
        "x": 100,  # 감지할 영역의 X 좌표 (게임 창의 좌상단)
        "y": 100,  # 감지할 영역의 Y 좌표
        "width": 800,  # 감지할 영역의 너비
        "height": 600,  # 감지할 영역의 높이
    }
    
    template_path = "/mnt/data/target.png"  # 탐지할 십자 아이콘 템플릿

    # **실시간 화면 캡처 후 아이콘 탐지 실행**
    positions = capture_screen_and_find_icons(screen_info, template_path, threshold=0.75)
    print(f"탐지된 녹색 십자 좌표: {positions}")

"""