# Notas de Engenharia de Prompt (`PROMPT_ENGINEERING_NOTES.md`)

Este documento detalha as decisões de arquitetura de prompts, as estratégias aplicadas para cada tipo de conteúdo, os resultados da comparação controlada entre as versões `v1` e `v2` e as limitações conhecidas da solução.

---

## 1. Arquitetura e Princípios de Design

Para evitar prompts monolíticos difíceis de manter, os templates foram externalizados do código Python (`prompts/v1_templates.txt` e `prompts/v2_templates.txt`) e divididos em **4 estratégias independentes** (`src/prompt_engine.py`):

1. **`diagnosis` (`gerar_prompt_diagnostico`):** Aplica *Decomposição Estruturada* em 4 blocos obrigatórios (*Hipóteses Levantadas*, *Evidências Disponíveis*, *Dados Faltantes* e *Conclusão Provável*), evitando que o modelo pule direto para conclusões sem evidência.
2. **`resolution_steps` (`gerar_prompt_passo_a_passo`):** Combina *Persona Prompting*, *Regras Condicionais por Canal/Nível* e *Few-Shot Learning* para produzir instruções ordenadas com critérios explícitos de verificação.
3. **`clarifying_questions` (`gerar_prompt_perguntas`):** Restringe o modelo a gerar apenas de 3 a 5 perguntas priorizadas (`P1`, `P2`, `P3`), acompanhadas da justificativa técnica de por que cada dado importa — evitando interrogatórios longos que frustram o cliente.
4. **`visual_flow` (`gerar_prompt_fluxo_visual`):** Orienta a geração de um fluxograma determinístico em ASCII (`[Etapa] --> SIM/NÃO`) seguido de uma síntese adaptada ao nível técnico do usuário.

---

## 2. Evolução das Versões: `v1` vs. `v2`

| Dimensão | Versão `v1` (Baseline Zero-Shot) | Versão `v2` (Estruturada + Guardrails) |
| :--- | :--- | :--- |
| **Técnica principal** | Instrução direta (*zero-shot*) com injeção simples das variáveis do cliente. | *Persona Prompting* + *Context Setting* + *Decomposição de Tarefa* + *Few-Shot* + Restrições Negativas. |
| **Controle de formato** | Aberto; o modelo decide extensão, seções e encerramento. | Rígido; define blocos obrigatórios, regras de canal (`chat`, `e-mail`, `telefone`) e assinatura fixa. |
| **Prevenção de alucinação** | Ausente; tende a inventar preços, URLs e placeholders (`[Seu Nome]`). | Explícita; proíbe invenção de dados não fornecidos, contatos fictícios e placeholders. |

---

## 3. Estudo Comparativo Controlado (Evidência em `/samples`)

Para uma comparação justa, mantivemos constantes o **cliente**, o **ticket**, o **tipo de conteúdo** e o **provedor/modelo**:

- **Cliente:** Totoro (`nível_tecnico: avançado`, `estilo_comunicacao: detalhado`, `canal_preferido: e-mail`)
- **Ticket:** `"meu app esta travando muito, como resolver?"`
- **Tipo de conteúdo:** `resolution_steps`
- **Modelo utilizado:** `groq:openai/gpt-oss-120b` (temperatura `0.2`)
- **Arquivo de evidência:** `samples/comparacao_v1_vs_v2.json`

### Resultados da Rubrica (Escala 1 a 5)

| Critério | Nota `v1` | Nota `v2` | Análise Comparativa |
| :--- | :---: | :---: | :--- |
| **Clareza** | **3 / 5** | **5 / 5** | A `v1` gerou um documento extenso de 8 seções cobrindo múltiplas stacks (Android, iOS, Kotlin, Swift) sem foco. A `v2` seguiu uma estrutura limpa e previsível (validação → passos numerados com verificação → critérios finais). |
| **Adequação ao cliente** | **4 / 5** | **5 / 5** | Ambas usaram vocabulário técnico avançado e formato de e-mail, mas a `v1` deixou placeholders não preenchidos (`[Seu Nome]`, telefone fictício). A `v2` respeitou a assinatura institucional limpa. |
| **Acionabilidade** | **3 / 5** | **5 / 5** | A `v1` misturou coleta de dados, testes de carga e exemplos de código em paralelo. A `v2` ordenou os passos sequencialmente e incluiu uma **Verificação** objetiva em cada etapa. |
| **Média Geral** | **3.33** | **5.00** | Ganho expressivo de previsibilidade, concisão e aderência ao formato na `v2`. |

---

## 4. Decisões Técnicas e Trade-offs

- **Temperatura baixa (`0.2`):** Escolhida para maximizar determinismo, consistência estrutural e adesão aos delimitadores de saída, reduzindo criatividade indesejada em suporte técnico.
- **Resiliência Multi-Provedor (`Groq` → `Gemini`):** Como APIs gratuitas sofrem instabilidades pontuais (`503 UNAVAILABLE` ou *rate limits*), implementamos fallback automático mantendo o registro exato do `provider_model` utilizado em cada execução para garantir rastreabilidade nas comparações.
- **Cache Local Determinístico:** Evita chamadas redundantes quando `(customer_id, ticket, content_type, prompt_version)` são idênticos, reduzindo latência e consumo de cota.

---

## 5. Limitações Conhecidas

1. **Ausência de Base de Conhecimento (RAG):** O assistente opera apenas sobre o relato do ticket e boas práticas gerais de engenharia de software; para produtos proprietários específicos, seria necessário acoplar uma etapa de recuperação (RAG) sobre a documentação oficial do produto.
2. **Cache por Correspondência Exata:** O cache atual normaliza espaços e caixa alta/baixa (`strip().lower()`), mas não detecta paráfrases semânticas (ex.: *"app travando"* vs. *"aplicativo congelando"*).
3. **Validação de Saída via Texto:** As saídas são estruturadas em Markdown/ASCII para leitura humana direta no terminal e na interface web; em uma integração via API REST, seria recomendável forçar *Structured Outputs* (JSON Schema) no modelo.
