import numpy as np
import cv2


def rotate_image(image_bytes, clockwise=True):
    # Converte bytes para array numpy
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return image_bytes

    # Define o código de rotação do OpenCV
    # ROTATE_90_CLOCKWISE (90° horários) ou ROTATE_90_COUNTERCLOCKWISE (90° anti-horários)
    code = cv2.ROTATE_90_CLOCKWISE if clockwise else cv2.ROTATE_90_COUNTERCLOCKWISE
    rotated_img = cv2.rotate(img, code)
    
    # Codifica de volta para bytes
    _, buffer = cv2.imencode('.jpg', rotated_img)
    return buffer.tobytes()


def preprocess_image(file):
    file.seek(0)
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    _, buffer = cv2.imencode('.jpg', enhanced)
    return buffer.tobytes()
