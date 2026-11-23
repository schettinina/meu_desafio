import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI

load_dotenv()


def _chamar_groq(prompt: str, exigir_json: bool = False) -> tuple[str, str]:
    chave_groq = os.getenv("GROQ_API_KEY")
    if not chave_groq:
        raise ValueError("GROQ_API_KEY não configurada no .env")

    cliente = OpenAI(
        api_key=chave_groq,
        base_url="https://api.groq.com/openai/v1",
        timeout=30.0
    )

    modelos_groq = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
    ]

    ultimo_erro = None
    for modelo in modelos_groq:
        try:
            argumentos = {
                "model": modelo,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            if exigir_json:
                argumentos["response_format"] = {"type": "json_object"}

            resposta = cliente.chat.completions.create(**argumentos)
            return f"groq:{modelo}", resposta.choices[0].message.content
        except Exception as erro:
            ultimo_erro = erro
            continue

    raise RuntimeError(f"Todos os modelos Groq falharam: {ultimo_erro}")


def _chamar_gemini(prompt: str, exigir_json: bool = False) -> tuple[str, str]:
    chave_gemini = os.getenv("GEMINI_API_KEY")
    if not chave_gemini:
        raise ValueError("GEMINI_API_KEY não configurada no .env")

    cliente = genai.Client(
        api_key=chave_gemini,
        http_options=types.HttpOptions(timeout=30000)
    )

    configuracao = {"temperature": 0.2}
    if exigir_json:
        configuracao["response_mime_type"] = "application/json"

    modelos_gemini = [
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
    ]

    ultimo_erro = None
    for modelo in modelos_gemini:
        try:
            resposta = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(**configuracao)
            )
            return f"gemini:{modelo}", resposta.text
        except Exception as erro:
            ultimo_erro = erro
            continue

    raise RuntimeError(f"Todos os modelos Gemini falharam: {ultimo_erro}")


def gerar_resposta(prompt: str, exigir_json: bool = False) -> tuple[str, str]:
    """
    Orquestrador com fallback multi-provedor e cascata de modelos.
    Retorna uma tupla: (provedor_modelo_usado, texto_resposta)
    """
    provedores = [
        ("Groq", _chamar_groq),
        ("Gemini", _chamar_gemini),
    ]

    erros = []

    for nome_provedor, funcao_chamada in provedores:
        try:
            return funcao_chamada(prompt, exigir_json=exigir_json)
        except Exception as erro:
            print(f"[Aviso] Falha no provedor {nome_provedor}: {erro}. Acionando fallback...")
            erros.append(f"{nome_provedor}: {erro}")

    raise RuntimeError(f"Todos os provedores de LLM falharam. Detalhes: {' | '.join(erros)}")