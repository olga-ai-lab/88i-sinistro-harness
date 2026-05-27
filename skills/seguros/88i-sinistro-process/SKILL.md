---
name: 88i-sinistro-process
description: "Orquestra fluxo completo de sinistro 88i (triagem → extração → validação → fraude → decisão → reembolso). Use quando receber novo sinistro ou precisar reprocessar um existente. Trigger em: 'processar sinistro', 'novo sinistro', 'fluxo sinistro', 'análise completa', 'sinistro do zero', 'reprocessar', 'workflow sinistro'."
version: 1.0.0
author: Olga AI Lab
license: MIT
metadata:
  hermes:
    tags: [seguros, sinistros, 88i, workflow, orquestração]
    related_skills: [sinistro-analyzer, fraude-detector, sinistro-doc-classifier, sinistro-doc-forensics, sinistro-claim-adjudicator, olga-analista-seguros-88i]
---

# Orquestrador de Sinistro — Workflow Completo 88i

## Overview

Skill **orchestrator** que coordena o **fluxo end-to-end** de um sinistro na 88i Seguradora:

```
┌─────────────────────────────────────────────────────────────┐
│                    NOVO SINISTRO                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼─────────────┐
        │  1. TRIAGEM DOCUMENTAL    │  ← sinistro-doc-classifier
        │  (Qual tipo? Qualidade?)  │
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  2. EXTRAÇÃO DE CAMPOS    │  ← sinistro-analyzer
        │  (Estruturar JSON)        │
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  3. VALIDAÇÃO DOCUMENTAL  │  ← sinistro-doc-forensics
        │  (Autenticidade? Campos?) │
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  4. SCORING DE FRAUDE     │  ← fraude-detector
        │  (Risco? Inconsistências?)│
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  5. ANÁLISE DE COBERTURA  │  ← olga-analista-seguros-88i
        │  (Qual cobertura? Regras?)│
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  6. DECISÃO OPERACIONAL   │  ← sinistro-claim-adjudicator
        │  (Aprova? Nega? Manual?)  │
        └────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  7. FORMALIZAÇÃO & AVISO  │  ← supabase_tool
        │  (Atualiza BD, notifica)  │
        └─────────────────────────────┘
```

## When to Use

- ✅ **Novo sinistro** chegou (email, webhook, upload)
- ✅ **Precisa** análise completa = aprovação/rejeição/manual
- ✅ **Documentação** está completa (todos docs recebidos)
- ✅ **Segurado** solicitou reprocessamento

### Não use para:

- ❌ Apenas **1 etapa** (ex: só validar doc) — use skill específica
- ❌ **Documentação** incompleta — aguarde todos documentos
- ❌ **Análise rápida** sem rigor — use reviews manuais

## 7 Etapas do Workflow

### 1️⃣ **TRIAGEM DOCUMENTAL**

**Entrada:** Imagem/PDF do documento  
**Skill:** `sinistro-doc-classifier`  
**Saída:** Tipo documental + qualidade + campos esperados

```python
triagem = await sinistro_doc_classifier(
    imagem="documento.pdf",
    contexto_sinistro={
        "tipo_veiculo": "moto",
        "tipo_sinistro": "roubo"
    }
)
# Retorna:
# {
#   "tipo": "boletim",
#   "qualidade": "boa",
#   "campos_obrigatorios": ["numero_bo", "data", "tipo_crime", "vitima"],
#   "confianca": 0.96
# }
```

### 2️⃣ **EXTRAÇÃO DE CAMPOS**

**Entrada:** Documento classificado + imagem  
**Skill:** `sinistro-analyzer`  
**Saída:** JSON estruturado com campos extraídos

```python
extracao = await sinistro_analyzer(
    tipo_doc=triagem["tipo"],  # "boletim"
    imagem=imagem_bytes,
    campos_alvo=triagem["campos_obrigatorios"]
)
# Retorna:
# {
#   "numero_bo": "123456789",
#   "data_ocorrencia": "2026-05-15",
#   "tipo_crime": "roubo",
#   "vitima": {"nome": "João", "cpf": "123..."},
#   "bens_roubados": [...],
#   "qualidade_imagem": "boa",
#   "confianca_extracao": 0.94
# }
```

### 3️⃣ **VALIDAÇÃO DOCUMENTAL**

**Entrada:** Dados extraídos + histórico segurado  
**Skill:** `sinistro-doc-forensics`  
**Saída:** Sinais de suspeita + validações de campo

```python
validacao = await sinistro_doc_forensics(
    tipo_doc=triagem["tipo"],
    dados_extraidos=extracao,
    historico_segurado=supabase_get_segurado(cpf)
)
# Retorna:
# {
#   "autenticidade": "legítimo",
#   "campos_validados": {
#     "numero_bo": {"valido": true, "formato": "ok"},
#     "data_ocorrencia": {"valido": true, "vigencia_ok": true}
#   },
#   "sinais_suspeita": [],
#   "validacao_geral": "PASSA"
# }
```

### 4️⃣ **SCORING DE FRAUDE**

**Entrada:** Dados validados + histórico comportamental  
**Skill:** `fraude-detector`  
**Saída:** Score 0.0-1.0 + categoria risco

```python
fraude = await fraude_detector(
    dados_sinistro=extracao,
    historico_segurado=supabase_get_segurado(cpf),
    tipo_sinistro="roubo"
)
# Retorna:
# {
#   "score_fraude": 0.15,
#   "categoria": "BAIXO",
#   "temporal_score": 0.10,
#   "estrutural_score": 0.08,
#   "comportamental_score": 0.20,
#   "recomendacao": "aprovação"
# }
```

### 5️⃣ **ANÁLISE DE COBERTURA**

**Entrada:** Dados sinistro + regime segurado + plataforma  
**Skill:** `olga-analista-seguros-88i`  
**Saída:** Cobertura aplicável + regras + condições

```python
cobertura = await olga_analista_seguros_88i(
    tipo_sinistro="roubo_veiculo",
    regime=segurado["regime"],  # "uber" or "padrao"
    plataforma=segurado["plataforma"],  # "uber", "99", "iFood"
    tipo_veiculo=extracao["veiculo"]["tipo"],  # "moto"
    valor_sinistro=laudo["valor_estimado"],
    data_inicio_vigencia=bilhete["data_inicio"],
    data_sinistro=extracao["data_ocorrencia"]
)
# Retorna:
# {
#   "cobertura_aplicavel": "Cobertura I - Roubo Veículo",
#   "regime_aplica": "UBER",
#   "franquia": 0,
#   "limite_indenizacao": 15000,
#   "regras_aplicaveis": [
#     "30 dias cooldown após retorno",
#     "Somente automóveis",
#     "Vigência deve estar ativa"
#   ],
#   "situacao_cobertura": "COBERTO"
# }
```

### 6️⃣ **DECISÃO OPERACIONAL**

**Entrada:** Tudo acima + análise final  
**Skill:** `sinistro-claim-adjudicator`  
**Saída:** Aprovação/rejeição + justificativa + próximo passo

```python
decisao = await sinistro_claim_adjudicator(
    extracao_documental=extracao,
    validacao_documental=validacao,
    fraude_score=fraude,
    cobertura_analise=cobertura,
    historico_sinistros=supabase_get_sinistros(cpf),
    tipo_operacao="primeira_analise"
)
# Retorna:
# {
#   "recomendacao": "APROVACAO",
#   "justificativa": [
#     "Documentação completa e validada",
#     "Score fraude baixo (0.15)",
#     "Cobertura aplicável (Roubo Veículo)",
#     "Histórico segurado limpo"
#   ],
#   "valor_indenizacao": 8500,
#   "proximos_passos": [
#     "Enviar comprovante para assinatura digital",
#     "Registrar reembolso no sistema",
#     "Notificar segurado"
#   ]
# }
```

### 7️⃣ **FORMALIZAÇÃO & AVISO**

**Entrada:** Decisão final  
**Ferramentas:** `supabase_tool`, email, Inngest  
**Saída:** Sinistro registrado + segurado notificado

```python
# Atualizar Supabase
await supabase_update_sinistro({
    "id": sinistro_id,
    "status": "APROVADO",
    "valor_indenizacao": decisao["valor_indenizacao"],
    "data_decisao": datetime.now(),
    "score_fraude": fraude["score_fraude"],
    "scoring_completo": {
        "temporal": fraude["temporal_score"],
        "estrutural": fraude["estrutural_score"],
        "comportamental": fraude["comportamental_score"]
    },
    "analista_responsavel": "agent_88i_v1"
})

# Disparar workflow Inngest (reembolso)
await inngest_trigger_reembolso({
    "sinistro_id": sinistro_id,
    "segurado_id": extracao["cpf"],
    "valor": decisao["valor_indenizacao"]
})

# Notificar via email/SMS
await enviar_notificacao({
    "tipo": "decisao_sinistro",
    "segurado_id": extracao["cpf"],
    "status": "APROVADO",
    "valor": decisao["valor_indenizacao"],
    "pix_key": segurado["pix_key"]  # Se tiver
})
```

## Implementação em Python

### Arquivo: `scripts/process_sinistro_88i.py`

```python
import asyncio
from baml_client import baml
from tools.supabase_tool import supabase_get_segurado, supabase_update_sinistro
from tools.inngest_tool import inngest_trigger_reembolso

async def process_sinistro_88i(sinistro_id: str, documento_paths: list):
    """
    Orquestra workflow completo de sinistro
    
    Args:
        sinistro_id: ID único do sinistro (ex: CLM-2026-001234)
        documento_paths: Lista de caminhos (imagens/PDFs)
    
    Returns:
        dict com resultado final e histórico de análise
    """
    
    # 1. TRIAGEM
    print(f"[1/7] Triagem documental para {sinistro_id}...")
    triagens = []
    for doc_path in documento_paths:
        triagem = await baml.classificador_documento(
            imagem_path=doc_path
        )
        triagens.append(triagem)
    
    # 2. EXTRAÇÃO
    print("[2/7] Extração de campos...")
    extrações = []
    for triagem, doc_path in zip(triagens, documento_paths):
        extracao = await baml.extrator_documental(
            tipo_doc=triagem["tipo"],
            imagem_path=doc_path
        )
        extrações.append(extracao)
    
    # 3. VALIDAÇÃO
    print("[3/7] Validação documental...")
    validações = []
    for extracao in extrações:
        validacao = await baml.validador_forense(
            tipo_doc=extracao["tipo"],
            dados=extracao
        )
        validações.append(validacao)
    
    # Recuperar histórico
    segurado = await supabase_get_segurado(extrações[0]["cpf"])
    
    # 4. FRAUDE
    print("[4/7] Scoring de fraude...")
    fraude = await baml.fraude_analyzer(
        dados=extrações[0],  # Principal
        historico=segurado,
        tipo_sinistro=extrações[0]["tipo_sinistro"]
    )
    
    # 5. COBERTURA
    print("[5/7] Análise de cobertura...")
    cobertura = await baml.analista_cobertura(
        regime=segurado["regime"],
        plataforma=segurado["plataforma"],
        tipo_veiculo=extrações[0]["veiculo"]["tipo"],
        data_sinistro=extrações[0]["data_ocorrencia"],
        data_vigencia=segurado["data_inicio"]
    )
    
    # 6. DECISÃO
    print("[6/7] Decisão operacional...")
    decisao = await baml.adjudicador_sinistro(
        extracao=extrações[0],
        validacao=validações[0],
        fraude=fraude,
        cobertura=cobertura,
        historico_sinistros=segurado["sinistros"]
    )
    
    # 7. FORMALIZAÇÃO
    print("[7/7] Formalização e aviso...")
    await supabase_update_sinistro({
        "id": sinistro_id,
        "status": decisao["recomendacao"],
        "valor_indenizacao": decisao.get("valor_indenizacao"),
        "analise_completa": {
            "triagem": triagens,
            "extracao": extrações,
            "validacao": validações,
            "fraude": fraude,
            "cobertura": cobertura,
            "decisao": decisao
        }
    })
    
    if decisao["recomendacao"] == "APROVACAO":
        await inngest_trigger_reembolso({
            "sinistro_id": sinistro_id,
            "valor": decisao["valor_indenizacao"]
        })
    
    print(f"\n✅ Sinistro {sinistro_id}: {decisao['recomendacao']}")
    return decisao

# Execução
if __name__ == "__main__":
    resultado = asyncio.run(process_sinistro_88i(
        sinistro_id="CLM-2026-001234",
        documento_paths=[
            "boletim.pdf",
            "laudo.pdf",
            "nf.pdf",
            "crlv.pdf"
        ]
    ))
    print(resultado)
```

## Common Pitfalls

1. **Saltar etapas se falhar uma**
   - Solução: SEMPRE fazer todas 7, marcar falhas no registro

2. **Não documentar cada etapa**
   - Solução: guardar output de cada skill no histórico

3. **Timeout em processamento de imagem**
   - Solução: timeout = 60s, retry 2x, fallback manual

4. **Usar dados antigos (cache segurado desatualizado)**
   - Solução: sempre `supabase_get_segurado()` fresh antes de análise

5. **Não rollback em erro**
   - Solução: transaction SQL, ou marcar status como "ERRO" para reprocessar

6. **Confundir decisão automática com manual**
   - Solução: sempre incluir "precisa_analista" na saída se score inconcluso

## Verification Checklist

- [ ] Todos 7 passos foram executados
- [ ] Cada etapa tem output documentado
- [ ] Score fraude está entre 0.0-1.0
- [ ] Cobertura foi verificada contra regime/plataforma
- [ ] Decisão tem justificativa clara
- [ ] Se aprovado: Inngest workflow foi disparado
- [ ] Supabase foi atualizado com status final
- [ ] Segurado foi notificado (email/SMS/dashboard)
- [ ] Relatório completo foi gerado

## One-Shot Recipe: Processar Novo Sinistro

```bash
hermes skill 88i-sinistro-process

# INPUT
sinistro_id: "CLM-2026-001234"
documentos: [
  { "path": "boletim.pdf", "tipo": "documento_original" },
  { "path": "laudo.jpg", "tipo": "documento_original" },
  { "path": "nf.pdf", "tipo": "documento_original" },
  { "path": "crlv.jpg", "tipo": "documento_original" }
]

# EXECUTE
[88i-sinistro-process] → dispara todas 7 etapas em sequência

# OUTPUT
{
  "sinistro_id": "CLM-2026-001234",
  "status": "APROVADO",
  "valor_indenizacao": 8500,
  "score_fraude": 0.15,
  "categoria_fraude": "BAIXO",
  "cobertura": "Roubo Veículo",
  "analista_responsavel": "agent_88i_v1",
  "timestamp": "2026-05-27T14:30:00Z",
  "proximos_passos": [
    "Enviar comprovante para assinatura",
    "Processar reembolso",
    "Notificar segurado"
  ]
}
```
