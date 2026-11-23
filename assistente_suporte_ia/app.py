import os
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

for chave in ("GROQ_API_KEY", "GEMINI_API_KEY"):
    try:
        valor = st.secrets.get(chave)
        if valor:
            os.environ[chave] = str(valor).strip()
    except Exception:
        pass

from src.llm_client import gerar_resposta
# Garante que os imports relativos e caminhos de dados funcionem tanto localmente quanto no Streamlit Cloud
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Carrega secrets do Streamlit Cloud para variáveis de ambiente se existirem
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

from src.storage import (
    carregar_perfis,
    buscar_no_cache,
    salvar_interacao,
    salvar_amostra_comparacao,
)
from src.prompt_engine import construir_prompt, TIPOS_CONTEUDO
from src.llm_client import gerar_resposta

st.set_page_config(
    page_title="Assistente de Suporte Técnico com IA",
    page_icon="🛠️",
    layout="wide",
)

st.title("Assistente de Suporte Técnico Personalizado")
st.caption("Engenharia de Prompt aplicada ao perfil técnico, estilo de comunicação e canal do cliente.")

perfis = carregar_perfis()
mapa_perfis = {
    f"{p['nome']} ({p['nivel_tecnico']} | {p['estilo_comunicacao']} | {p['canal_preferido']})": p
    for p in perfis
}

# Barra lateral com parâmetros do atendimento
with st.sidebar:
    st.header("Configuração do Atendimento")
    perfil_label = st.selectbox("Perfil do Cliente", list(mapa_perfis.keys()))
    perfil_selecionado = mapa_perfis[perfil_label]

    tipo_conteudo = st.selectbox(
        "Tipo de Conteúdo",
        options=list(TIPOS_CONTEUDO.keys()),
        format_func=lambda k: f"{TIPOS_CONTEUDO[k]} ({k})",
    )

    modo = st.radio(
        "Modo de Execução",
        ["Geração Única", "Comparar v1 vs v2 + Rubrica"],
    )

    versao_unica = "v2"
    if modo == "Geração Única":
        versao_unica = st.selectbox(
            "Versão do Prompt",
            options=["v2", "v1"],
            format_func=lambda v: "v2 (Estruturado + Guardrails)" if v == "v2" else "v1 (Baseline Zero-Shot)",
        )

ticket = st.text_area(
    f"Descreva o ticket / problema de {perfil_selecionado['nome']}:",
    placeholder="Ex.: O aplicativo está travando frequentemente ao abrir a tela de relatórios.",
    height=100,
)

# --- MODO 1: GERAÇÃO ÚNICA ---
if modo == "Geração Única":
    if st.button("Gerar Resposta", type="primary", use_container_width=True):
        if not ticket.strip():
            st.warning("Por favor, descreva o problema do cliente antes de gerar.")
        else:
            item_cache = buscar_no_cache(
                perfil_selecionado["id"], ticket, tipo_conteudo, versao_unica
            )
            if item_cache:
                st.info(
                    f"**Recuperado do Cache** (`data/history.json`) | Modelo: `{item_cache.get('provider_model')}`"
                )
                st.markdown(item_cache.get("output"))
            else:
                with st.spinner(f"Gerando resposta ({versao_unica} | {tipo_conteudo})..."):
                    try:
                        prompt_final = construir_prompt(
                            perfil_selecionado,
                            ticket,
                            versao=versao_unica,
                            tipo_conteudo=tipo_conteudo,
                        )
                        provedor_modelo, resposta = gerar_resposta(prompt_final)
                        caminho_salvo = salvar_interacao(
                            perfil=perfil_selecionado,
                            ticket=ticket,
                            tipo_conteudo=tipo_conteudo,
                            versao_prompt=versao_unica,
                            provedor_modelo=provedor_modelo,
                            saida=resposta,
                        )
                        st.success(
                            f"Gerado via `{provedor_modelo}` e salvo em `{caminho_salvo}`"
                        )
                        st.markdown(resposta)
                    except Exception as erro:
                        st.error(f"Erro ao consultar o modelo: {erro}")

# --- MODO 2: COMPARAÇÃO CONTROLADA + RUBRICA ---
else:
    if st.button("Executar Comparação (v1 vs v2)", type="primary", use_container_width=True):
        if not ticket.strip():
            st.warning("Por favor, descreva o problema do cliente antes de comparar.")
        else:
            with st.spinner("Executando prompts v1 e v2 para o mesmo cenário..."):
                try:
                    resultados_temp = {}
                    for v in ("v1", "v2"):
                        prompt_v = construir_prompt(
                            perfil_selecionado, ticket, versao=v, tipo_conteudo=tipo_conteudo
                        )
                        modelo_v, saida_v = gerar_resposta(prompt_v)
                        resultados_temp[v] = {
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "customer_id": perfil_selecionado["id"],
                            "customer_profile": {
                                "name": perfil_selecionado["nome"],
                                "technical_level": perfil_selecionado["nivel_tecnico"],
                                "communication_style": perfil_selecionado["estilo_comunicacao"],
                                "channel": perfil_selecionado["canal_preferido"],
                            },
                            "ticket": ticket.strip(),
                            "prompt_version": v,
                            "content_type": tipo_conteudo,
                            "provider_model": modelo_v,
                            "output": saida_v,
                        }
                    st.session_state["comparacao_atual"] = resultados_temp
                except Exception as erro:
                    st.error(f"Erro durante a comparação: {erro}")

    if "comparacao_atual" in st.session_state:
        comp = st.session_state["comparacao_atual"]
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Versão v1 (Zero-Shot)")
            st.caption(f"Modelo: `{comp['v1']['provider_model']}`")
            st.markdown(comp["v1"]["output"])

        with col2:
            st.subheader("Versão v2 (Estruturado)")
            st.caption(f"Modelo: `{comp['v2']['provider_model']}`")
            st.markdown(comp["v2"]["output"])

        st.divider()
        st.subheader("Rubrica Obrigatória de Avaliação (Escala 1 a 5)")

        with st.form("form_rubrica"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Notas V1**")
                v1_clar = st.slider("Clareza (v1)", 1, 5, 3)
                v1_clar_j = st.text_input("Justificativa Clareza (v1)", "Resposta funcional, mas menos estruturada.")
                v1_fit = st.slider("Adequação ao Cliente (v1)", 1, 5, 3)
                v1_fit_j = st.text_input("Justificativa Adequação (v1)", "Adaptação parcial ao perfil.")
                v1_act = st.slider("Acionabilidade (v1)", 1, 5, 3)
                v1_act_j = st.text_input("Justificativa Acionabilidade (v1)", "Passos genéricos.")

            with c2:
                st.markdown("**Notas V2**")
                v2_clar = st.slider("Clareza (v2)", 1, 5, 5)
                v2_clar_j = st.text_input("Justificativa Clareza (v2)", "Estrutura clara e previsível.")
                v2_fit = st.slider("Adequação ao Cliente (v2)", 1, 5, 5)
                v2_fit_j = st.text_input("Justificativa Adequação (v2)", "Vocabulário e canal perfeitamente alinhados.")
                v2_act = st.slider("Acionabilidade (v2)", 1, 5, 5)
                v2_act_j = st.text_input("Justificativa Acionabilidade (v2)", "Critérios de verificação claros em cada etapa.")

            if st.form_submit_button("Salvar Avaliação no Histórico e /samples"):
                eval_v1 = {
                    "clarity": {"score": v1_clar, "justification": v1_clar_j},
                    "customer_fit": {"score": v1_fit, "justification": v1_fit_j},
                    "actionability": {"score": v1_act, "justification": v1_act_j},
                }
                eval_v2 = {
                    "clarity": {"score": v2_clar, "justification": v2_clar_j},
                    "customer_fit": {"score": v2_fit, "justification": v2_fit_j},
                    "actionability": {"score": v2_act, "justification": v2_act_j},
                }
                comp["v1"]["evaluation"] = eval_v1
                comp["v2"]["evaluation"] = eval_v2

                salvar_interacao(
                    perfil_selecionado,
                    comp["v1"]["ticket"],
                    comp["v1"]["content_type"],
                    "v1",
                    comp["v1"]["provider_model"],
                    comp["v1"]["output"],
                    eval_v1,
                )
                salvar_interacao(
                    perfil_selecionado,
                    comp["v2"]["ticket"],
                    comp["v2"]["content_type"],
                    "v2",
                    comp["v2"]["provider_model"],
                    comp["v2"]["output"],
                    eval_v2,
                )
                caminho_sample = salvar_amostra_comparacao(comp["v1"], comp["v2"])
                st.success(f"Avaliação salva em `data/history.json` e exportada para `{caminho_sample}`!")