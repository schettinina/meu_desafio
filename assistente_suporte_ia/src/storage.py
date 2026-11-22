import json
import os
from datetime import datetime

CAMINHO_PERFIS = "data/profiles.json"
CAMINHO_HISTORICO = "data/history.json"


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


def buscar_no_cache(cliente_id, duvida, versao_prompt):
    historico = carregar_historico()
    duvida_limpa = duvida.strip().lower()

    # Percorre do mais recente para o mais antigo
    for item in reversed(historico):
        mesmo_cliente = item.get("cliente_id") == cliente_id
        mesma_duvida = item.get("duvida", "").strip().lower() == duvida_limpa
        mesma_versao = item.get("versao_prompt") == versao_prompt

        if mesmo_cliente and mesma_duvida and mesma_versao:
            return item.get("resposta")

    return None


def salvar_interacao(perfil, duvida, versao_prompt, resposta):
    historico = carregar_historico()

    novo_registro = {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente_id": perfil["id"],
        "cliente_nome": perfil["nome"],
        "duvida": duvida.strip(),
        "versao_prompt": versao_prompt,
        "resposta": resposta
    }

    historico.append(novo_registro)

    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=2)