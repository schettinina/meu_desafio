# Assistente de Suporte Técnico Personalizado com IA

Aplicação CLI em Python que utiliza **Engenharia de Prompt** para adaptar diagnósticos, passos de resolução, perguntas de triagem e fluxos visuais ao perfil técnico, estilo de comunicação e canal de atendimento de cada cliente.

---
**Aplicação Online (Demo Interativa):** [Acessar Assistente no Streamlit Cloud](https://meudesafio-bvsatqu8gozbfzjm5k6fcf.streamlit.app/)

Aplicação em Python (**CLI** e **Interface Web Streamlit**) que utiliza **Engenharia de Prompt** para adaptar diagnósticos técnicos, passos de resolução, perguntas de triagem e fluxos visuais ao perfil técnico, estilo de comunicação e canal preferido de cada cliente.

---
## Funcionalidades Principais

- **Perfis de Cliente Configuráveis (`data/profiles.json`):** 5 perfis pré-cadastrados combinando níveis técnicos (`leigo`, `intermediário`, `avançado`), estilos (`direto`, `detalhado`, `didático`) e canais (`chat`, `e-mail`, `telefone`).
- **4 Estratégias Especializadas de Conteúdo (`src/prompt_engine.py`):**
  1. `diagnosis` — Diagnóstico estruturado (hipóteses, evidências, dados faltantes e conclusão provável).
  2. `resolution_steps` — Passo a passo de resolução adaptado ao nível e canal do cliente.
  3. `clarifying_questions` — Perguntas de esclarecimento priorizadas (`P1` a `P3`).
  4. `visual_flow` — Fluxograma de decisão em ASCII e resumo das bifurcações.
- **Versionamento e Comparação Controlada (`v1` vs. `v2`):** Modo dedicado para comparar duas versões de prompt sob as mesmas condições (cliente, ticket, tipo de conteúdo e modelo) e registrar a avaliação na rubrica obrigatória de 3 critérios (*Clareza*, *Adequação ao Cliente* e *Acionabilidade*).
- **Persistência e Cache Inteligente (`src/storage.py`):** Armazena todas as execuções em `data/history.json` com `timestamp`, perfil, versão do prompt, `provider_model` e reutiliza resultados equivalentes sem gastar chamadas extras de API.
- **Fallback Multi-Provedor (`src/llm_client.py`):** Orquestrador com cascata automática entre **Groq** (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`) e **Google Gemini** (`gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-flash-lite-latest`).

---

## Estrutura do Projeto

assistente_suporte_ia/
├── data/
│   ├── profiles.json                 # Perfis de clientes (3 a 5 perfis)
│   └── history.json                  # Histórico e cache persistente das execuções
├── prompts/
│   ├── v1_templates.txt              # Templates v1 (baseline zero-shot)
│   └── v2_templates.txt              # Templates v2 (persona, regras, few-shot e guardrails)
├── samples/
│   └── comparacao_v1_vs_v2.json      # Evidência de comparação controlada com rubrica
├── src/
│   ├── main.py                       # Interface CLI e fluxo de comparação/rubrica
│   ├── prompt_engine.py              # 4 estratégias de prompt + injeção de contexto
│   ├── llm_client.py                 # Cliente LLM com fallback Groq -> Gemini
│   └── storage.py                    # Persistência JSON, cache e exportação de amostras
├── .env.example                      # Exemplo das variáveis de ambiente necessárias
├── PROMPT_ENGINEERING_NOTES.md       # Documentação detalhada das decisões de prompt
├── requirements.txt                  # Dependências Python do projeto
└── README.md                         # Instruções de setup, arquitetura e uso

---

## Setup e Execução

### 1. Pré-requisitos
- Python 3.9 ou superior
- Chave de API da **Groq** (`GROQ_API_KEY`) e/ou **Google Gemini** (`GEMINI_API_KEY`)

### 2. Instalação das dependências

git clone <url-do-repositorio>
cd assistente_suporte_ia
pip3 install -r requirements.txt

### 3. Configuração das variáveis de ambiente
Copie o arquivo de exemplo e adicione suas chaves reais no `.env`:

cp .env.example .env

Conteúdo do `.env`:

GROQ_API_KEY=sua_chave_groq_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui

### 4. Executando a aplicação
A partir da raiz do projeto, execute:

python3 -m src.main

---

## Exemplos de Uso

### Fluxo 1: Geração Individual + Cache
1. Selecione um cliente (ex.: `1. Maria` — *leigo | direto | chat*).
2. Escolha o tipo de conteúdo (ex.: `1. Diagnóstico do problema`).
3. Escolha o modo `1. Gerar resposta única` e informe o ticket (ex.: *"Não consigo entrar na minha conta, dá erro ao colocar a senha"*).
4. Repita a mesma consulta para observar a mensagem `[CACHE] Resposta recuperada de data/history.json` sem nova chamada de API.

### Fluxo 2: Comparação `v1` vs. `v2` com Rubrica
1. Selecione um cliente (ex.: `2. Totoro` — *avançado | detalhado | e-mail*).
2. Escolha o tipo de conteúdo (ex.: `2. Passo a passo de resolução`).
3. Escolha o modo `2. Comparar v1 vs v2 lado a lado + Aplicar Rubrica`.
4. Avalie ambas as respostas nos 3 critérios (escala 1 a 5) com justificativas; o resultado consolidado será salvo automaticamente em `samples/comparacao_v1_vs_v2.json`.

---

## Documentação Complementar
Para detalhes sobre a engenharia de prompts, métricas da comparação controlada e limitações da solução, consulte [`PROMPT_ENGINEERING_NOTES.md`](./PROMPT_ENGINEERING_NOTES.md).