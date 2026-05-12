import cv2
import numpy as np

def segment_rows(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: return []

    # 1. Resize para consistência
    h, w = img.shape[:2]
    img = cv2.resize(img, (1200, int(h * (1200 / w))))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Binarização
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 25, 12)

    # 3. LIMPEZA DE BORDAS (O "Corte Cirúrgico")
    # Zera (pinta de preto) os 3% das bordas da imagem para ignorar molduras e papel
    pad_h, pad_w = int(img.shape[0] * 0.03), int(img.shape[1] * 0.03)
    binary[0:pad_h, :] = 0  # Topo
    binary[-pad_h:, :] = 0  # Baixo
    binary[:, 0:pad_w] = 0  # Esquerda
    binary[:, -pad_w:] = 0  # Direita

    # 4. REMOÇÃO DE LINHAS (Tabela)
    # Apaga linhas horizontais longas
    horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1))
    lines_h = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz, iterations=2)
    binary = cv2.subtract(binary, lines_h)

    # 5. Dilação Horizontal para agrupar palavras
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 3))
    dilated = cv2.dilate(binary, kernel, iterations=2)

    # 6. Detecção de Contornos
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
    
    crops = []
    for cnt in contours:
        x, y, w_c, h_c = cv2.boundingRect(cnt)
        
        # Filtro Rigoroso: 
        # A largura deve ser significativa (ex: > 30% da página)
        # A altura deve ser de uma linha manuscrita (30px a 120px)
        if w_c > 350 and 30 < h_c < 120:
            # Respiro vertical
            y_s, y_e = max(0, y-10), min(img.shape[0], y + h_c + 10)
            crops.append(img[y_s:y_e, :])
            
    return crops if crops else [img]