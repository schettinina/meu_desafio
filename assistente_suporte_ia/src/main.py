from datetime import datetime
from src.storage import (
    carregar_perfis,
    buscar_no_cache,
    salvar_interacao,
    salvar_amostra_comparacao,
)
from src.prompt_engine import construir_prompt, TIPOS_CONTEUDO
from src.llm_client import gerar_resposta


def escolher_perfil(perfis):
    print("\n=== CLIENTES DISPONÍVEIS ===")
    for indice, perfil in enumerate(perfis, start=1):
        print(
            f"{indice}. {perfil['nome']} "
            f"(Nível: {perfil['nivel_tecnico']} | Estilo: {perfil['estilo_comunicacao']} | Canal: {perfil['canal_preferido']})"
        )

    while True:
        escolha = input("\nEscolha o número do cliente (ou 'sair'): ").strip().lower()
        if escolha == "sair":
            return None
        if escolha.isdigit() and 1 <= int(escolha) <= len(perfis):
            return perfis[int(escolha) - 1]
        print("Opção inválida. Digite o número correspondente ao cliente.")


def escolher_tipo_conteudo():
    chaves = list(TIPOS_CONTEUDO.keys())
    print("\n=== TIPO DE CONTEÚDO A GERAR ===")
    for idx, chave in enumerate(chaves, start=1):
        print(f"{idx}. {TIPOS_CONTEUDO[chave]} ({chave})")

    while True:
        opcao = input("Escolha (1 a 4): ").strip()
        if opcao.isdigit() and 1 <= int(opcao) <= len(chaves):
            return chaves[int(opcao) - 1]
        print("Opção inválida. Digite um número de 1 a 4.")


def escolher_modo():
    print("\n=== MODO DE EXECUÇÃO ===")
    print("1. Gerar resposta única (escolher v1 ou v2)")
    print("2. Comparar v1 vs v2 lado a lado + Aplicar Rubrica (gera amostra em /samples)")
    while True:
        opcao = input("Escolha (1 ou 2) [padrão 1]: ").strip() or "1"
        if opcao in ("1", "2"):
            return opcao
        print("Opção inválida. Digite 1 ou 2.")


def escolher_versao_prompt():
    print("\nVersão do prompt:")
    print("1. v1 (Zero-shot básico)")
    print("2. v2 (Estruturado: Persona + Contexto + Regras + Few-shot)")
    opcao = input("Escolha (1 ou 2) [padrão 2]: ").strip()
    return "v1" if opcao == "1" else "v2"


def coletar_rubrica(versao: str) -> dict:
    print(f"\n--- RUBRICA OBRIGATÓRIA PARA VERSÃO {versao.upper()} (Escala 1 a 5) ---")
    criterios = [
        ("clarity", "Clareza (compreensível, organizada e sem ambiguidade?)"),
        ("customer_fit", "Adequação ao nível do cliente (vocabulário e profundidade combinam?)"),
        ("actionability", "Acionabilidade (cliente/atendente sabe exatamente o que fazer?)"),
    ]
    avaliacao = {}
    for chave, descricao in criterios:
        while True:
            nota_str = input(f"Nota para {descricao} [1-5]: ").strip()
            if nota_str.isdigit() and 1 <= int(nota_str) <= 5:
                nota = int(nota_str)
                break
            print("Digite um número inteiro de 1 a 5.")
        justificativa = input(f"Justificativa curta para '{chave}': ").strip()
        avaliacao[chave] = {
            "score": nota,
            "justification": justificativa or "Sem justificativa adicional.",
        }
    return avaliacao


def executar_geracao_unica(perfil: dict, ticket: str, tipo_conteudo: str, versao: str):
    item_cache = buscar_no_cache(perfil["id"], ticket, tipo_conteudo, versao)
    if item_cache:
        print(f"\n[CACHE] Resposta recuperada de data/history.json (Modelo: {item_cache.get('provider_model')}):")
        print("-" * 60)
        print(item_cache.get("output"))
        print("-" * 60)
        return

    print(f"\nConsultando LLM ({versao} | {tipo_conteudo})...")
    prompt_final = construir_prompt(perfil, ticket, versao=versao, tipo_conteudo=tipo_conteudo)
    provedor_modelo, resposta = gerar_resposta(prompt_final)

    caminho_salvo = salvar_interacao(
        perfil=perfil,
        ticket=ticket,
        tipo_conteudo=tipo_conteudo,
        versao_prompt=versao,
        provedor_modelo=provedor_modelo,
        saida=resposta,
    )

    print(f"\n[RESPOSTA | Cliente: {perfil['nome']} | Tipo: {tipo_conteudo} | Prompt: {versao} | Modelo: {provedor_modelo}]")
    print("-" * 60)
    print(resposta)
    print("-" * 60)
    print(f"Resultado salvo em: {caminho_salvo}")


def executar_comparacao(perfil: dict, ticket: str, tipo_conteudo: str):
    print(f"\nExecutando comparação controlada (v1 vs v2) para {perfil['nome']} | {tipo_conteudo}...")
    resultados = {}

    for versao in ("v1", "v2"):
        print(f"\n>>> Gerando saída com prompt {versao}...")
        prompt_final = construir_prompt(perfil, ticket, versao=versao, tipo_conteudo=tipo_conteudo)
        provedor_modelo, resposta = gerar_resposta(prompt_final)

        print(f"\n[SAÍDA {versao.upper()} | Modelo: {provedor_modelo}]")
        print("-" * 60)
        print(resposta)
        print("-" * 60)

        avaliacao = coletar_rubrica(versao)
        caminho_salvo = salvar_interacao(
            perfil=perfil,
            ticket=ticket,
            tipo_conteudo=tipo_conteudo,
            versao_prompt=versao,
            provedor_modelo=provedor_modelo,
            saida=resposta,
            avaliacao=avaliacao,
        )

        resultados[versao] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "customer_id": perfil["id"],
            "customer_profile": {
                "name": perfil["nome"],
                "technical_level": perfil["nivel_tecnico"],
                "communication_style": perfil["estilo_comunicacao"],
                "channel": perfil["canal_preferido"],
            },
            "ticket": ticket.strip(),
            "prompt_version": versao,
            "content_type": tipo_conteudo,
            "provider_model": provedor_modelo,
            "output": resposta,
            "evaluation": avaliacao,
        }
        print(f"Registro {versao} salvo em: {caminho_salvo}")

    caminho_sample = salvar_amostra_comparacao(resultados["v1"], resultados["v2"])
    print(f"\nComparação completa exportada com sucesso para: {caminho_sample}")


def iniciar_assistente():
    perfis = carregar_perfis()
    print("=== ASSISTENTE DE SUPORTE TÉCNICO COM IA ===")

    while True:
        perfil = escolher_perfil(perfis)
        if perfil is None:
            print("\nEncerrando o assistente. Até logo!")
            break

        tipo_conteudo = escolher_tipo_conteudo()
        modo = escolher_modo()
        ticket = input(f"\nDescreva o ticket/problema de {perfil['nome']}: ").strip()

        if not ticket:
            print("O ticket não pode ficar em branco.")
            continue

        try:
            if modo == "2":
                executar_comparacao(perfil, ticket, tipo_conteudo)
            else:
                versao = escolher_versao_prompt()
                executar_geracao_unica(perfil, ticket, tipo_conteudo, versao)
        except Exception as erro:
            print(f"\nErro durante a execução: {erro}")


if __name__ == "__main__":
    iniciar_assistente()