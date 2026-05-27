---
name: fraude-detector
description: "Identifica padrões de risco e suspeita em sinistros 88i (inconsistências temporais, dados incoerentes, sinais comportamentais). Use quando houver dados estruturados de um sinistro (campos extraídos + histórico segurado) e for preciso scoring de risco. Trigger em: 'fraude', 'suspeita', 'risco', 'inconsistência', 'possível fraude', 'análise de risco', 'validação de coerência'."
version: 1.0.0
author: Olga AI Lab
license: MIT
metadata:
  hermes:
    tags: [seguros, sinistros, 88i, fraude, análise-risco]
    related_skills: [sinistro-analyzer, sinistro-doc-forensics, sinistro-claim-adjudicator]
---

# Detector de Fraude & Risco — Sinistros 88i

## Overview

Skill especializada em **scoring de risco** e **detecção de padrões suspeitos** em sinistros 88i.

Diferente de `sinistro-doc-forensics` (que valida **autenticidade documental**), **fraude-detector** avalia **coerência lógica + comportamento segurado** para assinalar sinistros de risco.

Usa **3 dimensões de análise:**
1. **Temporal** — datas inconsistentes, timing suspeito
2. **Estrutural** — dados contraditórios entre documentos
3. **Comportamental** — padrão de sinistros, frequência anômala

## When to Use

- ✅ **Dados extraídos** já disponíveis (campos estruturados do sinistro)
- ✅ **Histórico segurado** acessível (sinistros anteriores, prêmios)
- ✅ **Precisa** scoring quantitativo de risco (0.0 - 1.0)
- ✅ **Próximo passo** é decisão de cobertura

### Não use para:

- ❌ Validação de documento original (use `sinistro-doc-forensics`)
- ❌ Extração de campos (use `sinistro-analyzer`)
- ❌ Decisão operacional final (use `sinistro-claim-adjudicator`)

## 3 Dimensões de Análise

### 1️⃣ **TEMPORAL** — Datas & Timing

```python
# Sinais de suspeita:

✅ BOM:      Sinistro ocorre durante vigência → cobertura possível
⚠️  SUSPEITO: Sinistro 3 dias ANTES de contratação → cobertura negada

✅ BOM:      Aviso prévio (DITA) respeitado (90+ dias) → comportamento normal
⚠️  SUSPEITO: Aviso prévio 5 dias antes do sinistro → timing conveniente

✅ BOM:      Múltiplos sinistros espaçados 12+ meses → histórico normal
⚠️  SUSPEITO: 3+ sinistros em 30 dias → concentração anômala

✅ BOM:      BO emitido 1-7 dias após ocorrência → normal
⚠️  SUSPEITO: BO emitido 30+ dias depois → possível fabricação

✅ BOM:      Laudo técnico em até 15 dias → procedimento normal
⚠️  SUSPEITO: Laudo em 60+ dias com "impossível inspecionar" → FRAUDE
```

**Pontuação temporal:**
```json
{
  "temporal_score": {
    "vigencia_check": 0.0 or 1.0,      // Ocorreu durante contrato?
    "aviso_previo_delta": 0.0 to 1.0,  // DITA respeitou 90 dias?
    "frequencia_anomala": 0.0 to 1.0,  // Muitos sinistros recente?
    "documento_delay": 0.0 to 1.0,      // BO/laudo muito atrasados?
    "weighted": 0.0 to 1.0               // Score final temporal
  }
}
```

### 2️⃣ **ESTRUTURAL** — Coerência de Dados

```python
# Sinais de suspeita:

✅ BOM:      BO cita "moto Honda" → CRLV também Honda → coerente
⚠️  SUSPEITO: BO cita "Honda" → CRLV mostra "Yamaha" → CONTRADIÇÃO

✅ BOM:      Laudo valor $8.500 ≈ NF valor $8.450 → consistente
⚠️  SUSPEITO: Laudo $8.500 vs NF $2.000 → divergência 75% → OVERPAYMENT

✅ BOM:      Vitima CPF = proprietário CRLV → mesma pessoa
⚠️  SUSPEITO: BO vítima CPF diferente de CRLV → ROUBO "de terceiros"?

✅ BOM:      Data laudo APÓS BO → sequência normal
⚠️  SUSPEITO: Laudo com data ANTERIOR a BO → IMPOSSÍVEL fisicamente

✅ BOM:      Descrição BO vs Laudo técnico coerentes
⚠️  SUSPEITO: BO diz "colisão frontal" → Laudo mostra dano traseiro → INCONSISTENTE
```

**Pontuação estrutural:**
```json
{
  "estrutural_score": {
    "consistencia_veiculo": 0.0 to 1.0,  // Marca/modelo/placa coerente?
    "coerencia_valores": 0.0 to 1.0,     // Laudo ≈ NF ≈ Boleto?
    "propriedade_cpf": 0.0 to 1.0,       // CPF vítima = proprietário?
    "sequencia_temporal_docs": 0.0 to 1.0, // Datas em ordem lógica?
    "descricao_convergente": 0.0 to 1.0, // BO + Laudo descrevem mesmo evento?
    "weighted": 0.0 to 1.0                // Score final estrutural
  }
}
```

### 3️⃣ **COMPORTAMENTAL** — Padrão Segurado

```python
# Sinais de suspeita:

✅ BOM:      Primeiro sinistro em 2+ anos vigência → histórico limpo
⚠️  SUSPEITO: 4° sinistro em 6 meses → perfil concentrado

✅ BOM:      Sinistro de colisão (acidental) → esperado
⚠️  SUSPEITO: 3 "roubos" + 2 "sinistros parciais" em 1 ano → PADRÃO coordenado

✅ BOM:      Renda mensal R$6.000 → indenização R$500/dia reasonable
⚠️  SUSPEITO: Renda R$2.000 → solicita R$5.000/dia → SOBREVALORIZADO 150%

✅ BOM:      Prêmio pago regularmente → cliente "bom"
⚠️  SUSPEITO: Atraso 60+ dias em prêmio → sincroniza com sinistro? → SUSPEITO

✅ BOM:      Endereço estável 3+ anos
⚠️  SUSPEITO: Endereço mudou 3x em 6 meses → INSTÁVEL
```

**Pontuação comportamental:**
```json
{
  "comportamental_score": {
    "frequencia_sinistros": 0.0 to 1.0,  // Taxa/mês dentro esperado?
    "tipo_sinistro_pattern": 0.0 to 1.0, // Padrão de tipos (roubo vs acidente)?
    "valor_coerencia": 0.0 to 1.0,       // Indenização proporcional renda?
    "pagamento_regularidade": 0.0 to 1.0, // Prêmios pagos no prazo?
    "estabilidade_endereco": 0.0 to 1.0, // Quantas mudanças recentes?
    "weighted": 0.0 to 1.0                // Score final comportamental
  }
}
```

## Scoring Final

```python
def calcular_risco_fraude(temporal, estrutural, comportamental):
    """
    Combina 3 dimensões em score único
    
    Args:
        temporal: dict com 'weighted' 0.0-1.0
        estrutural: dict com 'weighted' 0.0-1.0
        comportamental: dict com 'weighted' 0.0-1.0
    
    Returns:
        {
          "score_fraude": 0.0 - 1.0,
          "categoria": "BAIXO" | "MÉDIO" | "ALTO" | "CRÍTICO",
          "justificativa": [lista de evidências],
          "recomendação": "aprovação" | "validação_manual" | "rejeição"
        }
    """
    
    # Pesos customizados para 88i
    # (sinistros veiculares: temporal + estrutural = 70% | comportamental = 30%)
    score = (
        0.40 * temporal['weighted'] +
        0.30 * estrutural['weighted'] +
        0.30 * comportamental['weighted']
    )
    
    if score <= 0.3:
        categoria = "BAIXO"
        recomendacao = "aprovação"
    elif score <= 0.6:
        categoria = "MÉDIO"
        recomendacao = "validação_manual"
    elif score <= 0.85:
        categoria = "ALTO"
        recomendacao = "rejeição_com_recurso"
    else:
        categoria = "CRÍTICO"
        recomendacao = "rejeição + investigação"
    
    return {
        "score_fraude": round(score, 3),
        "categoria": categoria,
        "recomendacao": recomendacao
    }
```

## Matriz de Risco por Tipo Sinistro

| Tipo | Temporal | Estrutural | Comportamental | Peso Final |
|------|----------|-----------|-----------------|-----------|
| **ROUBO** | 40% | 35% | 25% | Risco alto naturalmente |
| **COLISÃO** | 30% | 40% | 30% | Moderado (acidental) |
| **DITA** | 50% | 20% | 30% | Temporal crítico |
| **SINISTRO PARCIAL** | 25% | 45% | 30% | Estrutural crítico |

## Integração com BAML

### Arquivo: `baml_src/fraude_scoring.baml`

```baml
function analisar_fraude(
  sinistro_dados: SinistroExtraido,
  historico_segurado: SeguidoHistorico,
  tipo_sinistro: string
) -> ScoringFraude {
  client "claude-opus"
  prompt #"
    Você é analista sênior de fraude em seguros.
    Analise os 3 dimensões e return scoring estruturado.
    
    Seja objetivo: para cada sinal de suspeita, cite a evidência.
    Pese correlações (ex: timing suspeito + valor sobrevalorizado = risco alto).
  "#
}

type ScoringFraude {
  temporal: DimensaoScore
  estrutural: DimensaoScore
  comportamental: DimensaoScore
  score_final: float // 0.0 - 1.0
  categoria: "baixo" | "medio" | "alto" | "critico"
  justificativas: string[] // Lista de evidências
  recomendacao: string // "aprovação" | "manual" | "rejeição"
}
```

## Common Pitfalls

1. **Scoring muito sensível a dados faltantes**
   - Solução: tratar campo ausente como "desconhecido" (0.5), não penalizar

2. **Não normalizar valores entre segurados**
   - Solução: usar percentis (ex: 75º percentil de renda) não valores absolutos

3. **Misturar fraude com recusa por regra**
   - Solução: regra negócio (ex: "roubo não cobre veículo vencido") ≠ fraude

4. **Confiar apenas em 1 dimensão**
   - Solução: sempre ponderar 3 dimensões, não singular

5. **Não documentar threshold de decisão**
   - Solução: sempre comunique score → categoria → ação

6. **Penalizar frequência sem context**
   - Solução: comparar contra baseline do perfil segurado + histórico padrão

## Verification Checklist

- [ ] Dados estruturados foram extraídos por `sinistro-analyzer`
- [ ] Histórico segurado foi recuperado do Supabase/CRM
- [ ] Todas 3 dimensões foram pontuadas (0.0 - 1.0)
- [ ] Score final está entre 0.0 - 1.0
- [ ] Cada score tem lista de justificativas (evidências)
- [ ] Recomendação é uma ação clara (aprovação/manual/rejeição)
- [ ] Timestamp do cálculo foi registrado
- [ ] Pronto para enviar para `sinistro-claim-adjudicator`

## One-Shot Recipe: Score de Fraude

```bash
hermes skill fraude-detector

# INPUT
sinistro_id: "CLM-2026-001234"
dados_extraidos: {
  "numero_bo": "123456789",
  "data_ocorrencia": "2026-05-15",
  "tipo_veiculo": "moto",
  "marca_bo": "Honda",
  "marca_crlv": "Honda", ✅ coerente
  "valor_laudo": 8500,
  "valor_nf": 8450,   ✅ ~coerente
  "cpf_vitima": "123...",
  "cpf_crlv": "123...",  ✅ mesma pessoa
}
historico: {
  "sinistros_ultimo_ano": 1,  ✅ frequência normal
  "atrasos_premium": 0,       ✅ bom pagador
  "renda_mensal": 6000,
  "valor_indenizacao_solicitado": 500  ✅ proporcional

# EXECUTE
[fraude-detector]

# OUTPUT
{
  "temporal_score": { "weighted": 0.15 },      ✅ BOM (tudo dentro prazo)
  "estrutural_score": { "weighted": 0.10 },    ✅ BOM (dados coerentes)
  "comportamental_score": { "weighted": 0.08 },✅ BOM (histórico limpo)
  "score_fraude": 0.11,
  "categoria": "BAIXO",
  "recomendacao": "aprovação",
  "justificativas": [
    "Todas datas em sequência lógica",
    "Dados de marca/placa coerentes",
    "Valor indenização proporcional à renda",
    "Histórico segurado sem anomalias"
  ]
}
```
