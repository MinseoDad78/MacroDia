import cv2
import numpy as np
import mss
import time


def preprocess_image(image):
    """
    이미지를 전처리하여 엣지 이미지로 변환합니다.
    Args:
        image (numpy.ndarray): 입력 이미지.
    Returns:
        numpy.ndarray: 엣지 이미지.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)  # Canny 엣지 검출
    return edges


def detect_icon(frame, icon_template, threshold=0.8):
    """
    엣지 검출된 이미지를 사용하여 아이콘을 탐지합니다.
    Args:
        frame (numpy.ndarray): 캡처된 화면.
        icon_template (numpy.ndarray): 엣지 템플릿 이미지.
        threshold (float): 템플릿 매칭 민감도.
    Returns:
        tuple: 탐지된 아이콘의 중심 좌표 (center_x, center_y), 또는 None.
    """
    result = cv2.matchTemplate(frame, icon_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        icon_w, icon_h = icon_template.shape[::-1]
        center_x = max_loc[0] + icon_w // 2
        center_y = max_loc[1] + icon_h // 2
        return center_x, center_y
    return None


def capture_screen_and_find_icon(template_path, threshold=0.8):
    """
    화면을 캡처하고 특정 아이콘을 엣지 기반으로 탐지합니다.
    Args:
        template_path (str): 아이콘 템플릿 이미지 경로.
        threshold (float): 템플릿 매칭 민감도.
    """
    # 아이콘 템플릿 로드 및 전처리
    icon_template = cv2.imread(template_path)
    if icon_template is None:
        print("템플릿 이미지를 로드할 수 없습니다.")
        return
    icon_template = preprocess_image(icon_template)

    with mss.mss() as sct:
        monitor = {"top": 100, "left": 100, "width": 800, "height": 600}

        while True:
            # 화면 캡처 및 전처리
            frame = np.array(sct.grab(monitor))
            edge_frame = preprocess_image(frame)

            # 아이콘 탐지
            icon_center = detect_icon(edge_frame, icon_template, threshold)
            if icon_center:
                center_x, center_y = icon_center
                print(f"아이콘 발견: ({center_x}, {center_y})")
            else:
                print("아이콘을 찾을 수 없습니다.")

            time.sleep(0.5)
            
def detect_icon_orb(frame, icon_template, threshold=10):
    """
    ORB를 사용하여 아이콘을 탐지합니다.
    Args:
        frame (numpy.ndarray): 캡처된 화면.
        icon_template (numpy.ndarray): 템플릿 이미지.
        threshold (int): 최소 매칭점 개수.
    Returns:
        tuple: 탐지된 아이콘의 중심 좌표 (center_x, center_y), 또는 None.
    """
    # ORB 생성 및 특징점 검출
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(icon_template, None)
    kp2, des2 = orb.detectAndCompute(frame, None)

    # 매칭 수행
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # 매칭 점수 계산
    matches = sorted(matches, key=lambda x: x.distance)
    if len(matches) >= threshold:
        # 중심 좌표 계산
        matched_kp = [kp2[m.trainIdx].pt for m in matches]
        center_x = int(np.mean([pt[0] for pt in matched_kp]))
        center_y = int(np.mean([pt[1] for pt in matched_kp]))
        return center_x, center_y
    return None


# 실행
if __name__ == "__main__":
    # 템플릿 이미지 경로와 민감도 설정
    template_path = "path_to_icon_image.png"  # 템플릿 이미지 경로
    threshold = 0.8  # 민감도

    # 아이콘 탐지 실행
    capture_screen_and_find_icon(template_path, threshold)
