# Agente de Ingestão de Sinistro — Semana 1

**Stack:** BAML + LangGraph + Claude
**Objetivo:** receber narrativa livre de sinistro e devolver JSON estruturado auditável, com score de confiança e roteamento determinístico.

---

## O que cada peça faz

### BAML (`baml_src/sinistro.baml`)
Define **o que** o LLM deve devolver (schema) e **como** deve ser pedido (prompt).
Gera um client Python tipado em `baml_client/` — chamar `baml.ExtrairSinistro(narrativa=...)` retorna um objeto Pydantic validado, nunca um JSON torto.

**Por que importa:** elimina 80% dos bugs "LLM inventou campo" / "JSON mal formado". Se o schema quebrar, BAML faz retry estruturado antes de estourar.

### LangGraph (`agent.py`)
Define o **grafo de estados** do agente:
```
START → extrair → decidir_rota ─┬→ pronto_para_analise → END
                                ├→ solicitar_esclarecimento → END
                                └→ escalar_humano → END
```

**Por que importa:** o roteamento é **explícito e determinístico**, não escondido em prompt. Cada nó é uma função Python pura, testável isoladamente.

### Separação neurosimbólica
- **LLM (BAML):** interpreta linguagem natural e extrai estrutura
- **Código (LangGraph):** decide para onde o caso vai, com regras explícitas
- **Zero LLM na decisão de roteamento** — isso é o que previne "as regras não estão sendo aplicadas"

---

## Setup no Mac

```bash
# 1. Python 3.10+ e ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependências
pip install -r requirements.txt

# 3. Variáveis de ambiente
cp .env.example .env
# edita .env e cola sua ANTHROPIC_API_KEY

# 4. Gerar o client BAML a partir do schema
baml-cli generate

# 5. Carregar as env vars e rodar
export $(cat .env | xargs)
python test_narrativas.py
```

## Uso programático

```python
from agent import processar_narrativa

resultado = processar_narrativa(
    "bati minha moto ontem na paulista, perna quebrada, tenho BO"
)

print(resultado["proxima_acao"])       # 'pronto_para_analise'
print(resultado["extracao"].tipo_sinistro)  # 'IAT'
print(resultado["extracao"].confianca)      # 0.85
```

---

## Comandos úteis

```bash
# Rodar os testes built-in do BAML contra o LLM real
baml-cli test

# Regenerar o client após editar o .baml
baml-cli generate

# Ver o playground interativo do BAML
baml-cli dev    # abre http://localhost:2024
```

---

## O que a Semana 1 AINDA NÃO faz (e não deveria)

- ❌ Não decide cobertura (essa é a camada determinística de regras — Semana 3)
- ❌ Não fala com Supabase (ainda local)
- ❌ Não usa Temporal (ainda síncrono)
- ❌ Não expõe MCP (só consome o próprio client BAML)
- ❌ Não tem observabilidade (Langfuse entra na Semana 8)

**Por quê:** cada peça tem que funcionar isolada antes de plugar no resto. Construir tudo junto esconde os bugs de cada camada.

---

## Próximos passos (Semana 2)

1. Adicionar **tools** no agente (consultar apólice mockada, validar CPF/CNH)
2. Agente multi-turno: mantém contexto ao pedir esclarecimento
3. Dataset de 50 narrativas reais + script de eval calculando:
   - Consistency rate (mesma entrada = mesma saída)
   - Accuracy de classificação
   - Precision/recall de red flags
4. Primeira integração: agente lê apólice real via MCP Supabase
