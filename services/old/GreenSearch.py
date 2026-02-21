import cv2
import numpy as np
import mss
import logging
import pyautogui
class IconDetector:
    def __init__(self, template_path):
        self.template_path = template_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

    def resize_template(self, icon_template, scales):
        """
        템플릿 이미지를 다양한 크기로 조정합니다.
        Args:
            icon_template (numpy.ndarray): 원본 템플릿 이미지.
            scales (list): 크기 조정 비율 리스트.
        Returns:
            list: 크기가 조정된 템플릿 이미지 리스트.
        """
        resized_templates = []
        for scale in scales:
            resized_templates.append(cv2.resize(icon_template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA))
        return resized_templates

    def detect_icon(self, frame, icon_templates, threshold=0.9):
        """
        템플릿 매칭을 사용하여 특정 아이콘을 탐지합니다.
        Args:
            frame (numpy.ndarray): 캡처된 화면.
            icon_templates (list): 크기가 조정된 템플릿 이미지 리스트.
            threshold (float): 탐지 민감도.
        Returns:
            list: 탐지된 아이콘의 중심 좌표 리스트 [(x1, y1), (x2, y2), ...].
        """
        detected_positions = []

        for icon_template in icon_templates:
            result = cv2.matchTemplate(frame, icon_template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            icon_w, icon_h = icon_template.shape[::-1]

            for pt in zip(*locations[::-1]):  # (x, y) 좌표 생성
                center_x = pt[0] + icon_w // 2
                center_y = pt[1] + icon_h // 2
                detected_positions.append((center_x, center_y))

        return detected_positions

    def capture_screen_and_find_icon(self, info, threshold=0.9, scales=[0.6, 0.8, 1.0, 1.2], exclusion_radius=5):
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
        monitor = {"top": info['y'], "left": info['x'], "width": info['width'], "height": info['height']}
        self.logger.debug(f"캡처 영역: {monitor}")

        with mss.mss() as sct:
            while True:
                # 화면 캡처
                frame = np.array(sct.grab(monitor))
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # 아이콘 탐지
                icon_positions = self.detect_icon(gray_frame, resized_templates, threshold)
                for pos in icon_positions:
                    center_x, center_y = pos

                    # 중심 좌표 출력
                    self.logger.info(f"아이콘 탐지 좌표: ({center_x}, {center_y})")
                    pyautogui.click(center_x, center_y)
                if not icon_positions:
                    self.logger.info("탐지된 아이콘 없음.")

                # ESC 키로 종료
                if cv2.waitKey(1) & 0xFF == 27:
                    break

        cv2.destroyAllWindows()


# 실행 예제
if __name__ == "__main__":
    # 아이콘 탐지기 생성
    template_path = "path_to_icon_template.png"  # 템플릿 이미지 경로
    detector = IconDetector(template_path)

    # 화면 캡처 영역 정보
    screen_info = {
        "x": 100,  # 캡처 시작 X 좌표
        "y": 100,  # 캡처 시작 Y 좌표
        "width": 800,  # 캡처 영역 너비
        "height": 600,  # 캡처 영역 높이
    }

    # 특정 아이콘 탐지 실행
    detector.capture_screen_and_find_icon(screen_info, threshold=0.9)
