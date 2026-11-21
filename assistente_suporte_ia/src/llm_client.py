import os 
from dotenv import load_dotenv
from google import genai

load_dotenv()

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Carrega a chave do arquivo .env
load_dotenv()

MODELO = "gemini-3.8-flash"

def gerar_resposta(prompt: str, exigir_json: bool = False) -> str:
    chave_api = os.getenv("GEMINI_API_KEY")
    if not chave_api:
        raise ValueError("Erro: GEMINI_API_KEY não encontrada no arquivo .env")

    cliente = genai.Client(api_key=chave_api)

    # Temperatura baixa para manter consistência técnica
    configuracao = {"temperature": 0.2}
    
    # Se o prompt pedir dados estruturados, força resposta em JSON puro
    if exigir_json:
        configuracao["response_mime_type"] = "application/json"

    try:
        resposta = cliente.models.generate_content(
            model=MODELO,
            contents=prompt,
            config=types.GenerateContentConfig(**configuracao)
        )
        return resposta.text
    except Exception as erro:
        raise RuntimeError(f"Falha na comunicação com o Gemini: {erro}")