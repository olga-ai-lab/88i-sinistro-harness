# Política de Decisão Documental — 88i Seguradora Digital (v2)

## Objetivo
Guiar a skill decisória a operar como analista sênior, combinando regras determinísticas (sem julgamento) com avaliação qualitativa (julgamento profissional).

---

## Camada 1 — Regras determinísticas (HARD RULES)

Estas regras são binárias e não admitem interpretação. Se falharem, o status é automático:

| Código | Regra | Produto | Falha → |
|--------|-------|---------|---------|
| D1 | Apólice vigente na data do fato | Ambos | `rejected_documentally` |
| D2 | Evento fora do período de carência | Ambos | `rejected_documentally` |
| D3 | Evento durante período de trabalho | Impedimento | `pending_documents` (pedir comprovante) |
| D4 | Cooldown 90 dias entre sinistros na mesma cobertura | Impedimento | `rejected_documentally` |
| D5 | Dispositivo de localização ativado | Impedimento | `rejected_documentally` |
| D6 | Tipo de veículo válido (Uber: apenas automóveis) | Imp. Uber | `rejected_documentally` |
| D7 | Evento enquadra em risco coberto | Ambos | `rejected_documentally` |
| D8 | Evento não enquadra em exclusão geral | Ambos | `rejected_documentally` |
| D9 | Evento não enquadra em exclusão específica | Ambos | `rejected_documentally` |
| D10 | NF não é de parente do segurado | Bagagens | `rejected_documentally` |

---

## Camada 2 — Suficiência documental

Documentos obrigatórios por produto + cobertura conforme `olga-analista-seguros-88i`. Verificar:
1. Todos os documentos obrigatórios foram recebidos?
2. Cada documento recebido tem os campos mínimos extraídos?
3. Qualidade de imagem permite extração confiável?

Classificação:
- `complete` — todos os docs com campos mínimos presentes
- `partial` — docs presentes mas com campos faltantes recuperáveis
- `insufficient` — docs obrigatórios ausentes

---

## Camada 3 — Coerência temporal

Sequência esperada: `occurrence ≤ report ≤ notice ≤ opened`

Anomalias a registrar:
- BO registrado antes do fato
- Aviso muito tardio (> 30 dias sem justificativa)
- Atestado/laudo emitido antes do fato
- Certidão de não localização emitida < 15 dias após o fato
- Data de retorno ao trabalho anterior à data do sinistro

---

## Camada 4 — Fraude (scoring objetivo)

Aplicar `resources/fraud_scoring_matrix.md`. Score acumula sinais independentes com pesos.

---

## Camada 5 — Decisão

### Árvore de decisão (em ordem de prioridade)

```
1. SE regra D1-D10 falhou com rejeição inequívoca
   → rejected_documentally

2. SE fraud_score ≥ 10
   → fraud_escalation (obrigatório)

3. SE fraud_score 6-9 E forensics marcou needs_human_review
   → fraud_escalation

4. SE documentos obrigatórios ausentes
   → pending_documents

5. SE campos mínimos incompletos em docs recebidos
   → pending_documents

6. SE anomalias temporais OU cross-doc severity=high
   → pending_manual_review

7. SE fraud_score 1-5
   → pending_manual_review

8. SE tudo ok
   → approved_for_next_step
```

---

## Status válidos

| Status | Quando |
|--------|--------|
| `approved_for_next_step` | Tudo completo, coerente, fraud_risk low |
| `pending_documents` | Docs ou campos ausentes recuperáveis |
| `pending_manual_review` | Ambiguidade ou fraud_risk medium |
| `fraud_escalation` | Múltiplos sinais convergentes (score ≥ 6) |
| `rejected_documentally` | Regra determinística inequívoca |

---

## Princípio do analista sênior

> "Err on the side of caution." Na dúvida entre `pending_documents` e `pending_manual_review`, escolha `pending_manual_review`. Não escalar quando deveria (Type II error) é mais custoso que escalar desnecessariamente (Type I error).
