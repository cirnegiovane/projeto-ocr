from google import genai
from PIL import Image
import json
import cv2

def call_gemini(image_np, api_key):
    try:
        client = genai.Client(api_key=api_key)
        
        # Usamos o nome puro do modelo. A v1 estável suporta este nome.
        #model = genai.GenerativeModel('gemini-1.5-flash')
        
        image_pil = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
        
        prompt = """
        Extract handwriting to JSON. 
        Keys: NOME, TELEFONE, CIDADE, BAIRRO, ORGAO.
        Return ONLY JSON.
        """
        
        # Chamada padrão (compatível com v1 estável)
        #response = model.generate_content([prompt, image_pil])
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                prompt,
                image_pil
            ]
        )
        
        # Parsing manual robusto
        txt = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(txt)
        
    except Exception as e:
        if "429" in str(e):
            print("⚠️ Quota atingida. Aguardando 5 segundos...")
            time.sleep(5) # Throttle básico
        print(f"DEBUG IA: {e}")
        return {"NOME": "ERRO", "TELEFONE": "", "CIDADE": "", "BAIRRO": "", "ORGAO": ""}