from pathlib import Path

PASTA_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"

TIPOS_CONTEUDO = {
    "diagnosis": "Diagnóstico do problema",
    "resolution_steps": "Passo a passo de resolução",
    "clarifying_questions": "Perguntas de esclarecimento",
    "visual_flow": "Resumo visual do fluxo",
}


def _carregar_secao_template(versao: str, tipo_conteudo: str) -> str:
    arquivo = "v1_templates.txt" if versao in ("v1", "v1_basico") else "v2_templates.txt"
    caminho = PASTA_PROMPTS / arquivo

    if not caminho.exists():
        raise FileNotFoundError(f"Template de prompt não encontrado: {caminho}")

    conteudo = caminho.read_text(encoding="utf-8")
    marcador = f"==={tipo_conteudo}==="

    if marcador not in conteudo:
        raise ValueError(f"Seção '{tipo_conteudo}' não encontrada em {arquivo}")

    trecho = conteudo.split(marcador, 1)[1]
    if "===" in trecho:
        trecho = trecho.split("\n===", 1)[0]

    return trecho.strip()


def _preencher_contexto(template: str, perfil: dict, duvida: str) -> str:
    return template.format(
        nome=perfil.get("nome", "Cliente"),
        nivel_tecnico=perfil.get("nivel_tecnico", "intermediário"),
        estilo_comunicacao=perfil.get("estilo_comunicacao", "direto"),
        canal_preferido=perfil.get("canal_preferido", "chat"),
        duvida=duvida.strip(),
    )


def gerar_prompt_diagnostico(perfil: dict, duvida: str, versao: str = "v2") -> str:
    """Estratégia 1: Diagnóstico estruturado (hipóteses, evidências, dados faltantes, conclusão)."""
    template = _carregar_secao_template(versao, "diagnosis")
    return _preencher_contexto(template, perfil, duvida)


def gerar_prompt_passo_a_passo(perfil: dict, duvida: str, versao: str = "v2") -> str:
    """Estratégia 2: Passo a passo de resolução adaptado ao nível e estilo do cliente."""
    template = _carregar_secao_template(versao, "resolution_steps")
    return _preencher_contexto(template, perfil, duvida)


def gerar_prompt_perguntas(perfil: dict, duvida: str, versao: str = "v2") -> str:
    """Estratégia 3: Perguntas de esclarecimento priorizadas."""
    template = _carregar_secao_template(versao, "clarifying_questions")
    return _preencher_contexto(template, perfil, duvida)


def gerar_prompt_fluxo_visual(perfil: dict, duvida: str, versao: str = "v2") -> str:
    """Estratégia 4: Fluxograma ASCII e árvore de decisão."""
    template = _carregar_secao_template(versao, "visual_flow")
    return _preencher_contexto(template, perfil, duvida)


def construir_prompt(
    perfil: dict,
    duvida: str,
    versao: str = "v2",
    tipo_conteudo: str = "diagnosis"
) -> str:
    """Roteador central que delega para cada uma das 4 estratégias especializadas."""
    estrategias = {
        "diagnosis": gerar_prompt_diagnostico,
        "resolution_steps": gerar_prompt_passo_a_passo,
        "clarifying_questions": gerar_prompt_perguntas,
        "visual_flow": gerar_prompt_fluxo_visual,
    }

    if tipo_conteudo not in estrategias:
        raise ValueError(f"Tipo de conteúdo inválido: {tipo_conteudo}")

    return estrategias[tipo_conteudo](perfil, duvida, versao)