# Regras de Validação Cruzada entre Documentos — 88i (v1)

## Objetivo
Definir as comparações obrigatórias entre documentos do mesmo sinistro para detectar inconsistências que um analista sênior humano identificaria naturalmente.

---

## Regras de cruzamento

### R1 — Nome do segurado (cross-all)
- **Comparar:** nome em TODOS os documentos vs. nome na apólice/bilhete
- **Tolerância:** abreviações, acentuação, ordem nome/sobrenome
- **Severity LOW:** "João Silva" vs. "João da Silva" (variação preposição)
- **Severity HIGH:** "João Silva" vs. "Maria Santos" (nomes completamente diferentes)
- **Ação se HIGH:** `pending_manual_review` + flag para analista

### R2 — Data do fato (BO/BRAT × aviso × formulário)
- **Comparar:** occurrence_date no BO/BRAT vs. occurrence_date no claim_form vs. occurrence_date no incident_notice
- **Tolerância:** ±1 dia (erro de preenchimento comum)
- **Severity LOW:** diferença de 1 dia
- **Severity MEDIUM:** diferença de 2-7 dias
- **Severity HIGH:** diferença > 7 dias ou BO com data anterior ao fato
- **Ação se HIGH:** elevar fraud_score +3

### R3 — Placa do veículo (CRLV × BO × BRAT)
- **Comparar:** plate no vehicle_document vs. vehicle_plate no police_report vs. vehicle_a_plate no traffic_accident_report
- **Tolerância:** ZERO — placa deve ser idêntica
- **Severity HIGH:** qualquer divergência
- **Ação se HIGH:** elevar fraud_score +4, `pending_manual_review`

### R4 — IMEI (NF celular × comprovante bloqueio)
- **Comparar:** IMEI na invoice_receipt vs. IMEI no imei_block_proof
- **Tolerância:** ZERO — IMEI deve ser idêntico (15 dígitos)
- **Severity HIGH:** qualquer divergência
- **Ação se HIGH:** elevar fraud_score +4, `pending_manual_review`

### R5 — Período de trabalho × horário do sinistro
- **Comparar:** work_period no work_period_proof vs. occurrence_time no police_report/claim_form
- **Tolerância:** ±30 minutos (tempo entre última corrida e o evento)
- **Severity MEDIUM:** evento 30min-2h fora do período de trabalho
- **Severity HIGH:** evento claramente fora do período (ex: sinistro às 3h, trabalho até 22h)
- **Ação se HIGH:** elevar fraud_score +3

### R6 — Nome paciente × nome segurado (laudo médico × apólice)
- **Comparar:** patient_name no medical_report/certificate vs. nome do segurado
- **Tolerância:** mesma tolerância que R1
- **Ação se HIGH:** elevar fraud_score +3

### R7 — Data atestado/laudo × data do fato
- **Comparar:** issue_date do medical_report vs. occurrence_date
- **Regra:** data do laudo/atestado DEVE ser ≥ data do fato
- **Severity HIGH:** laudo com data ANTERIOR ao fato
- **Ação se HIGH:** elevar fraud_score +4 (forte indicador de fraude)

### R8 — Comprovante residência × prazo 88i
- **Comparar:** issue_date do proof_of_address vs. data atual
- **Regra 88i:** comprovante deve ter ≤ 90 dias
- **Ação se vencido:** `pending_documents` (solicitar atualizado)

### R9 — NF × parentesco (Bagagens/Encomendas)
- **Comparar:** recipient_name na invoice_receipt vs. insured_name
- **Regra 88i:** NF emitida para parente do segurado é vedada no produto Bagagens
- **Nota:** o sistema não pode verificar parentesco automaticamente — sinalizar quando nomes de família divergem para revisão humana

### R10 — Timeline completa
- **Sequência esperada:** occurrence_date ≤ report_date ≤ notice_date ≤ opened_at
- **Para médicos:** occurrence_date ≤ medical_issue_date
- **Para oficina:** occurrence_date ≤ repair_entry_date ≤ repair_exit_date ≤ work_return_date
- **Qualquer inversão:** registrar como timeline_issue

---

## Prioridade de execução
1. Sempre executar R1, R2, R10 (aplicáveis a todos os sinistros)
2. R3 quando houver BO/BRAT + CRLV
3. R4 quando houver NF celular + bloqueio IMEI
4. R5 quando houver comprovante de trabalho
5. R6, R7 quando houver documentação médica
6. R8 sempre que houver comprovante de residência
7. R9 apenas para produto Bagagens/Encomendas
