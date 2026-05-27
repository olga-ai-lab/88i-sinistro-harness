# Campos de Extração por Tipo de Documento — 88i Sinistros
# Usado pela skill sinistro-doc-forensics (Etapa 2 do pipeline)
# Fonte: Condições Gerais 88i março/2026

---

## police_report (Boletim de Ocorrência Policial)
Campos obrigatórios:
- report_number (nº BO/registro)
- issuing_authority (delegacia / órgão emissor)
- occurrence_date (data do fato)
- report_date (data do registro)
- insured_or_victim_name (nome da vítima/segurado)
- vehicle_plate (placa, quando aplicável)
- short_narrative (resumo da narrativa)
- authenticity_markers (código de verificação, QR, cabeçalho institucional)

Campos opcionais:
- occurrence_time (hora do fato)
- location (endereço/local)
- witness_info

---

## traffic_accident_report (BRAT — Boletim de Reg. de Acidente de Trânsito)
Campos obrigatórios:
- report_number
- issuing_authority (órgão de trânsito)
- occurrence_date
- occurrence_time
- vehicle_plate
- involved_vehicles (lista de veículos envolvidos)
- short_narrative
- insured_driver_name

Campos opcionais:
- croqui_present (boolean)
- third_party_info

---

## non_location_certificate (Certidão de Não Localização)
Campos obrigatórios:
- issuing_authority (delegacia)
- referenced_bo_number (nº do BO de referência)
- vehicle_plate
- certificate_date
- declaration_text (deve conter "não localizado")

Validação crítica: certificate_date NÃO deve ser < 15 dias após occurrence_date do BO

---

## medical_report (Laudo Médico)
Campos obrigatórios:
- patient_name
- doctor_name
- crm_number
- crm_state (UF — 2 letras)
- issue_date
- clinical_summary
- diagnosis_code (CID quando aplicável)
- signature_or_stamp

Campos opcionais:
- rest_period (período de afastamento)
- hospital_or_clinic

---

## medical_certificate (Atestado Médico)
Campos obrigatórios:
- patient_name
- doctor_name
- crm_number
- crm_state
- issue_date
- absence_period (período de afastamento em dias)
- signature

Campos opcionais:
- cid_code
- return_date

---

## identity_document (RG / CNH / CPF / Passaporte)
Campos obrigatórios:
- full_name
- document_number
- document_type (rg | cnh | cpf | passaporte)
- expiry_date (CNH — verificar validade)
- photo_present (boolean, quando aplicável)

Para CNH especificamente:
- cnh_category (A, B, AB, etc.)
- cnh_validity_date
- cnh_status (ativa / vencida / suspensa — inferir quando possível)

---

## proof_of_address (Comprovante de Residência)
Campos obrigatórios:
- holder_name
- address_full
- issue_date
- document_source (conta de luz, água, banco, etc.)

Validação crítica: issue_date NÃO deve ser > 90 dias antes da data do sinistro

---

## vehicle_document (CRLV / CRV)
Campos obrigatórios:
- owner_name
- vehicle_plate
- renavam (11 dígitos)
- chassis
- vehicle_model
- model_year
- manufacture_year
- exercise_year (ano do CRLV)

Validações:
- RENAVAM deve ter 11 dígitos
- Placa formato Mercosul (AAA0A00) ou antigo (AAA-0000)
- model_year NÃO deve ser > ano_corrente + 1

---

## invoice_receipt (Nota Fiscal NF-e / Cupom)
Campos obrigatórios:
- items_description
- total_value
- access_key (chave de acesso — 44 dígitos para NF-e)
- issuer_cnpj (14 dígitos)
- recipient_name
- recipient_cpf_or_cnpj
- issue_date

Validações críticas:
- access_key deve ter exatamente 44 dígitos
- issuer_cnpj deve ter 14 dígitos
- REGRA 88i: recipient NÃO deve ser parente do segurado (verificar sobrenome ou declaração)

---

## claim_form (Aviso / Formulário de Sinistro)
Campos obrigatórios:
- insured_name
- policy_or_product_reference
- occurrence_date
- notice_date
- event_description
- coverage_claimed

---

## work_period_proof (Comprovante de Período de Trabalho — App)
Campos obrigatórios:
- driver_name (ou identificador na plataforma)
- platform (uber | 99 | ifood | rappi | etc.)
- date
- work_period_start (hora início)
- work_period_end (hora fim)
- trip_count (número de corridas/entregas)

Validações:
- Período de trabalho deve cobrir o horário do sinistro alegado
- Screenshot sem sinais de edição (barras de ferramentas, seleção ativa)

---

## imei_block_proof (Comprovante de Bloqueio IMEI)
Campos obrigatórios:
- imei_number (15 dígitos)
- block_date
- issuing_entity (operadora ou ANATEL)
- device_description

Validação crítica: imei_number deve ter 15 dígitos e coincidir com NF do celular

---

## repair_estimate (Orçamento / Laudo de Oficina)
Campos obrigatórios:
- vehicle_plate
- vehicle_model
- defects_described
- repair_cost_estimate
- estimated_repair_days
- workshop_name
- workshop_cnpj_or_registration
- issue_date

---

## damage_photo (Foto de Danos)
Campos a registrar (sem extração formal — análise visual):
- damage_type (veículo | celular | encomenda | bagagem)
- damage_visible (boolean + descrição)
- photo_quality
- consistency_with_narrative (compatível com o evento alegado?)

---

## prior_declaration (Declaração Prévia de Encomenda — Prod. C)
Campos obrigatórios:
- item_description
- item_value
- item_characteristics
- declaration_date
- declarant_name

Validação crítica: declaration_date DEVE ser ANTERIOR à data do sinistro

---

## work_return_proof (Comprovante de Retorno ao Trabalho)
Campos obrigatórios:
- driver_name
- return_date
- platform_confirmation (via app ou declaração)

---

## CAMPOS UNIVERSAIS DE CROSS-VALIDATION

Sempre que múltiplos documentos estiverem disponíveis, verificar:

1. name_consistency: nome do segurado/paciente/motorista é consistente entre todos os docs?
2. date_sequence: occurrence ≤ report/BO ≤ notice ≤ opened_at
3. plate_consistency: placa no BO = placa no CRLV?
4. imei_consistency: IMEI no bloqueio = IMEI na NF do celular?
5. work_period_overlap: período de trabalho no app cobre o horário do sinistro?
6. address_currency: comprovante de residência emitido há ≤ 90 dias?
7. cnh_validity: CNH válida na data do sinistro?
8. invoice_recipient: destinatário da NF NÃO é parente do segurado?
9. prior_declaration_date: declaração prévia anterior ao sinistro?
10. certificate_timing: certidão não localização emitida ≥ 15 dias após roubo?
