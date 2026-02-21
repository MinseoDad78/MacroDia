import cv2
import numpy as np

def detect_green_crosses_template_matching(image_path, template_path, threshold=0.7):
    """
    템플릿 매칭을 이용하여 녹색 십자가(+) 탐지
    Args:
        image_path (str): 입력 이미지 경로
        template_path (str): 십자 모양 템플릿 이미지 경로
        threshold (float): 매칭 민감도 (0.7~0.9 추천)
    Returns:
        list: 탐지된 녹색 십자의 중심 좌표 리스트 [(x1, y1), (x2, y2), ...]
    """
    # **[1] 이미지 로드**
    image = cv2.imread(image_path)
    if image is None:
        print("이미지를 로드할 수 없습니다.")
        return []

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print("템플릿 이미지를 로드할 수 없습니다.")
        return []

    # **[2] 이미지 전처리 (HSV 변환 & 녹색 필터링)**
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([40, 80, 40])  
    upper_green = np.array([80, 255, 255])  
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    green_only = cv2.bitwise_and(image, image, mask=green_mask)
    gray = cv2.cvtColor(green_only, cv2.COLOR_BGR2GRAY)

    # **[3] 템플릿 매칭 수행**
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    detected_positions = []
    h, w = template.shape

    for pt in zip(*locations[::-1]):  # 템플릿과 일치하는 위치 찾기
        center_x = pt[0] + w // 2
        center_y = pt[1] + h // 2
        detected_positions.append((center_x, center_y))

        # **탐지된 위치 표시**
        cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

    # **[4] 결과 출력**
    cv2.imshow("Green Crosses Detected", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return detected_positions

def detect_green_crosses(image_path, template_path, threshold=0.7, scales=[0.6, 0.8, 1.0, 1.2]):
    """
    템플릿 매칭을 이용하여 녹색 십자가(+) 탐지 (다중 크기 지원)
    Args:
        image_path (str): 입력 이미지 경로
        template_path (str): 십자 모양 템플릿 이미지 경로
        threshold (float): 매칭 민감도 (0.7~0.9 추천)
        scales (list): 템플릿 크기 조정 비율 리스트 (여러 크기 대응)
    Returns:
        list: 탐지된 녹색 십자의 중심 좌표 리스트 [(x1, y1), (x2, y2), ...]
    """
    # **[1] 이미지 로드**
    image = cv2.imread(image_path)
    if image is None:
        print("이미지를 로드할 수 없습니다.")
        return []

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print("템플릿 이미지를 로드할 수 없습니다.")
        return []

    # **[2] 이미지 전처리 (HSV 변환 & 녹색 필터링)**
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 60, 40])  # 기존보다 더 넓은 범위 적용
    upper_green = np.array([90, 255, 255])  
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    green_only = cv2.bitwise_and(image, image, mask=green_mask)
    gray = cv2.cvtColor(green_only, cv2.COLOR_BGR2GRAY)

    detected_positions = []
    
    # **[3] 템플릿 크기 변형하여 여러 크기 대응**
    for scale in scales:
        resized_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(gray, resized_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        h, w = resized_template.shape
        for pt in zip(*locations[::-1]):  # 템플릿과 일치하는 위치 찾기
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2
            detected_positions.append((center_x, center_y))

            # **탐지된 위치 표시**
            cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

    # **[4] 결과 출력**
    cv2.imshow("Green Crosses Detected", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return detected_positions



if __name__ == "__main__":
    image_path = "C:\\Dev\\Test\\002.png"
    template_path = "C:\\Dev\\Test\\target.png" # 녹색 십자(+) 템플릿 이미지
    positions = detect_green_crosses(image_path, template_path, threshold=0.6, scales=[0.5, 0.7, 1.0, 1.3,1.5,1.7,2.0])
    print(f"탐지된 녹색 십자 좌표: {positions}")