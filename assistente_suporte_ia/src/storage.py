import json
import os
from datetime import datetime

CAMINHO_PERFIS = "data/profiles.json"
CAMINHO_HISTORICO = "data/history.json"
PASTA_SAMPLES = "samples"


def carregar_perfis():
    with open(CAMINHO_PERFIS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_historico():
    if not os.path.exists(CAMINHO_HISTORICO):
        return []
    try:
        with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError:
        return []


def buscar_no_cache(cliente_id: str, ticket: str, tipo_conteudo: str, versao_prompt: str):
    """
    Localiza execução equivalente (mesmo cliente, ticket, tipo de conteúdo e versão de prompt)
    para reutilização sem nova chamada de API.
    """
    historico = carregar_historico()
    ticket_limpo = ticket.strip().lower()

    for item in reversed(historico):
        mesmo_cliente = item.get("customer_id") == cliente_id
        mesmo_ticket = item.get("ticket", "").strip().lower() == ticket_limpo
        mesmo_tipo = item.get("content_type") == tipo_conteudo
        mesma_versao = item.get("prompt_version") == versao_prompt

        if mesmo_cliente and mesmo_ticket and mesmo_tipo and mesma_versao:
            return item

    return None


def salvar_interacao(
    perfil: dict,
    ticket: str,
    tipo_conteudo: str,
    versao_prompt: str,
    provedor_modelo: str,
    saida: str,
    avaliacao: dict = None
) -> str:
    """
    Persiste a execução em JSON seguindo o schema estruturado do desafio
    e retorna o caminho do arquivo salvo.
    """
    os.makedirs(os.path.dirname(CAMINHO_HISTORICO), exist_ok=True)
    historico = carregar_historico()

    novo_registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "customer_id": perfil["id"],
        "customer_profile": {
            "name": perfil["nome"],
            "technical_level": perfil["nivel_tecnico"],
            "communication_style": perfil["estilo_comunicacao"],
            "channel": perfil["canal_preferido"],
        },
        "ticket": ticket.strip(),
        "prompt_version": versao_prompt,
        "content_type": tipo_conteudo,
        "provider_model": provedor_modelo,
        "output": saida,
    }

    if avaliacao:
        novo_registro["evaluation"] = avaliacao

    historico.append(novo_registro)

    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=2)

    return CAMINHO_HISTORICO


def salvar_amostra_comparacao(registro_v1: dict, registro_v2: dict) -> str:
    """
    Exporta a comparação completa (v1 vs v2 com rubrica) para o diretório /samples
    conforme exigido na entrega do desafio.
    """
    os.makedirs(PASTA_SAMPLES, exist_ok=True)
    caminho_amostra = os.path.join(PASTA_SAMPLES, "comparacao_v1_vs_v2.json")

    payload = {
        "comparison_metadata": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "customer_id": registro_v1["customer_id"],
            "customer_profile": registro_v1["customer_profile"],
            "ticket": registro_v1["ticket"],
            "content_type": registro_v1["content_type"],
            "provider_model_v1": registro_v1["provider_model"],
            "provider_model_v2": registro_v2["provider_model"],
        },
        "results": [registro_v1, registro_v2],
    }

    with open(caminho_amostra, "w", encoding="utf-8") as arquivo:
        json.dump(payload, arquivo, ensure_ascii=False, indent=2)

    return caminho_amostra