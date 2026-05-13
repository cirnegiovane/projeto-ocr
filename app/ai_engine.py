from google import genai
from PIL import Image
import json
import cv2

def call_gemini(file, api_key):
    MODEL_ID = 'gemini-2.5-flash' 
    PROMPT = """
        Analise a tabela na imagem e extraia os dados para o formato JSON. 
        Siga rigorosamente estas regras:
        1. Retorne uma lista de objetos com as chaves: "NOME", "TELEFONE", "CIDADE", "BAIRRO", "ORGAO".
        2. Se uma palavra estiver ilegível, deixe o valor como string vazia "".
        3. Processe a imagem de cima para baixo, linha por linha.
        4. Responda APENAS o JSON, sem explicações, markdown ou blocos de código.
        """
    client = genai.Client(api_key=api_key)
    try:
        if file is None:
            raise
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                genai.types.Part.from_bytes(data=file, mime_type='image/jpeg'),
                PROMPT
                ]
            )
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(clean_text.strip())
        except Exception as e:
            # Caso a IA retorne algo que não é JSON puro
            print(f"Erro ao decodificar JSON: {e}")
            return []

    except Exception as e:
        print(f"\nErro ao processar {file}: {e}")