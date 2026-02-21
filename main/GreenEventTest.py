import cv2
import numpy as np
import pyautogui


def detect_green_objects_with_labels(image_path):
    """
    이미지에서 녹색 영역을 탐지하고 탐지된 좌표에 'O'를 표기합니다.
    Args:
        image_path (str): 입력 이미지 경로.
    Returns:
        None
    """
    # 이미지 읽기
    image = cv2.imread(image_path)
    if image is None:
        print("이미지를 로드할 수 없습니다.")
        return

    # BGR 이미지를 HSV로 변환
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 녹색 범위 정의 (HSV 값으로 설정)
    lower_green = np.array([35, 100, 50])  # 녹색 하한
    upper_green = np.array([85, 255, 255])  # 녹색 상한

    # 녹색 마스크 생성
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # 컨투어(윤곽선) 검출
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 컨투어 중심 계산 및 'O' 표기
    for contour in contours:
        if cv2.contourArea(contour) < 50:  # 너무 작은 영역은 무시
            continue

        # 중심 좌표 계산
        M = cv2.moments(contour)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])

            # 중심 좌표를 이미지에 표시
            cv2.putText(image, "O", (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(f"녹색 탐지 좌표: ({center_x}, {center_y})")

    # 결과 출력
    cv2.imshow("Green Detected with Labels", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# 실행
image_path = "C:\\Games\\0001.png"  # 업로드된 이미지 경로
detect_green_objects_with_labels(image_path)
