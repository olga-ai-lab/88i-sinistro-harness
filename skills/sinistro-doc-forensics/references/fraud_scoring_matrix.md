# Matriz de Scoring de Fraude — 88i Seguradora Digital (v1)

## Objetivo
Substituir classificação subjetiva (low/medium/high) por scoring objetivo com pesos e acumulação, simulando o checklist mental de um analista sênior.

---

## Categorias e pesos

### CAT-1: Sinais documentais (+2 cada)
| Código | Sinal | Peso |
|--------|-------|------|
| D01 | BO sem código de verificação/autenticação | +2 |
| D02 | NF sem chave SEFAZ ou chave incompleta | +2 |
| D03 | CRM sem UF ou CRM/UF inconsistente | +2 |
| D04 | Documento com sinais visuais de edição/colagem | +2 |
| D05 | Campo essencial ausente sem justificativa | +2 |
| D06 | Fontes heterogêneas em campos sensíveis | +2 |
| D07 | Screenshot de app com barra de edição visível | +2 |

### CAT-2: Sinais temporais (+3 cada)
| Código | Sinal | Peso |
|--------|-------|------|
| T01 | BO com data de registro ANTERIOR ao fato | +3 |
| T02 | Atestado/laudo médico com data ANTERIOR ao fato | +3 |
| T03 | Certidão de não localização emitida < 15 dias | +3 |
| T04 | Divergência > 7 dias entre data do fato em BO vs. aviso | +3 |
| T05 | Sinistro ocorrido fora do período de trabalho comprovado | +3 |

### CAT-3: Sinais narrativos (+2 cada)
| Código | Sinal | Peso |
|--------|-------|------|
| N01 | Narrativa contraditória entre documentos | +2 |
| N02 | Detalhes clínicos incompatíveis com tipo de acidente | +2 |
| N03 | CID incompatível com narrativa do sinistro | +2 |
| N04 | Valor do orçamento desproporcional ao dano visível | +2 |

### CAT-4: Sinais comportamentais (+3 cada)
| Código | Sinal | Peso |
|--------|-------|------|
| B01 | 2+ sinistros na mesma cobertura em 6 meses | +3 |
| B02 | Padrão documental similar entre sinistros | +3 |
| B03 | Sinistro aberto imediatamente após contratação | +3 |
| B04 | Mesmo segurado com fraude anterior confirmada | +5 |

### CAT-5: Sinais cross-doc (+2 a +4 cada)
| Código | Sinal | Peso |
|--------|-------|------|
| X01 | Nome completamente divergente entre docs (severity HIGH) | +4 |
| X02 | Placa divergente entre CRLV e BO | +4 |
| X03 | IMEI divergente entre NF e bloqueio | +4 |
| X04 | Nome com variação menor (severity LOW) | +1 |
| X05 | Data com divergência 2-7 dias (severity MEDIUM) | +2 |

---

## Faixas de risco

| Score total | Nível | Ação obrigatória |
|-------------|-------|-----------------|
| 0 | `low` | Nenhuma ação adicional |
| 1-5 | `medium` | `pending_manual_review` com sinais listados |
| 6-9 | `high` | `fraud_escalation` se confirmado por revisão humana |
| 10+ | `critical` | `fraud_escalation` obrigatório e imediato |

---

## Regras de aplicação

1. **Acumular, não substituir:** cada sinal soma ao score total. Um caso com D01+T01+N01 = 2+3+2 = 7 → `high`.
2. **Independência:** sinais devem ser independentes. Não contar o mesmo fato 2x em categorias diferentes.
3. **Convergência:** 3+ sinais de categorias DIFERENTES são mais significativos que 3 sinais da mesma categoria.
4. **Contexto:** sinais CAT-4 (comportamentais) requerem consulta ao histórico do segurado no Supabase.
5. **Transparência:** SEMPRE listar os códigos e sinais que contribuíram para o score.

---

## Exemplo de aplicação

**Caso:** Roubo de celular, Cobertura III
- D02: NF sem chave SEFAZ → +2
- T05: Sinistro às 23h, último registro de corrida às 18h → +3
- X03: IMEI na NF = 356938035643809, IMEI no bloqueio = 356938035643810 → +4
- **Score total: 9 → HIGH**
- **Ação: fraud_escalation após revisão humana**
- **Sinais convergentes de 3 categorias diferentes (documental + temporal + cross-doc)**
